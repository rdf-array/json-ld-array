#!/usr/bin/env node
// Run a SPARQL query with comunica-array over local data and print the results in a given format.
//   node comunica-array-query.js QUERY.rq DATA.ttl|- MEDIATYPE
// MEDIATYPE: application/sparql-results+json, application/sparql-results+xml, text/csv,
// text/tab-separated-values, or application/n-triples for CONSTRUCT/DESCRIBE.
const fs = require('fs');
const path = require('path');
const fork = process.env.COMUNICA_ARRAY || path.join(process.env.HOME, 'checkouts/rdf-array/comunica-array');
const { QueryEngine } = require(path.join(fork, 'engines/query-sparql'));
const [queryFile, dataFile, mediaType] = process.argv.slice(2);
(async () => {
  const engine = new QueryEngine();
  const sources = dataFile === '-' ? [] : [{
    type: 'serialized',
    value: fs.readFileSync(dataFile, 'utf8'),
    mediaType: dataFile.endsWith('.nt') ? 'application/n-triples' : dataFile.endsWith('.trig') ? 'application/trig' : 'text/turtle',
    baseIRI: 'file://' + path.resolve(dataFile),
  }];
  const result = await engine.query(fs.readFileSync(queryFile, 'utf8'), { sources, baseIRI: 'file://' + path.resolve(queryFile) });
  const { data } = await engine.resultToString(result, mediaType);
  data.on('data', chunk => process.stdout.write(chunk));
  data.on('error', e => { console.error(e.message); process.exit(1); });
})().catch(e => { console.error(e.message); process.exit(1); });
