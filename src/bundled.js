export function mergeBundled(saved, manifest) {
  if (manifest.version !== 1 || !Array.isArray(manifest.tracks)) throw Error('同梱音声の一覧形式が不正です。');
  const seen = new Set();
  for (const t of manifest.tracks) {
    if (!Number.isInteger(t.number) || t.number < 1 || t.number > 9999 || typeof t.name !== 'string' || !/^audio\/files\/[a-f0-9]{64}\.(mp3|wav|m4a|ogg|aac)$/.test(t.url) || seen.has(t.number)) throw Error('同梱音声の番号またはパスが不正です。');
    seen.add(t.number);
  }
  const result = saved.filter(t => !t.bundled);
  for (const t of manifest.tracks) {
    if (result.some(old => old.number === t.number)) continue;
    const old = saved.find(old => old.number === t.number);
    result.push({...old, ...t, id:old?.id || `bundled-${t.number}`, bundled:true, count:old?.count || 0});
  }
  return result;
}
