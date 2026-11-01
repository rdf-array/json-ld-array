// Parse SPARQL with a ts-jison build of SPARQL.js's grammar.
const path = require('path');
const { DataFactory } = require('rdf-data-factory');
module.exports = function load(built) {
  const { SparqlParserParser, ParserStatics: P } = require(path.resolve(built));
  return function parse(q) {
    Object.assign(P, { base: '', prefixes: Object.create({}), factory: new DataFactory(),
                       sparqlStar: true, pathOnly: false, skipValidation: true });
    P._resetBlanks();
    return new SparqlParserParser().parse(q);
  };
};
