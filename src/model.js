export function trackNumber(name){const base=name.replace(/\\/g,'/').split('/').pop().replace(/\.[^.]+$/,'');const tokens=base.match(/\d+/g)||[];const candidates=tokens.filter(t=>t.length<=4&&Number(t)>0);return candidates.length?Number(candidates.at(-1)):null;}
export function selectRange(tracks,start,end){return tracks.filter(t=>t.number!==null&&t.number>=start&&t.number<=end).sort(sortTracks);}
export function sortTracks(a,b){return (a.number??Infinity)-(b.number??Infinity)||a.name.localeCompare(b.name,'ja',{numeric:true});}
export function nextIndex(index,length,repeat){if(!length)return -1;return index+1<length?index+1:repeat?0:-1;}
export const verifiedGroups=[{id:'vocab',name:'頻出語彙・表現',start:122,end:131,description:'セレクションリスト',verified:true},{id:'part2',name:'Part 2 トレーニング',start:132,end:136,description:'正誤判断柔軟トレーニング',verified:true},{id:'reading',name:'Part 6・7 読解',start:137,end:167,description:'スラッシュリーディング・音読',verified:true},{id:'reading-part6',name:'Part 6 本冊・読解',start:137,end:140,description:'本冊の長文音読',verified:true},{id:'reading-part7',name:'Part 7 本冊・読解',start:141,end:147,description:'本冊の長文音読',verified:true},{id:'mock-part6',name:'Part 6 完全模試・読解',start:148,end:151,description:'完全模試の長文音読',verified:true},{id:'mock-part7',name:'Part 7 完全模試・読解',start:152,end:167,description:'完全模試の長文音読',verified:true}];
export function validRange(start,end){return Number.isInteger(start)&&Number.isInteger(end)&&start>0&&end>=start&&end<=9999;}

export function listeningGroups(tracks) {
  const numbers = tracks.map(t => t.number).filter(n => Number.isInteger(n) && n > 0);
  if (!numbers.length) return verifiedGroups;
  return [{id:'all-audio', name:'すべての音声', start:Math.min(...numbers), end:Math.max(...numbers), description:'登録済みの音声を番号順に連続再生', available:true}, ...verifiedGroups];
}
export function featuredGroups(tracks, limit=3) {
  return listeningGroups(tracks).map((group,index)=>({group,index,ready:selectRange(tracks,group.start,group.end).length>0}))
    .sort((a,b)=>Number(b.ready)-Number(a.ready)||a.index-b.index).slice(0,limit).map(item=>item.group);
}
