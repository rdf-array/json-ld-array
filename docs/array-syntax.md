# Array syntax: candidates for SPARQL-array and ShEx-array, checked

*Design note, 2026-10-31. Proposes the syntax to replace the `((x))[i]` position patterns of
SPARQL-array and the `((shapeExpr))[m, n]` Collection shape expression of ShEx-array, which
[rdf-array.md](rdf-array.html#open-questions) listed as expected to change. Implemented on 2026-11-01 in
jena-array, shex.js-array, lezer-shexc-array, traqula-array and comunica-array, pyshexc, ShExJSG-array and
PyShEx-array, rdflib-array, oxigraph-array and rudof-array, with the shared suites rewritten to it. The grammars, the harness and the examples are in
[tools/array-syntax/](https://github.com/rdf-array/rdf-array/tree/rdf-sequences/tools/array-syntax), and
[array-syntax-uses.md](../management/array-syntax-uses.md) lists the files that adopting a new syntax would rewrite.*

The strawman spelled positions in SPARQL and member constraints in ShEx alike, as `(( … ))[ … ]`. The two
languages need different things, though. A SPARQL query matches members and binds variables to them and
to their positions; a ShEx schema constrains every member, often by position, as in a tuple. Other
languages keep the two apart: SQL, Cypher and JSONPath for the first; RELAX NG, CDDL, ASN.1 and JSON
Schema for the second. This note takes one design from each side, checks that it parses without conflicts
as part of the whole grammar, runs it on nested data (lists of lists, tuples of tuples and recursion), and
measures it against those languages (§6).

The proposals, in short:

- **SPARQL-array.** `UNNEST(expr AS ?x AT ?i)` binds each member and its 1-based position.
  `...` inside a pattern's `( … )` matches any run of members, and `...?rest` binds that run.
  `expr[i]` indexes and `expr[m...n]` slices. `?x IN ?seq` tests membership. `SEQ(…)`, `SEQLEN(…)`
  and `isSEQ(…)` build and inspect sequences. `()` is the empty sequence.
- **ShEx-array.** `LIST` takes two forms:
  - `LIST ( regex )` takes a regular expression over the members, with `;`, `|`, groups and
    cardinalities, as in a triple expression.
  - `LIST * x`, `LIST + x`, `LIST {m,n} x` take that many members, each matching x.

Both add no conflicts to their grammars (§3). On the examples (§4) they give the results expected.

## 1. SPARQL-array

### 1.1 Grammar

These productions change SPARQL 1.1's grammar (the names are SPARQL.js's, from which they were tested):

```
GraphPatternNotTriples ::= … | 'UNNEST' '(' Expression 'AS' Var ( 'AT' Var )? ')'
TriplesNodePath        ::= '(' SeqMemberPath+ ')'          # in WHERE: patterns
SeqMemberPath          ::= GraphNodePath | '...' | GAPVAR   # GAPVAR is '...' and a Var, with no space
TriplesNode            ::= '(' GraphNode+ ')'              # templates and data: no '...'
GraphTerm              ::= … | NIL                         # () is the empty sequence, not rdf:nil
UnaryExpression        ::= '!' PostfixExpression | '+' PostfixExpression | '-' PostfixExpression | PostfixExpression
PostfixExpression      ::= PrimaryExpression
                         | PostfixExpression '[' Expression ']'
                         | PostfixExpression '[' Expression? '...' Expression? ']'   # but not '[' '...' ']'
RelationalExpression   ::= … | NumericExpression 'NOT'? 'IN' ( ExpressionList | SeqRef )
SeqRef                 ::= Var | 'SEQ' ExpressionList | SeqRef '[' Expression ']'
BuiltInCall            ::= … | 'SEQ' ExpressionList | 'SEQLEN' '(' Expression ')' | 'isSEQ' '(' Expression ')'
```

The lexer adds `...`, `GAPVAR` (`...?rest`, one token), `UNNEST`, `AT`, `SEQ`, `SEQLEN` and `isSEQ`.

### 1.2 Meaning

- **A sequence in a pattern** matches a sequence of the same length, member by member, as today.
  **`...`** matches zero or more members, so `( ?first ... )`, `( ... ?last )` and `( ... ?x ... )` find
  the first member, the last member and every member. A pattern may hold several gaps, and gaps may nest:
  `( ... ( "8480-6" ?name ( ?v ?unit ) ) ... )` finds a 3-tuple anywhere in a list of tuples. A template
  or INSERT DATA has no gap, since it builds a sequence rather than matching one.
- **A named gap `...?rest`** matches like `...` and binds `?rest` to the run it matched, as a sequence.
  `( ?head ...?tail )` takes a list apart as `[h, ...t]` does in JavaScript, `[h, t @ ..]` in Rust and
  `[H|T]` in Prolog, and `( ...?before ?x ... )` gives `?x`'s position as `SEQLEN(?before) + 1`. The
  same variable twice must match equal runs. The token is `...` followed by the variable with no
  space: `( ?a ... ?b )` is a gap and then a member, `( ?a ...?b )` a named gap, as `:a .b` and `:a.b`
  already differ.
- **`UNNEST(expr AS ?x AT ?i)`** yields one solution per member of the sequence that `expr` evaluates to,
  binding `?x` to the member and `?i` to its position, counting from 1, like `for $x at $i in` in XQuery
  and `UNNEST … WITH ORDINALITY` in SQL. Two UNNESTs reach the cells of a matrix, and an UNNEST of a
  list of tuples, followed by `?x[j]`, reads one field of each tuple. When `expr` is unbound or not a
  sequence, there is no solution.
- **`expr[i]`** is the i-th member, counting from 1, and chains: `?rows[2][3]`. An index out of range, or
  applied to something other than a sequence, is an error, so a BIND leaves its variable unbound.
- **`expr[m...n]`** is the sequence of the members m to n, both included: `?pts[1...2]` is the first two,
  `?pts[2...]` the rest after the first, `?pts[...n]` the first n, `?rows[1][2...3]` the middle of the
  first row. The ends are expressions, so `?s[SEQLEN(?s) - 1 ... SEQLEN(?s)]` is the last two. The range is
  closed because the indexes are 1-based, as Swift's `...` and SQL's `a[2:4]` are. A slice is clamped
  to the sequence, as in SQL, Cypher and Python, so `SEQ(4, 5)[2...3]` is `(5)` and `SEQ()[2...]` is `()`,
  where an index out of range is an error. `:` cannot be the range mark, since `[2:4]` lexes `:4` as
  a prefixed name.
- **`?x IN ?seq`** is true when some member of the sequence equals `?x`. The needle may itself be a
  sequence: `SEQ(3, 4) IN ?points`. `?x IN ( … )` keeps its SPARQL 1.1 meaning, a list of expressions,
  so `?x IN (?seq)` asks whether `?x` equals `?seq`, not whether it is a member. The right-hand side of
  the new form is restricted to a variable, a `SEQ(…)` call or an indexed one of these, so that `IN (`
  still opens an expression list.
- **`=` and `!=`** compare whole sequences, members included, and so does a nested pattern:
  `?m :matrix ( ( 1 2 3 ) ( 4 5 6 ) )`.
- **In `ORDER BY` and `GROUP BY`** an index needs brackets, `ORDER BY (?x[1])`, because a bare `?x`
  there is a variable and not an expression.

## 2. ShEx-array

### 2.1 Grammar

`LIST` is a shape atom wherever one may stand (`shapeAtom`, `shapeAtomNoRef`, `inlineShapeAtom`),
except after `EXTENDS`:

```
listShape       ::= 'LIST' '(' listOneOf ')'
                  | 'LIST' cardinality inlineShapeAtom            # * + ? {m} {m,} {m,n} {m,*}
listOneOf       ::= listEachOf ( '|' listEachOf )*
listEachOf      ::= listUnary ( ';' listUnary )*
listUnary       ::= listMember cardinality?                     # how many members
listMember      ::= listMemberOr | '(' listOneOf ')'             # inside LIST ( ), '(' opens a group
listMemberOr    ::= listMemberAnd ( 'OR' inlineShapeAnd )*
listMemberAnd   ::= listMemberNot ( 'AND' inlineShapeNot )*
listMemberNot   ::= listMemberAtom | 'NOT' inlineShapeAtom
listMemberAtom  ::= nonLitInlineNodeConstraint inlineShapeOrRef? | litInlineNodeConstraint
                  | inlineShapeOrRef nonLitInlineNodeConstraint? | listShape | '.'
```

`listMemberAtom` is `inlineShapeAtom` without its parenthesised alternative. Only the member's
first atom loses the parentheses; later ones keep them, so `LIST ( @<B> AND ( @<A> OR @<C> ) )` is a
member. This is variant G of §3.

### 2.2 Meaning

- **`LIST ( regex )`** matches a sequence whose members, in order, match the regular expression. A member
  is a shape expression, and `;` (concatenation), `|` (choice), `( … )` (group) and cardinalities combine
  members as `;`, `|`, groups and cardinalities combine triple constraints in a triple expression.
  `LIST ( xsd:string ; xsd:integer )` is a pair, and `LIST ( xsd:integer * )` any list of integers.
  One difference from a triple expression: here `;` is ordered. `{ :a . ; :b . }` matches triples in any
  order, since a graph has none, while `LIST ( xsd:string ; xsd:integer )` takes the string first.
- **`LIST card x`** is short for `LIST ( x card )`: `LIST * xsd:integer` is any list of integers,
  `LIST + @<Track>` a non-empty list of tracks, `LIST {3} xsd:integer` three integers, and
  `LIST {2} LIST {3} xsd:integer` a 2×3 matrix, as CDDL's `[* int]`, `[+ track]`, `[3 int]` and
  `[2 [3 int]]`. The cardinality comes first because after a value expression it would count triples
  (next item). A bare `LIST xsd:integer` is a syntax error (§2.3).
- **A cardinality after the list belongs to the triple constraint**, as after any value expression.
  `:p LIST ( @<C> + ) {1,2}` and `:p LIST + @<C> {1,2}` both say one or two `:p` triples, each with
  a non-empty list of `<C>`.
- **ShExJ.** The harness writes `{ "type": "ListShape", "expression": … }`. Here `expression` is a
  `Member` (`{ "type": "Member", "shapeExpr": …, "min": …, "max": … }`) or an `EachOf` or `OneOf` of
  them, with `min` and `max` as on triple expressions, and both forms of §2.1 give the same ShExJ.
  Since this `EachOf` is ordered where a triple expression's is not, ShExJ may want it under another
  name, `ListEachOf`, so that a generic walker does not confuse the two. ShExR would follow ShExJ.

### 2.3 Alternatives that were rejected

- **Facets after the member** (`LIST xsd:string MINLENGTH 2`) conflict: ShEx's string facet `MINLENGTH`
  may follow `xsd:string` too, and with nesting, `LIST LIST x MINLENGTH 2` does not say which list
  the facet bounds. bison reports 14 shift/reduce conflicts (§3).
- **A member that may be any shape expression** makes `LIST ( ( @<A> ) … )` ambiguous: the `(` may open
  a group or a parenthesised shape expression. bison reports 7 shift/reduce and 31 reduce/reduce
  conflicts. Since a group holding one member means the same as that member, reading every such `(`
  as a group loses nothing.
- **`LIST` after `EXTENDS`.** In `EXTENDS LIST <S> { … }` the `{ … }` could be either the extending shape's
  body or a shape ANDed with `<S>`.
- **Bounds first only** (`LIST {m,n} x`, in the style of ASN.1's `SIZE`) has no conflicts, but it cannot
  say a tuple: `LIST ( xsd:string ; xsd:integer )` is a pair. It has no form for a flat list of pairs
  (§4.2) either. It survives as the shorthand of §2.1.
- **A bare `LIST x` for any number of x** (variant F) has no conflicts and is the shortest spelling of the
  commonest case, but it makes `LIST xsd:integer` and `LIST ( xsd:integer )` mean different things:
  any number of integers, and exactly one. `LIST * xsd:integer` costs two characters and has no such
  neighbour.

## 3. How they were checked

**The grammars are the real ones.** The SPARQL productions were added to SPARQL.js 3.7.4's Jison grammar,
which is the whole of SPARQL 1.1 Query and Update with SPARQL-star. The ShEx productions were added to
shex.js-array's ShExC grammar (commit `3980d3d6`), with the `((x))[m, n]` strawman and the precedence
that resolved its conflicts removed. That baseline is called B0 below. Each variant is B0 plus one
`listShape`.

**The checks are LALR(1) or stronger.**

- SPARQL's grammar was built with ts-jison as SLR(1) and as canonical LR(1). An SLR(1) grammar has no
  LALR(1) conflicts, because LALR(1) lookaheads are subsets of the SLR(1) follow sets.
- ShExC's grammar was converted to a bare bison grammar (the same rules and precedence declarations,
  with no actions) and checked by bison as LALR(1). It was also built by ts-jison as canonical LR(1).
- The converter is faithful: on the stock grammar it gives 0 conflicts, and with the strawman's `%prec`
  removed, bison reports the strawman's 4 known conflicts.
- ts-jison's own LALR(1) mode was not used. It reports 260 conflicts on stock SPARQL.js, and the parser
  it builds cannot parse `{ ?s ?p ?o }`.

| Grammar | LALR(1) (bison, or implied by SLR) | LR(1) (ts-jison) |
|---|---|---|
| SPARQL.js 3.7.4 + §1.1, slices and named gaps included | 0 (SLR(1): 0) | 0 |
| ShExC B0 (no list syntax) | 0 | 0 |
| A: `LIST {m,n}? x` | 0 | 0 |
| B: `LIST ( regex )`, a member any shape expression | 7 S/R, 31 R/R | 74 |
| C: `LIST ( regex )`, `(` opens a group | 0 | 0 |
| D: `LIST x MINLENGTH m MAXLENGTH n` | 14 S/R | not built: out of memory |
| E: C + `LIST {m,n} x` | 0 | 0 |
| F: E + `LIST x` | 0 | 0 |
| **G: C + `LIST card x`** (§2.1) | **0** | **0** |

**Regression.**

- B0 parses 488 of shexTest-array's 491 schemas; the other 3 now use `LIST`, which B0 does not have and G parses.
  It rejects all 105 negative-syntax tests.
- Variants A, B, C, E, F and G parse those 488 schemas to the same ShExJ as B0 and give the same verdict on
  every negative-syntax test.
- SPARQL.js's own test suite gives the same results with the patched grammar, except for the three
  runs of its `lists` test. Those expect a collection to give `rdf:first`/`rdf:rest` triples, where it
  is now one sequence term.

**The examples are run, not just parsed.** A small evaluator in the harness reads the data through
the patched grammar's INSERT DATA. It evaluates each query's parsed algebra and validates each
schema's parsed ShExJ, so the results below come from the parse trees.

## 4. Examples

The data, in Turtle-array:

```turtle
:obs1 :component ( ( "8480-6" "systolic"  ( 120 "mm[Hg]" ) )
                   ( "8462-4" "diastolic" (  80 "mm[Hg]" ) ) ) .
:obs2 :component ( ( "8480-6" "systolic"  ( 150 "mm[Hg]" ) )
                   ( "8462-4" "diastolic" (  95 "mm[Hg]" ) ) ) .
:obs3 :component ( ( "8480-6" "systolic"  ( "high" "mm[Hg]" ) ) ) .
:m1   :matrix ( ( 1 2 3 ) ( 4 5 6 ) ) .
:m2   :matrix ( ( 1 2 3 ) ( 4 5 ) ) .
:poly :points ( ( 0 0 ) ( 3 0 ) ( 3 4 ) ) .
:kv   :pairs  ( "a" 1 "b" 2 "c" 3 ) .
:tree :node   ( "root" ( ( "left" ( ) ) ( "right" ( ( "leaf" ( ) ) ) ) ) ) .
```

An observation's components are 3-tuples of a code, a name and a (value unit) pair. A matrix is a list
of rows, and `:m2`'s second row is short. A polyline is a list of points. `:kv` holds pairs flattened
into one list. A tree is a (label children) pair, whose children are trees.

### 4.1 SPARQL-array

**A tuple anywhere in a list of tuples.** The systolic reading, at whatever position it sits:

```sparql
SELECT ?obs ?v ?unit WHERE {
  ?obs :component ( ... ( "8480-6" ?name ( ?v ?unit ) ) ... )
}
```

| obs | v | unit |
|---|---|---|
| :obs1 | 120 | "mm[Hg]" |
| :obs2 | 150 | "mm[Hg]" |
| :obs3 | "high" | "mm[Hg]" |

**The first and the last member, nested.** The first point's x and the whole last point:

```sparql
SELECT ?x0 ?last WHERE { :poly :points ( ( ?x0 ?y0 ) ... ?last ) }
```

| x0 | last |
|---|---|
| 0 | (3 4) |

**Head and tail.** A named gap binds the rest of the list, and so does the slice `[2...]`:

```sparql
SELECT ?h ?t ?t2 WHERE {
  :poly :points ( ?h ...?t ) .
  :poly :points ?pts BIND(?pts[2...] AS ?t2)
}
```

| h | t | t2 |
|---|---|---|
| (0 0) | ((3 0) (3 4)) | ((3 0) (3 4)) |

**A position from a pattern.** The named gap before the match holds the members before it:

```sparql
SELECT ?x ?i WHERE { :poly :points ( ...?pre ?x ... ) BIND(SEQLEN(?pre) + 1 AS ?i) }
```

| x | i |
|---|---|
| (0 0) | 1 |
| (3 0) | 2 |
| (3 4) | 3 |

**Gaps at two levels of recursive data.** The root's children and their children:

```sparql
SELECT ?child ?grandchild WHERE {
  :tree :node ( "root" ( ... ( ?child ( ... ( ?grandchild ?kids ) ... ) ) ... ) )
}
```

| child | grandchild |
|---|---|
| "right" | "leaf" |

**UNNEST twice.** Every cell of every matrix, with its row and column:

```sparql
SELECT ?m ?i ?j ?x WHERE {
  ?m :matrix ?rows .
  UNNEST(?rows AS ?row AT ?i)
  UNNEST(?row AS ?x AT ?j)
}
```

| m | i | j | x |
|---|---|---|---|
| :m1 | 1 | 1 | 1 |
| :m1 | 1 | 2 | 2 |
| :m1 | 1 | 3 | 3 |
| :m1 | 2 | 1 | 4 |
| :m1 | 2 | 2 | 5 |
| :m1 | 2 | 3 | 6 |
| :m2 | 1 | 1 | 1 |
| :m2 | 1 | 2 | 2 |
| :m2 | 1 | 3 | 3 |
| :m2 | 2 | 1 | 4 |
| :m2 | 2 | 2 | 5 |

**UNNEST, then index into each tuple.** The components whose value is at least 90, with their positions.
`:obs3`'s `"high"` drops out, because comparing it with 90 is a type error:

```sparql
SELECT ?obs ?i ?code ?v WHERE {
  ?obs :component ?c .
  UNNEST(?c AS ?comp AT ?i)
  BIND(?comp[1] AS ?code)
  BIND(?comp[3][1] AS ?v)
  FILTER(?v >= 90)
}
```

| obs | i | code | v |
|---|---|---|---|
| :obs1 | 1 | "8480-6" | 120 |
| :obs2 | 1 | "8480-6" | 150 |
| :obs2 | 2 | "8462-4" | 95 |

**A slice of every row.** Columns 2 to 3 of each row, numpy's `a[:, 1:3]` taken row by row; the short
row of `:m2` gives what it has:

```sparql
SELECT ?m ?i ?cols WHERE {
  ?m :matrix ?rows .
  UNNEST(?rows AS ?row AT ?i)
  BIND(?row[2...3] AS ?cols)
}
```

| m | i | cols |
|---|---|---|
| :m1 | 1 | (2 3) |
| :m1 | 2 | (5 6) |
| :m2 | 1 | (2 3) |
| :m2 | 2 | (5) |

**Stride.** The keys of a flat key/value list sit at the odd positions, and each value is the member after
its key. SPARQL has no modulo operator, so the odd positions are `?i - 2 * FLOOR(?i / 2) = 1`:

```sparql
SELECT ?k ?v WHERE {
  :kv :pairs ?p .
  UNNEST(?p AS ?k AT ?i)
  BIND(?p[?i + 1] AS ?v)
  FILTER(?i - 2 * FLOOR(?i / 2) = 1)
}
```

| k | v |
|---|---|
| "a" | 1 |
| "b" | 2 |
| "c" | 3 |

**Chained indexes.** An index out of range leaves `?cell` unbound:

```sparql
SELECT ?m ?cell ?len WHERE {
  ?m :matrix ?rows .
  BIND(?rows[2][3] AS ?cell)
  BIND(SEQLEN(?rows[2]) AS ?len)
}
```

| m | cell | len |
|---|---|---|
| :m1 | 6 | 3 |
| :m2 |  | 2 |

**A sequence as the needle.** The polylines through the point (3 4):

```sparql
SELECT ?s WHERE { ?s :points ?pts FILTER(SEQ(3, 4) IN ?pts) }
```

| s |
|---|
| :poly |

**Whole nested values.** These are compared by an expression and by a pattern:

```sparql
SELECT ?m ?n WHERE {
  ?m :matrix ?rows FILTER(?rows = SEQ(SEQ(1, 2, 3), SEQ(4, 5, 6)))
  ?n :matrix ( ( 1 2 3 ) ( 4 5 6 ) )
}
```

| m | n |
|---|---|
| :m1 | :m1 |

### 4.2 ShEx-array

| Shapes | Focus → result |
|---|---|
| `<BP> LIST + @<Component>`<br>`<Component> LIST ( xsd:string ; xsd:string ; LIST ( xsd:integer ; xsd:string ) )` | `:obs1`'s and `:obs2`'s components conform; `:obs3`'s fail (`"high"` is not an integer) |
| `<Matrix2x3> LIST ( LIST ( xsd:integer {3} ) {2} )` | `:m1` conforms; `:m2` fails |
| `<Matrix2x3> LIST {2} LIST {3} xsd:integer` (the same ShExJ) | `:m1` conforms; `:m2` fails |
| `<Ragged> LIST ( LIST ( xsd:integer * ) * )`, or `LIST * LIST * xsd:integer` | `:m1` and `:m2` conform |
| `<Polyline> LIST ( LIST ( xsd:integer ; xsd:integer ) {2,} )` | `:poly` conforms; `:m1` fails |
| `<Pairs> LIST ( ( xsd:string ; xsd:integer ) * )` | `:kv` conforms; `:poly` fails |
| `<IntsOrPairs> LIST ( ( xsd:integer \| LIST ( xsd:integer ; xsd:integer ) ) + )` | `:poly` conforms; `:m1` fails |
| `<Tree> LIST ( xsd:string ; LIST ( @<Tree> * ) )` | `:tree` conforms; `:m1` fails |

`<Pairs>` is a repeated group. It is the one shape here that nesting `LIST`s cannot say, because its pairs
are not sequences of their own. `<Tree>` recurses through two levels of list at each step.

## 5. Edge cases and limits

Each case was parsed by the variant shown; the harness lists them with the results.

- **Lexing `...`.** SPARQL.js's lexer takes the longest match, so `...` wins over `.`. `( 1... )` is 1
  followed by a gap, and so is `( :a... )`, since a local name cannot end in `.`. But `( :a...b )` is
  one prefixed name, as `:a.b` already is. `[2...4]` is 2, `...`, 4, since `...` also wins over the
  decimal `.4`.
- **No gap outside patterns.** `CONSTRUCT { ?s :p ( ?a ... ) }` is a syntax error.
- **A named gap is one token.** `( ?a ...?b )` names the gap; `( ?a ... ?b )` is a gap and then the
  member `?b`. The parse checks both.
- **No stride in patterns.** `:kv :pairs ( ... ?k ?v ... )` matches every adjacent pair, ("b" 2) as well
  as (1 "b"); the UNNEST idiom of §4.1 is the way, or `( ...?pre ?k ?v ... )` with the same test on
  `SEQLEN(?pre)`.
- **`LIST x` is an error in G.** `LIST xsd:integer` is rejected with the message that `(`, `*`, `+`, `?` or
  a `{m,n}` was expected, and `LIST ( xsd:integer )` is exactly one integer. In F, `LIST xsd:integer`
  parsed and meant any number (§2.3).
- **A parenthesised first member.** Inside `LIST ( )`, `( ( @<A> ) AND @<B> )` is a syntax error,
  because the second `(` opens a group, and a group cannot be followed by `AND`. Write
  `( @<A> AND @<B> )`, or `@<B> AND ( @<A> )`.
- **Cardinalities.** In `:component LIST ( @<Component> + ) {1,2}` and `:p LIST * xsd:integer {1,2}`,
  the cardinality inside, or before the member, counts the list's members and the one after counts
  triples. This is checked by the parse.
- **Empty sequences.** `()` in a pattern or data is the empty sequence. `LIST ( @<Tree> * )` accepts it,
  and `LIST ( x + )` does not.

## 6. Against other languages

The comparison set is not numpy, whose slicing (`a[:, 0]`, `a[1:3, ::2]`, broadcasting) relies on dense,
rectangular, homogeneous arrays of a known rank. An rdf-array sequence is ragged, nested and mixed, like
a JSON array or a Lisp list, so the languages to measure against are SQL's arrays, Cypher's lists, XQuery's
sequences, JSONPath and jq, with numpy as the ceiling for index expressions; and on the schema side the
regular-expression types of XDuce and CDuce, RELAX NG's `<list>`, CDDL and JSON Schema.

| Need | This note | Cypher | PostgreSQL | XQuery | JSONPath, numpy |
|---|---|---|---|---|---|
| each member | `UNNEST(?s AS ?x)`, `( ... ?x ... )` | `UNWIND l AS x` | `unnest(a)` | `for $x in $s` | `$[*]` |
| with its position | `UNNEST(?s AS ?x AT ?i)` | `UNWIND range(0, size(l)-1)` | `WITH ORDINALITY` | `for $x at $i in $s` | — |
| i-th member | `?s[2]`, `( ?a ?x ... )` | `l[1]` | `a[2]` | `$s[2]` | `a[1]` |
| a nested cell | `?m[2][3]` | `l[1][2]` | `a[2][3]` | — | `a[1, 2]` |
| last | `( ... ?x )`, `?s[SEQLEN(?s)]` | `l[-1]`, `last(l)` | `a[cardinality(a)]` | `$s[last()]` | `a[-1]` |
| length | `SEQLEN(?s)` | `size(l)` | `cardinality(a)` | `count($s)` | `len(a)` |
| membership | `?x IN ?s` | `x IN l` | `x = ANY(a)` | `$x = $s` | — |
| head and tail | `( ?h ...?t )`, `?s[2...]` | `head(l)`, `tail(l)`, `l[1..]` | `a[2:]` | `subsequence($s, 2)` | `a[1:]` |
| slice | `?s[2...4]` | `l[1..4]` | `a[2:4]` | `subsequence($s, 2, 3)` | `a[1:4]` |
| a tuple anywhere, nested | `( ... ( "c" ?n ( ?v ?u ) ) ... )` | — | — | — | — |
| stride | UNNEST and `FLOOR` (§4.1) | — | — | — | `a[::2]`, `$[::2]` |
| map over members, to a list | — | `[x IN l \| x.p]` | `array_agg` in a subquery | `$s ! f(.)` | `a[:, 0]` |
| filter members, to a list | — | `[x IN l WHERE p]` | `array_agg` in a subquery | `$s[. > 3]` | a boolean mask |
| a list from solutions | — | `collect(x)` | `array_agg(x ORDER BY i)` | `for … return` | — |
| at any depth | — | — | — | `//` | `$..x` |
| a list of T, n of T, a tuple, a repeated group, a choice, recursion | `LIST` (§2) | — | — | RELAX NG, CDDL: `[* int]`, `[3 int]`, `[str, int]`, `[* (str, int)]` | JSON Schema `items`, `prefixItems`, `minItems` |

Where the note is ahead: the nested gap pattern finds a tuple anywhere in a list of tuples in one line,
which Cypher, SQL and JSONPath do with an unwind, an index and a filter. Where it is behind, the three
rows without an entry are one gap. SPARQL has no aggregate that builds a sequence from solutions, and
`SEQ(…)` takes a fixed number of arguments, so the inverse of UNNEST (repeated properties into one
sequence, the second half of rdf-array.md's update example) and the map and filter rows, which in a
query language are UNNEST and then that aggregate, cannot be written. A `COLLECT(?x)` in the family of
Cypher's `collect` and SQL's `array_agg` would fill all three; its order needs design, since SPARQL's
aggregates take no `ORDER BY`, and it is not in the grammar yet. Two smaller matters are open too:
`?s[-1]` parses already, and could count from the end as in Cypher and Lua, which is 1-based as well;
and nothing reaches a member at any depth, which would take a recursive construct.

## 7. Implementing it: the strawman

What an implementation reads, writes and requires, fixed here so that the forks agree. Everything in
this section is a first choice, to be revised with the implementations.

**ShExJ.** `ListShape` replaces `Collection`:

```json
{ "type": "ListShape", "expression": listExpr }
listExpr   = Member | ListEachOf | ListOneOf
Member     = { "type": "Member",     "shapeExpr": shapeExpr,        "min": m, "max": n }
ListEachOf = { "type": "ListEachOf", "expressions": [ listExpr… ], "min": m, "max": n }
ListOneOf  = { "type": "ListOneOf",  "expressions": [ listExpr… ], "min": m, "max": n }
```

`min` and `max` are as on triple expressions: absent means 1, and `-1` is unbounded. `LIST card x` is
`{ "type": "ListShape", "expression": { "type": "Member", "shapeExpr": x, "min": …, "max": … } }`, the
same as `LIST ( x card )`. A cardinality on a group sets the group's `min` and `max`; when the group's
expression carries a cardinality already, as `( x {2} ) {3}` does, it is wrapped in a `ListEachOf` of
one. The old `{ "type": "Collection", "shapeExpr": x, "min": m, "max": n }` is exactly
`{ "type": "ListShape", "expression": { "type": "Member", "shapeExpr": x, "min": m, "max": n } }`.
The names `ListEachOf` and `ListOneOf` are distinct from `EachOf` and `OneOf` because the first is
ordered and the second is not (§2.2).

**ShExR.** `sx:ListShape` with `sx:expression`; `sx:Member` with `sx:shapeExpr`, `sx:min` and `sx:max`;
`sx:ListEachOf` and `sx:ListOneOf` with `sx:expressions ( … )`, a sequence as `sx:shapeExprs` is, and
`sx:min` and `sx:max`. They replace `sx:Collection`.

**Validation results.** Where an implementation reports per-member results (shex.js's shexv), they are
named after the shape: `ListShapeResults` with one solution per member in order, and
`ListShapeFailure` holding either a `ListLengthViolation` or a `ListMemberFailure` with the member's
index, in place of the `Collection…` names.

**The `ra:` requirements of the test manifests.** `ra:GapPatterns` (`...` and `...?rest` in a sequence
pattern) and `ra:Unnest` replace `ra:PositionPatterns`; `ra:SequenceFunctions` keeps its name and now
covers `isSEQ`, `SEQLEN`, `SEQ`, `expr[i]`, `expr[m...n]` and `IN ?seq`; `ra:ListShapeExpression`
replaces `ra:CollectionShapeExpression`.

**Rewriting what uses the old syntax.** [array-syntax-uses.md](../management/array-syntax-uses.md) lists
the files. In ShExC, `((x))[m, n]` becomes `LIST {m,n} x` when x is an atom and `LIST {m,n} ( x )`
when it is not; `((x))` becomes `LIST * x`, `[1, *]` becomes `+`, `[n]` becomes `{n}`, and
`((((x))[2]))[3, *]` becomes `LIST {3,} LIST {2} x`. In SPARQL, `((?e))[?i]` and `((?e))[*]` become
`UNNEST(?seq AS ?e AT ?i)` on the sequence bound by the triple pattern, and `((?e))[n]` with a constant
becomes the pattern with n−1 fresh variables before `?e` and `...` after it, or an UNNEST with
`FILTER(?i = n)`, whichever keeps the test's expected results; a test whose point was the old spelling
(the bad-position syntax tests) is replaced by one for the new (`[2:4]`, a gap in a template, a bare
`LIST x`). The shared suites also gain the data, queries, shapes and results of §4.

## 8. Reproducing

```bash
tools/array-syntax/run.sh
```

The script needs git, node, python3, bison, a checkout of shex.js-array with its `node_modules` (for
ts-jison and the parser's dependencies), and a checkout of shexTest-array. It clones SPARQL.js 3.7.4
and applies `sparql.jison.patch`. It writes the ShExC variants with `variants.py`, checks each with bison
and ts-jison, and runs the shexTest corpus through each. Last, it runs the examples and edge cases of
`examples.js` into `demo.md` in its work directory. The whole run takes about two minutes.
