import {readdir,readFile,mkdir,writeFile,rename} from 'node:fs/promises';
import {resolve,join,basename,extname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {unzipSync} from 'fflate';
import {trackNumber} from '../src/model.js';
const root=resolve(fileURLToPath(new URL('..',import.meta.url)));
const input=process.argv.slice(2);
async function filesIn(dir){try{const out=[];for(const e of await readdir(dir,{withFileTypes:true})){if(e.isDirectory())out.push(...await filesIn(join(dir,e.name)));else if(e.isFile())out.push(join(dir,e.name));}return out;}catch(e){if(e.code==='ENOENT')return [];throw e;}}
const sources=input.length?input.map(p=>resolve(p)):(await filesIn(join(root,'audio-source'))).filter(p=>/\.(zip|mp3|wav|m4a|ogg|aac)$/i.test(p));
if(!sources.length){console.log('同梱音声: audio-source にZIPまたは音声を置くと次回起動時に準備します。');process.exit(0);}
const tracks=[],assets=[],numbers=new Set();
for(const path of sources){const bytes=await readFile(path);const entries=/\.zip$/i.test(path)?Object.entries(unzipSync(bytes,{filter:e=>/\.(mp3|wav|m4a|ogg|aac)$/i.test(e.name)&&!e.name.includes('__MACOSX')})):[[basename(path),bytes]];
 for(const [name,content]of entries){if(!/\.(mp3|wav|m4a|ogg|aac)$/i.test(name)||name.includes('__MACOSX'))continue;
 const filename=name.replace(/\\/g,'/').split('/').pop(),number=trackNumber(filename);
 if(number===null)throw Error(`トラック番号を判別できません: ${filename}。132.mp3のように番号を付けてください。`);
 if(numbers.has(number))throw Error(`番号 ${number} が重複しています。ZIPと解凍済み音声を重ねて置かないでください。`);
 numbers.add(number);const hash=createHash('sha256').update(content).digest('hex');const asset=hash+extname(filename).toLowerCase();
 assets.push([asset,content]);tracks.push({id:`bundled-${number}`,number,name:filename,url:`audio/files/${asset}`,bundled:true});
 }}
if(!tracks.length)throw Error('対象の音声ファイルがありません。');
const output=join(root,'public','audio');await mkdir(join(output,'files'),{recursive:true});
for(const [name,bytes]of assets)await writeFile(join(output,'files',name),bytes);
tracks.sort((a,b)=>a.number-b.number);
await writeFile(join(output,'manifest.json.tmp'),JSON.stringify({version:1,tracks},null,2));
await rename(join(output,'manifest.json.tmp'),join(output,'manifest.json'));
console.log(`同梱音声: ${tracks.length}トラック準備できました。ブラウザでの取り込みは不要です。`);
