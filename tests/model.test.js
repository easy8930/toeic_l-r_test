import test from 'node:test';import assert from 'node:assert/strict';import {trackNumber,selectRange,nextIndex,verifiedGroups,validRange} from '../src/model.js';
test('publisher filenames and unknown names',()=>{assert.equal(trackNumber('7018001_audio03/7018001_132.mp3'),132);assert.equal(trackNumber('001.mp3'),1);assert.equal(trackNumber('7018001.mp3'),null);assert.equal(trackNumber('132_Introduction.mp3'),132);assert.equal(trackNumber('voice.wav'),null);});
test('range is inclusive, sorted, and excludes unknown tracks',()=>{const ts=[{number:136},{number:null},{number:132},{number:137},{number:133}];assert.deepEqual(selectRange(ts,132,136).map(t=>t.number),[132,133,136]);});
test('continuous playback stops at range end or repeats',()=>{assert.equal(nextIndex(0,2,false),1);assert.equal(nextIndex(1,2,false),-1);assert.equal(nextIndex(1,2,true),0);assert.equal(nextIndex(0,0,true),-1);});
test('verified groups match provided PDF',()=>{assert.deepEqual(verifiedGroups.slice(0,3).map(g=>[g.start,g.end]),[[122,131],[132,136],[137,167]]);assert.ok(validRange(1,20));assert.ok(!validRange(20,1));assert.ok(!validRange(1.5,20));});

test('reading subgroups follow individual PDF track headings',()=>assert.deepEqual(verifiedGroups.slice(3).map(g=>[g.start,g.end]),[[137,140],[141,147],[148,151],[152,167]]));

test('partial 001-101 library always has a playable featured group',async()=>{
 const {listeningGroups,featuredGroups}=await import('../src/model.js');
 const tracks=Array.from({length:101},(_,i)=>({number:i+1,name:`${i+1}.mp3`}));
 const all=listeningGroups(tracks)[0];assert.equal(all.id,'all-audio');assert.equal(all.start,1);assert.equal(all.end,101);assert.equal(selectRange(tracks,all.start,all.end).length,101);
 assert.equal(featuredGroups(tracks)[0].id,'all-audio');
 assert.equal(featuredGroups([{number:132,name:'132.mp3'}])[1].id,'part2');
 assert.equal(listeningGroups([]).some(g=>g.id==='all-audio'),false);
});
