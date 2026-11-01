#!/bin/sh
# Reproduce docs/array-syntax.md: the conflict counts of the SPARQL and ShEx candidates, the shexTest
# regression, and the nested examples (written to $WORK/demo.md).
#   tools/array-syntax/run.sh            # WORK defaults to a new temporary directory
# Needs git, node, python3, bison, a checkout of shex.js-array with its node_modules (for ts-jison
# and the parser's dependencies) and one of shexTest-array. Set SHEXJS and SHEXTEST to elsewhere.
set -e
H=$(cd "$(dirname "$0")" && pwd)
SHEXJS=${SHEXJS:-$HOME/checkouts/rdf-array/shex.js-array}
SHEXTEST=${SHEXTEST:-$HOME/checkouts/rdf-array/shexTest-array}
SHEXJS_COMMIT=3980d3d6       # shex.js-array's grammar, with the ((x))[m,n] strawman the variants replace
SPARQLJS_TAG=v3.7.4
WORK=${WORK:-$(mktemp -d)}; export WORK SHEXJS
J=$SHEXJS/node_modules/.bin/ts-jison
export NODE_PATH=$SHEXJS/packages/shex-parser/node_modules:$SHEXJS/node_modules
conflicts() { grep -c 'Conflict in' "$1" || true; }
echo "work directory: $WORK"

# SPARQL: SPARQL.js's grammar, stock and patched, as SLR(1) (none implies none as LALR(1)) and LR(1).
# ts-jison's LALR(1) mode is not used: it reports conflicts the grammar does not have.
git -c advice.detachedHead=false clone -q --depth 1 --branch $SPARQLJS_TAG https://github.com/RubenVerborgh/SPARQL.js "$WORK/sparqljs"
cp "$WORK/sparqljs/lib/sparql.jison" "$WORK/sparql-base.jison"
git -C "$WORK/sparqljs" apply "$H/sparql.jison.patch"
for g in base new; do
  src=$WORK/sparql-base.jison; [ $g = new ] && src=$WORK/sparqljs/lib/sparql.jison
  MODE=slr "$H/build-sparql.sh" "$src" "$WORK/sparql-$g-slr.js"
  MODE=lr  "$H/build-sparql.sh" "$src" "$WORK/sparql-$g-lr.js"
  echo "SPARQL $g: SLR(1) $(conflicts "$WORK/sparql-$g-slr.js.log") conflicts, LR(1) $(conflicts "$WORK/sparql-$g-lr.js.log") conflicts"
done
cp "$WORK/sparql-new-slr.js" "$WORK/sparqljs/lib/SparqlParser.js"   # beside ./Wildcard, which it requires

# ShEx: the variants of shex.js-array's ShExC grammar, as LALR(1) by bison and LR(1) by ts-jison.
# The stock grammar without its %prec shows the converter keeps the strawman's conflicts.
git -C "$SHEXJS" show $SHEXJS_COMMIT:packages/shex-parser/lib/ShExJison.jison > "$WORK/ShExJison.jison"
cp "$SHEXJS/packages/shex-parser/lib/shex-parser.js" "$WORK/"   # built from src/, so not in git; it loads ./ShExJison
python3 "$H/jison2bison.py" "$WORK/ShExJison.jison" "$WORK/shex-stock.y"
grep -v '^%nonassoc' "$WORK/shex-stock.y" | sed 's/ %prec PAREN_SHAPE_EXPR//' > "$WORK/shex-noprec.y"
for y in stock noprec; do
  echo "ShExC $y: LALR(1) $(bison -v -o "$WORK/shex-$y.tab.c" "$WORK/shex-$y.y" 2>&1 | grep -o 'conflicts:.*' || echo 0 conflicts)"
done
mkdir -p "$WORK/v"
python3 "$H/variants.py" "$WORK/ShExJison.jison" "$WORK/v"
for v in B0 A B C D E F G; do
  python3 "$H/jison2bison.py" "$WORK/v/$v.jison" "$WORK/v/$v.y"
  b=$(bison -v -o "$WORK/v/$v.tab.c" "$WORK/v/$v.y" 2>&1 | grep -o 'conflicts:.*' || echo '0 conflicts')
  if [ $v = D ]; then echo "ShExC $v: LALR(1) $b; LR(1) not built (the canonical table exhausts memory)"; continue; fi
  "$J" -t javascript -p lr -n ShExJison -o "$WORK/v/$v.js" "$WORK/v/$v.jison" > "$WORK/v/$v.lr.log" 2>&1 ||
    { echo "ShExC $v: the LR(1) build failed; see $WORK/v/$v.lr.log"; exit 1; }
  echo "ShExC $v: LALR(1) $b; LR(1) $(conflicts "$WORK/v/$v.lr.log") conflicts"
  mkdir -p "$WORK/run/$v"; cp "$WORK/v/$v.js" "$WORK/run/$v/ShExJison.js"; cp "$WORK/shex-parser.js" "$WORK/run/$v/"
done

node "$H/corpus.js" "$SHEXTEST" A B C E F G
node "$H/demo.js" > "$WORK/demo.md"
echo "examples and edge cases: $WORK/demo.md"
