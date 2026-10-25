#!/usr/bin/env node
// Parse JSON-LD with jsonld-streaming-parser-array and print N-Quads-array (sequences as ( ... )).
//   node parse-jsonld-array.js FILE BASE [OPTIONS-JSON]
// OPTIONS-JSON: a test's "option" object (processingMode, specVersion, rdfDirection,
// produceGeneralizedRdf, expandContext as a path relative to the manifest directory).
const fs = require('fs');
const path = require('path');
const fork = process.env.JSONLD_PARSER_ARRAY || path.join(process.env.HOME, 'checkouts/rdf-array/jsonld-streaming-parser-array');
const { JsonLdParser } = require(fork);
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
const [file, base, optionText] = process.argv.slice(2);
const option = optionText ? JSON.parse(optionText) : {};
const settings = { baseIRI: option.base || base, dataFactory: new DataFactory() };
if (option.processingMode) settings.processingMode = option.processingMode.replace('json-ld-', '');
if (option.rdfDirection) settings.rdfDirection = option.rdfDirection;
if (option.produceGeneralizedRdf) settings.produceGeneralizedRdf = true;
if (option.expandContext) settings.context = JSON.parse(fs.readFileSync(path.join(path.dirname(file), '..', option.expandContext), 'utf8'));
settings.documentLoader = { load: async url => { throw new Error(`no remote documents: ${url}`); } };
const parser = new JsonLdParser(settings);
const lines = [];
parser.on('data', q => lines.push(`${nt(q.subject)} ${nt(q.predicate)} ${nt(q.object)}${q.graph.termType === 'DefaultGraph' ? '' : ' ' + nt(q.graph)} .`));
parser.on('error', e => { console.error(e.message); process.exit(1); });
parser.on('end', () => process.stdout.write(lines.join('\n') + '\n'));
fs.createReadStream(file).pipe(parser);
