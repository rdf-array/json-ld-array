// Parse every shexTest schema and negative-syntax test with each variant; compare with B0.
const fs = require('fs'), path = require('path');
const [T, ...variants] = process.argv.slice(2);
const files = d => fs.readdirSync(path.join(T, d)).filter(f => f.endsWith('.shex')).map(f => path.join(T, d, f));
const pos = files('schemas'), neg = files('negativeSyntax');
const run = (parse, f) => { try { return JSON.stringify(parse(fs.readFileSync(f, 'utf8'), 'http://a.example/' + path.basename(f))); } catch (e) { return 'ERROR ' + e.message.split('\n')[0]; } };
const base = require('./shex.js')('B0'), b = new Map([...pos, ...neg].map(f => [f, run(base, f)]));
console.log(`B0: ${pos.filter(f => !b.get(f).startsWith('ERROR')).length}/${pos.length} schemas parse, ${neg.filter(f => b.get(f).startsWith('ERROR')).length}/${neg.length} negative-syntax tests rejected`);
for (const v of variants) {
  const parse = require('./shex.js')(v);
  const diffPos = pos.filter(f => run(parse, f) !== b.get(f));
  const diffNeg = neg.filter(f => run(parse, f).startsWith('ERROR') !== b.get(f).startsWith('ERROR'));
  console.log(`${v}: ${diffPos.length} schemas parse differently from B0, ${diffNeg.length} negative-syntax verdicts differ`,
              [...diffPos, ...diffNeg].slice(0, 8).map(f => path.basename(f)).join(' '));
}
