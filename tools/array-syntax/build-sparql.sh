#!/bin/sh
# usage: [MODE=slr|lr|lalr] build-sparql.sh grammar.jison out.js
set -e
# ts-jison leaves the grammar's free `Parser` (SPARQL.js's static settings holder) undefined; supply one
# that also behaves like jison's exported Parser, so SPARQL.js's sparql.js and tests run unchanged.
"${SHEXJS:-$HOME/checkouts/rdf-array/shex.js-array}"/node_modules/.bin/ts-jison -t javascript -p ${MODE:-slr} -n SparqlParser -o "$2.tmp" "$1" > "$2.log" 2>&1 || { echo "the build of $2 failed; see $2.log" >&2; exit 1; }
{ echo 'var Parser = function () { return new SparqlParserParser(); }; exports.ParserStatics = Parser;'
  cat "$2.tmp"
  echo 'Parser.prototype = SparqlParserParser.prototype; exports.Parser = Parser;'; } > "$2" && rm "$2.tmp"
