import test from 'node:test';import assert from 'node:assert/strict';import {mergeBundled} from '../src/bundled.js';
const t={number:132,name:'132.wav',url:'audio/files/'+'a'.repeat(64)+'.wav'};const manifest={version:1,tracks:[t]};
test('fresh devices see bundled tracks without import',()=>{const [r]=mergeBundled([],manifest);assert.equal(r.id,'bundled-132');assert.equal(r.bundled,true);assert.equal(r.count,0)});
test('reload preserves counts and local overrides',()=>{const [r]=mergeBundled([{...t,id:'old',bundled:true,count:3}],manifest);assert.equal(r.count,3);assert.equal(r.id,'old');const local={id:'local',number:132,count:5};assert.deepEqual(mergeBundled([local],manifest),[local]);});
test('reject duplicate numbers and external paths',()=>{assert.throws(()=>mergeBundled([],{version:1,tracks:[t,t]}));assert.throws(()=>mergeBundled([],{version:1,tracks:[{...t,url:'https://example.com/132.wav'}]}));});
