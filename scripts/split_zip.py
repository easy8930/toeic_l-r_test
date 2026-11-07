#!/usr/bin/env python3
"""Repack a ZIP into independent, size-limited ZIPs (Python standard library only)."""
import argparse
from decimal import Decimal, InvalidOperation
from pathlib import Path
import shutil
import sys
import zipfile

DEFAULT_LIMIT = 24_000_000  # Below GitHub's 25 MiB browser-upload limit.


def entry_size(info):
    # ZIP_STORED: local header + filename + data + central-directory header.
    try:
        name = info.filename.encode('ascii')
    except UnicodeEncodeError:
        name = info.filename.encode('utf-8')
    return 30 + len(name) + info.file_size + 46 + len(name)


def split_zip(source, output=None, max_bytes=DEFAULT_LIMIT):
    source = Path(source).resolve()
    output = Path(output).resolve() if output else source.with_name(source.stem + '_github_parts')
    if max_bytes < 100 or max_bytes > DEFAULT_LIMIT:
        raise ValueError('上限サイズは0.0001〜24 MBで指定してください。')
    if output.exists():
        raise FileExistsError(f'出力先が既に存在します。別の出力先を指定してください: {output}')
    created = False
    try:
        with zipfile.ZipFile(source) as original:
            infos = [i for i in original.infolist() if not i.is_dir()]
            if not infos:
                raise ValueError('ZIP内にファイルがありません。')
            names = set()
            batches, batch, size = [], [], 22  # End-of-central-directory record.
            for info in infos:
                if info.flag_bits & 1:
                    raise ValueError(f'暗号化ZIPには対応していません: {info.filename}')
                if info.filename in names:
                    raise ValueError(f'ZIP内のファイル名が重複しています: {info.filename}')
                names.add(info.filename)
                required = entry_size(info)
                if required + 22 > max_bytes:
                    raise ValueError(f'1ファイルだけで上限を超えます: {info.filename} ({info.file_size:,} bytes)。音声自体の分割は行いません。')
                if size + required > max_bytes:
                    batches.append(batch)
                    batch, size = [], 22
                batch.append(info)
                size += required
            if batch:
                batches.append(batch)
            output.mkdir(parents=True, exist_ok=False)
            created = True
            results = []
            for number, entries in enumerate(batches, 1):
                target = output / f'{source.stem}_part{number:03d}.zip'
                with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_STORED, allowZip64=False) as archive:
                    for info in entries:
                        clean = zipfile.ZipInfo(info.filename, info.date_time)
                        clean.compress_type = zipfile.ZIP_STORED
                        clean.external_attr = info.external_attr
                        # Streaming reads verify source CRC; no full audio file is loaded into RAM.
                        with original.open(info) as reader, archive.open(clean, 'w') as writer:
                            shutil.copyfileobj(reader, writer, length=1024 * 1024)
                if target.stat().st_size > max_bytes:
                    raise ValueError(f'出力が指定サイズを超えました: {target.name}')
                with zipfile.ZipFile(target) as check:
                    bad = check.testzip()
                    if bad:
                        raise ValueError(f'出力ZIPの整合性確認に失敗しました: {bad}')
                results.append(target)
                print(f'{target.name}: {target.stat().st_size / 1_000_000:.2f} MB / {len(entries)}ファイル')
            return results
    except BaseException:
        if created:
            # This invocation created this directory exclusively; do not touch input files.
            shutil.rmtree(output)
        raise


def main():
    parser = argparse.ArgumentParser(description='ZIPを24MB以下の独立したZIPに分けます。元ZIPと音声は変更しません。')
    parser.add_argument('zip_file', type=Path, help='分割する元ZIPのパス')
    parser.add_argument('--output', type=Path, help='出力フォルダー（既存フォルダーは上書きしません）')
    parser.add_argument('--max-mb', default='24', help='各ZIPの上限MB（10進、最大24、既定24）')
    args = parser.parse_args()
    try:
        try:
            value = Decimal(args.max_mb)
            if not value.is_finite() or value <= 0:
                raise ValueError('上限サイズには正の数を指定してください。')
            limit = int(value * 1_000_000)
        except (InvalidOperation, OverflowError) as error:
            raise ValueError('上限サイズに有効な数値を指定してください。') from error
        results = split_zip(args.zip_file, args.output, limit)
        print(f'\n完了: {len(results)}個のZIPを作成しました。\n保存先: {results[0].parent}')
        print('作成されたZIPをすべてGitHubのaudio-sourceへ追加してください。元ZIPや解凍済み音声を重ねて登録しないでください。')
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, zipfile.LargeZipFile, NotImplementedError) as error:
        print(f'エラー: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
