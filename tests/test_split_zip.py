import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('split_zip', Path(__file__).resolve().parents[1] / 'scripts/split_zip.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SplitZipTests(unittest.TestCase):
    def test_independent_zips_preserve_all_files_and_size(self):
        with tempfile.TemporaryDirectory() as folder:
            original = Path(folder) / '音声.zip'
            data = {f'音声/{i:03d}.mp3': bytes([i]) * 400 for i in range(1, 7)}
            with zipfile.ZipFile(original, 'w', compression=zipfile.ZIP_DEFLATED) as z:
                for name, content in data.items():
                    z.writestr(name, content)
            before = original.read_bytes()
            with contextlib.redirect_stdout(io.StringIO()):
                parts = module.split_zip(original, max_bytes=1100)
            self.assertGreater(len(parts), 1)
            recovered = {}
            for part in parts:
                self.assertLessEqual(part.stat().st_size, 1100)
                with zipfile.ZipFile(part) as z:
                    self.assertIsNone(z.testzip())
                    recovered.update({name: z.read(name) for name in z.namelist()})
            self.assertEqual(recovered, data)
            self.assertEqual(original.read_bytes(), before)
            with self.assertRaises(FileExistsError):
                module.split_zip(original, max_bytes=1100)

    def test_large_single_file_fails_without_partial_results(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'large.zip'
            with zipfile.ZipFile(source, 'w') as z:
                z.writestr('001.mp3', b'x' * 1000)
            with self.assertRaises(ValueError):
                module.split_zip(source, max_bytes=1000)
            self.assertFalse(source.with_name('large_github_parts').exists())

    def test_invalid_zip_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'invalid.zip'
            source.write_bytes(b'not a zip')
            with self.assertRaises(zipfile.BadZipFile):
                module.split_zip(source)
            self.assertFalse(source.with_name('invalid_github_parts').exists())


if __name__ == '__main__':
    unittest.main()
