#!/usr/bin/env node
// Parse Turtle, TriG, N-Triples or N-Quads with N3.js-array and print N-Quads-array (sequences as ( ... )).
//   node parse-n3-array.js FILE BASE
const fs = require('fs');
const path = require('path');
const fork = process.env.N3_ARRAY || path.join(process.env.HOME, 'checkouts/rdf-array/N3.js-array');
const { Parser } = require(path.join(fork, 'lib'));
const XSD_STRING = 'http://www.w3.org/2001/XMLSchema#string';
const esc = s => s.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n').replace(/\r/g, '\\r');
function nt(t) {
  switch (t.termType) {
    case 'NamedNode': return `<${t.value}>`;
    case 'BlankNode': return `_:${t.value}`;
    case 'Literal': return `"${esc(t.value)}"` + (t.language ? `@${t.language}${t.direction ? '--' + t.direction : ''}` :
      t.datatype.value === XSD_STRING ? '' : `^^<${t.datatype.value}>`);
    case 'Quad': return `<<( ${nt(t.subject)} ${nt(t.predicate)} ${nt(t.object)} )>>`;
    case 'Sequence': return t.elements.length ? `(${t.elements.map(nt).join(' ')})` : '()';
    default: return '';
  }
}
const [file, base] = process.argv.slice(2);
const format = { '.ttl': 'text/turtle', '.trig': 'application/trig', '.nt': 'application/n-triples', '.nq': 'application/n-quads' }[path.extname(file)];
try {
  const quads = new Parser({ baseIRI: base, format }).parse(fs.readFileSync(file, 'utf8'));
  process.stdout.write(quads.map(q => `${nt(q.subject)} ${nt(q.predicate)} ${nt(q.object)}${q.graph.termType === 'DefaultGraph' ? '' : ' ' + nt(q.graph)} .\n`).join(''));
} catch (e) { console.error(e.message); process.exit(1); }
