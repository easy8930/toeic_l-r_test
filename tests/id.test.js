import test from 'node:test';
import assert from 'node:assert/strict';
import {createId} from '../src/id.js';
test('LAN HTTP generates unique UUIDs without randomUUID',()=>{
 const provider={getRandomValues:array=>crypto.getRandomValues(array)};
 const ids=Array.from({length:100},()=>createId(provider));
 assert.equal(new Set(ids).size,100);
 for(const id of ids)assert.match(id,/^[\da-f]{8}-[\da-f]{4}-4[\da-f]{3}-[89ab][\da-f]{3}-[\da-f]{12}$/);
});
test('HTTPS keeps native UUID support',()=>assert.equal(createId({randomUUID:()=> 'native-id'}),'native-id'));
