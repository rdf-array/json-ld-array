// Mocha root hooks that record every jsonld.arrayToRDF call of a test run, for json-ld-api-contrib.
//   npx mocha --require capture-jsonld-array.js tests/array.js   (in jsonld.js-array; CAPTURE=out.json)
const path = require('path');
const fs = require('fs');
const jsonld = require(path.resolve('lib/index.js'));
const calls = [];
let title = null;
// JSON with each parseJSON Number written in its own lexical form (1.70 stays 1.70)
function json(v, indent = '') {
  if (v instanceof Number) return v.lexical || String(v.valueOf());
  if (Array.isArray(v)) return v.length ? '[' + v.map(x => json(x, indent)).join(', ') + ']' : '[]';
  if (v && typeof v === 'object') {
    const keys = Object.keys(v);
    return keys.length ? '{ ' + keys.map(k => JSON.stringify(k) + ': ' + json(v[k], indent)).join(', ') + ' }' : '{}';
  }
  return JSON.stringify(v);
}
const original = jsonld.arrayToRDF;
jsonld.arrayToRDF = async function(data, mapping, options) {
  const call = {title, data: json(data), mapping: mapping && mapping.compiled ? null : json(mapping)};
  try {
    const quads = await original.call(this, data, mapping, {});
    call.nquads = jsonld.array.toNQuads(quads);
  } catch(e) {
    call.error = {name: e.name, code: e.details && e.details.code, message: e.message};
  }
  calls.push(call);
  return original.call(this, data, mapping, options);
};
exports.mochaHooks = {
  beforeEach() { title = this.currentTest.fullTitle(); },
  afterAll() { fs.writeFileSync(process.env.CAPTURE || 'capture.json', JSON.stringify(calls, null, 1)); }
};
