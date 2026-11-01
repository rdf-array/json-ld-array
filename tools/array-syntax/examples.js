// Examples run by demo.js. SPARQL: [title, query]. ShEx: [title, variant, schema, [[subject, predicate, shape]...]].
exports.sparql = [
  ['Ellipsis, nested: the systolic reading, wherever it sits in the list of tuples', `
SELECT ?obs ?v ?unit WHERE {
  ?obs :component ( ... ( "8480-6" ?name ( ?v ?unit ) ) ... )
}`],
  ['First and last members, nested: the first point\'s x and the whole last point', `
SELECT ?x0 ?last WHERE { :poly :points ( ( ?x0 ?y0 ) ... ?last ) }`],
  ['Head and tail: a named gap binds the rest of the list, as the slice [2...] does', `
SELECT ?h ?t ?t2 WHERE {
  :poly :points ( ?h ...?t ) .
  :poly :points ?pts BIND(?pts[2...] AS ?t2)
}`],
  ['A position from a pattern: the named gap before the match has the members before it', `
SELECT ?x ?i WHERE { :poly :points ( ...?pre ?x ... ) BIND(SEQLEN(?pre) + 1 AS ?i) }`],
  ['Two levels of ellipsis in recursive data: the root\'s children and grandchildren', `
SELECT ?child ?grandchild WHERE {
  :tree :node ( "root" ( ... ( ?child ( ... ( ?grandchild ?kids ) ... ) ) ... ) )
}`],
  ['UNNEST twice: every matrix cell with its row and column', `
SELECT ?m ?i ?j ?x WHERE {
  ?m :matrix ?rows .
  UNNEST(?rows AS ?row AT ?i)
  UNNEST(?row AS ?x AT ?j)
}`],
  ['UNNEST, then index into each tuple: components whose value is at least 90', `
SELECT ?obs ?i ?code ?v WHERE {
  ?obs :component ?c .
  UNNEST(?c AS ?comp AT ?i)
  BIND(?comp[1] AS ?code)
  BIND(?comp[3][1] AS ?v)
  FILTER(?v >= 90)
}`],
  ['Slices of every row: columns 2 to 3, clamped to a short row', `
SELECT ?m ?i ?cols WHERE {
  ?m :matrix ?rows .
  UNNEST(?rows AS ?row AT ?i)
  BIND(?row[2...3] AS ?cols)
}`],
  ['Stride: the keys at odd positions of a flat key/value list, each with the member after it', `
SELECT ?k ?v WHERE {
  :kv :pairs ?p .
  UNNEST(?p AS ?k AT ?i)
  BIND(?p[?i + 1] AS ?v)
  FILTER(?i - 2 * FLOOR(?i / 2) = 1)
}`],
  ['Chained indexes and SEQLEN; out-of-range leaves ?cell unbound', `
SELECT ?m ?cell ?len WHERE {
  ?m :matrix ?rows .
  BIND(?rows[2][3] AS ?cell)
  BIND(SEQLEN(?rows[2]) AS ?len)
}`],
  ['IN a sequence, with a sequence as the needle: polylines through (3 4)', `
SELECT ?s WHERE { ?s :points ?pts FILTER(SEQ(3, 4) IN ?pts) }`],
  ['Whole nested values: by expression, and by pattern', `
SELECT ?m ?n WHERE {
  ?m :matrix ?rows FILTER(?rows = SEQ(SEQ(1, 2, 3), SEQ(4, 5, 6)))
  ?n :matrix ( ( 1 2 3 ) ( 4 5 6 ) )
}`],
];
exports.shex = [
  ['Blood pressure: a non-empty list of 3-tuples whose third member is a (value unit) pair', 'G', `
<BP>        LIST + @<Component>
<Component> LIST ( xsd:string ; xsd:string ; LIST ( xsd:integer ; xsd:string ) )`,
    [['obs1', 'component', 'BP'], ['obs2', 'component', 'BP'], ['obs3', 'component', 'BP']]],
  ['A 2×3 matrix, and a ragged list of lists', 'G', `
<Matrix2x3> LIST ( LIST ( xsd:integer {3} ) {2} )
<Ragged>    LIST ( LIST ( xsd:integer * ) * )`,
    [['m1', 'matrix', 'Matrix2x3'], ['m2', 'matrix', 'Matrix2x3'], ['m1', 'matrix', 'Ragged'], ['m2', 'matrix', 'Ragged']]],
  ['The same two with the cardinality-first shorthand', 'G', `
<Matrix2x3S> LIST {2} LIST {3} xsd:integer
<RaggedS>    LIST * LIST * xsd:integer`,
    [['m1', 'matrix', 'Matrix2x3S'], ['m2', 'matrix', 'Matrix2x3S'], ['m1', 'matrix', 'RaggedS'], ['m2', 'matrix', 'RaggedS']]],
  ['Bounds-first only (variant A), no member regular expressions', 'A', `
<Matrix2x3A> LIST {2} LIST {3} xsd:integer`,
    [['m1', 'matrix', 'Matrix2x3A'], ['m2', 'matrix', 'Matrix2x3A']]],
  ['A polyline: at least two (x y) points', 'G', `
<Polyline> LIST ( LIST ( xsd:integer ; xsd:integer ) {2,} )`,
    [['poly', 'points', 'Polyline'], ['m1', 'matrix', 'Polyline']]],
  ['A flat key/value list: a repeated group, which a nested LIST cannot say', 'G', `
<Pairs> LIST ( ( xsd:string ; xsd:integer ) * )`,
    [['kv', 'pairs', 'Pairs'], ['poly', 'points', 'Pairs']]],
  ['Alternatives among members: each member an integer or an (x y) pair', 'G', `
<IntsOrPairs> LIST ( ( xsd:integer | LIST ( xsd:integer ; xsd:integer ) ) + )`,
    [['poly', 'points', 'IntsOrPairs'], ['m1', 'matrix', 'IntsOrPairs']]],
  ['Recursion through nested lists: a tree as (label (child ...))', 'G', `
<Tree> LIST ( xsd:string ; LIST ( @<Tree> * ) )`,
    [['tree', 'node', 'Tree'], ['m1', 'matrix', 'Tree']]],
];
exports.edges = [
  ['A gap is a pattern, so CONSTRUCT templates reject it', 'sparql', 'CONSTRUCT { ?s :p ( ?a ... ) } WHERE { ?s :p ?a }', 'rejected'],
  ['`1...` lexes as 1 then ...', 'sparql', 'SELECT * { ?s :p ( 1... ) }', '(1 ...)'],
  ['`:a...` lexes as :a then ... (a local name cannot end in .)', 'sparql', 'SELECT * { ?s :p ( :a... ) }', '(:a ...)'],
  ['but `:a...b` is one prefixed name, as `:a.b` already is', 'sparql', 'SELECT * { ?s :p ( :a...b ) }', '(:a...b)'],
  ['`( ?a ... ?b )` is a gap and then a member; `( ?a ...?b )` is a named gap', 'sparql', 'SELECT * { ?s :p ( ?a ... ?b ) . ?s :q ( ?a ...?b ) }', '(?a ... ?b), then (?a ...?b)'],
  ['`[2:4]` cannot be a slice: `:4` is a prefixed name', 'sparql', 'SELECT * { ?s :p ?o BIND(?o[2:4] AS ?x) }', 'rejected'],
  ['`[2...4]` lexes as 2, ..., 4; the ends may be expressions or absent', 'sparql', 'SELECT * { ?s :p ?o BIND(?o[2...4] AS ?x) BIND(?o[...SEQLEN(?o) - 1] AS ?y) BIND(?o[2...][1] AS ?z) }', 'slice, slice, index of a slice'],
  ['IN ( list ) keeps its SPARQL 1.1 meaning; IN ?seq is the new form', 'sparql', 'SELECT * { ?s :p ?o FILTER(?o IN (?a) && ?o IN ?a) }', 'in, then inseq'],
  ['Nested positions without UNNEST: chained ellipsis patterns bind no index', 'sparql', 'SELECT * { ?m :matrix ( ... ( ... ?x ... ) ... ) }', 'nested gaps'],
  ['G: LIST * x, LIST + x and LIST {m,n} x are LIST ( x * ), LIST ( x + ) and LIST ( x {m,n} )', 'G', '<S> LIST * xsd:integer <T> LIST + @<A> <U> LIST {2,3} .', 'parsed'],
  ['G: a bare LIST x is a syntax error, not a different meaning from LIST ( x )', 'G', '<S> LIST xsd:integer', 'rejected'],
  ['G: LIST ( x ) is the regular expression form: exactly one x', 'G', '<S> LIST ( xsd:integer )', 'exactly one'],
  ['G: cardinality-first with a parenthesised member', 'G', '<S> LIST {2} ( @<A> OR @<B> )', 'two of (A OR B)'],
  ['G: inside LIST ( ), a member may not start with ( : that ( is always a group', 'G', '<S> LIST ( ( @<A> ) AND @<B> )', 'rejected'],
  ['G: a parenthesis later in a member is an ordinary shape expression', 'G', '<S> LIST ( @<B> AND ( @<A> OR @<C> ) )', 'parsed'],
  ['G: a group holding one member means the same as the member', 'G', '<S> LIST ( ( @<A> OR @<B> ) * )', 'group of one OR'],
  ['G: the cardinality after LIST ( ) is the triple constraint\'s', 'G', '<S> { :component LIST ( @<Component> + ) {1,2} }', 'member +, triple {1,2}'],
  ['G: cardinality-first LIST shares the triple cardinality after it', 'G', '<S> { :p LIST * xsd:integer {1,2} }', 'list *, triple {1,2}'],
  ['A: LIST without bounds takes any length', 'A', '<S> LIST LIST xsd:integer', 'parsed'],
  ['E: LIST ( … ) is always the regex form, so bounds-first needs bounds', 'E', '<S> LIST xsd:integer', 'rejected'],
  ['F: LIST atom without bounds, when the atom does not start with (', 'F', '<S> LIST LIST xsd:integer', 'any-length list of any-length lists'],
  ['F: but LIST ( x ) is exactly one x: the trap G removes', 'F', '<S> LIST ( xsd:integer )', 'exactly one'],
];
