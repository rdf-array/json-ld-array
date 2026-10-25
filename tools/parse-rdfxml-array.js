#!/usr/bin/env node
// Parse RDF/XML with rdfxml-streaming-parser-array and print N-Quads-array (sequences as ( ... )).
//   node parse-rdfxml-array.js FILE BASE
// Needs ~/checkouts/rdf-array/rdfxml-streaming-parser-array built (its dist/ is committed).
const fs = require('fs');
const path = require('path');
const fork = process.env.RDFXML_ARRAY || path.join(process.env.HOME, 'checkouts/rdf-array/rdfxml-streaming-parser-array');
const { RdfXmlParser } = require(fork);
const { DataFactory } = require(path.join(fork, 'node_modules/rdf-data-factory'));
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
const parser = new RdfXmlParser({ baseIRI: base, dataFactory: new DataFactory() });
const lines = [];
parser.on('data', q => lines.push(`${nt(q.subject)} ${nt(q.predicate)} ${nt(q.object)}${q.graph.termType === 'DefaultGraph' ? '' : ' ' + nt(q.graph)} .`));
parser.on('error', e => { console.error(e.message); process.exit(1); });
parser.on('end', () => process.stdout.write(lines.join('\n') + '\n'));
fs.createReadStream(file).pipe(parser);
