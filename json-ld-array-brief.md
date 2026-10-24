# JSON-LD-array: brief for a sanity check and a jsonld.js prototype

Paste-ready summary of `json-ld-array.md` (design sketch, 2026-10-23, https://github.com/rdf-array/rdf-array). The
target is a fork of https://github.com/digitalbazaar/jsonld.js whose `toRDF` accepts a JSON-LD-array
mapping, so the language can be tried in a locally modified JSON-LD playground. The full document has
the tables of examples; this brief has the rules.

## What it is

A mapping language from **conventional JSON** (no `@` keywords in the data) to **rdf-array**, RDF with
a fifth kind of term, the **sequence**: `(1 2 3)` is one term, `()` the empty sequence, no
`rdf:first`/`rdf:rest`. Sister syntaxes: Turtle-array, SPARQL-array, ShEx-array. Repos and forks live
in the GitHub organisation rdf-array (branch `rdf-sequences`); the JS stack there has RDF/JS types,
data factory, N3.js, JSON-LD streaming parser and serializer, and a Comunica engine that already
speak sequences (`termType: "Sequence"`, `elements`, `DataFactory.sequence()`).

Goals: (1) no legacy simplifications, so prefixes, property definitions, class definitions and
directives each have their own place; (2) the part of a document that produces RDF carries no
directives, the mapping lives in its own document or in two reserved members; (3) no `@list`/`@set`:
arrays are sequences, dictionaries are repeated properties, spreading is done afterwards in
SPARQL-array; (4) one construct for property mappings, `propertyMap`, inline or named.

## Terminology

A JSON object's members have a *key* (the name) and a value (RFC 8259 §4, JSON-LD 1.1 §1.4, Infra).
"Key" always means a member name in the data; members of the mapping are "attributes". Keys are plain
strings compared code unit by code unit, never expanded as compact IRIs. "The identifier key" names a
key by the role its definition gives it; what names the node is always that member's *value*.

## Value kinds

| JSON | rdf-array |
|---|---|
| object | a node: fresh blank node, or the node its identifier key's value names |
| array | one sequence term of the converted elements, in order; `[]` → `()` |
| object declared `keyedBy` | a dictionary: one value of the property per entry, unordered → repeated property |
| string | plain literal; or an identifier (IRI or blank node) under `valueType: "identifier"`; or typed / language-tagged under `datatype` / `language` |
| number | `xsd:integer` if no fraction or exponent, else `xsd:decimal`; `datatype` overrides and decides the lexical form |
| boolean | `xsd:boolean` |
| null | nothing (no triple, no sequence element) |

## The mapping document

Root attributes: `prefixes` (mapping-side only, root only); `base` (initial base, then lexically
scoped); `vocab`; `unmappedKeys`; `unmappedTypes`; `typeMap`; `propertyMap`; `namedPropertyMaps`;
`namedTypeMaps` (root only).

`unmappedKeys` is `"error" | "ignore" | "vocab"` or `{ "scope": "none" | "root" | "enclosing",
"otherwise": "error" | "ignore" | "vocab" }`; a string means scope `none`; default
`{ "scope": "none", "otherwise": "error" }`. `unmappedTypes` has the same shape for type values and
defaults to the `unmappedKeys` settings.

`propertyMap` and `typeMap` are either an inline map or a string naming an entry of
`namedPropertyMaps` / `namedTypeMaps`. Named maps may refer to one another and to themselves; the
expansion is bounded because the data is finite. Named maps are declared at the root only, like the
rules of a grammar.

A property definition is a string (the predicate IRI) or an object with: `iri`; `role`
(`identifier` | `type` | `base`); `template`; `baseTemplate`; `termType` (`iri` default |
`blankNode`); `datatype`; `language`, `direction`; `valueType: "identifier"`; `inverse`; `flatten`;
`keyedBy` (`identifier` | `language` | `type` | `{ property, valueProperty }`); `typeMap`;
`propertyMap`. A type definition is a class IRI or `{ "iri", "propertyMap" }`.

`role` semantics: `identifier`: the member's value, resolved against the enclosing base or expanded
through `template`, names the node. `type`: the member's value, through the governing type maps,
gives the node its classes. `base`: the member's value, resolved against the enclosing base, is the
base for the object's other members.

## Processing

1. A JSON object is a node governed by two maps: its *position map* (the `propertyMap` of the
   definition it appears under, or the root `propertyMap` for the root object) and its *type map*
   (the `propertyMap` of the type definition its type key's value selects, if any). A named map is in
   scope exactly as if written inline.
2. Identifier, base and type first. Identifier key present → its value (or template expansion),
   resolved against the enclosing base, names the node; else a fresh blank node (stable if
   `termType: "blankNode"` + `template`). A key with role `base`, or an identifier key with a `baseTemplate`,
   present → its value or expansion, resolved against the enclosing base, becomes the base for the
   object's *other* members; the identifier itself resolves against the enclosing base. A
   `baseTemplate` on a property (a definition with an `iri`) sets the base of that property's values. Type key present → its values,
   through the type maps, are the node's classes. More than one identifier key, or more than one
   base-setting key, in one object is an error; one key may be both (`"id": { "role": "identifier",
   "baseTemplate": "{}/" }`). Member order never matters.
3. Every other key is looked up in the type map, then the position map. `scope: none`: nothing else.
   `scope: root`: then the root `propertyMap` (global dictionary). `scope: enclosing`: then each
   enclosing property map, nearest first, then the root (lexical scoping, shadowing). Still unmapped →
   `otherwise`. Type values likewise in type maps under `unmappedTypes`. Never looked up: `keyedBy`
   entry keys (data), keys inside an `rdf:JSON` value, the reserved `propertyMap` / `mapping` members,
   keys whose values a template, a `from` reference or a group consumes.
4. Convert the value by kind under the definition found. Arrays → one sequence; dictionaries →
   repeated values; `flatten` on an object attaches its keys to the current node, on an array makes
   its elements root nodes; `inverse` swaps subject and object. Arrays under `inverse` and under the
   type role spread into one triple per element (the only two exceptions to arrays-are-sequences).
5. Root value: object → node; array → one node per element; scalar → nothing.

## Bases and templates

The base in force starts as the root `base`; an object inherits the base of its position unless one
of its keys sets a new one (role `base` or `baseTemplate`), which applies to its other members and
below. A property definition's own `baseTemplate` sets the base for that property's values. Templates
follow RFC 6570 simple string expansion with four references: `{}` the own value of the member whose
definition carries the template; `{key}` the value of the member named `key` in the object the
template describes; `{../key}` the enclosing object's member (arrays are transparent to `..`); `{#}`
the 1-based position in the enclosing array. Substituted values are percent-encoded as IRI components
(R2RML's IRI-safe rule); into blank node labels they go as they are. Relative expansions resolve
against the base in force (RFC 3986). A reference with no value → no term, no triple.

Leading example: with `"base": "https://example.org/people/"`, `"id": { "role": "identifier",
"baseTemplate": "{}/" }`, `"knows": { "iri": "schema:knows", "valueType": "identifier",
"baseTemplate": "friends.ttl", "template": "#{}" }` and data `{ "id": "alice", "knows": ["Bob",
"Eve"] }`, the output is `<https://example.org/people/alice> schema:knows
( <https://example.org/people/alice/friends.ttl#Bob> <https://example.org/people/alice/friends.ttl#Eve> ) .`
— one sequence, because `knows` is an array.

## Embedded form

Any data object may carry a `propertyMap` member (a map or a name): the position map of that object.
The root data object may instead carry a `mapping` member holding a complete mapping document: the
conventional root `@context`, separated into its parts. External and embedded mappings combine, the
embedded one being the nearer. The two member names are reserved; nothing else in the data is.

## Design decisions already taken (sanity-check these)

- `valueType: "identifier"` rather than `"iri"`: a value may identify a blank node (`termType`), and
  the word mirrors `role: "identifier"`.
- Default strictness: `{ "scope": "none", "otherwise": "error" }`; §11 of the document argues for
  `"otherwise": "ignore"` as the API-friendly default.
- `null` in an array leaves no element (positions shift); fractional numbers → `xsd:decimal`;
  `prefixes` root-only, `base` scoped; named maps root-only.
- Still proposed, not core (from RML): `{ "from": "key" }` as an alternative to constants for `iri`,
  `datatype`, `language`, `class`; `class` on definitions and the root (type by structure); `groups`
  for virtual properties built from sibling keys; `keyedBy: { "predicate": { "template": … } }`;
  `identifier` as an attribute of an object's definition (`role: "identifier"` on a key being its
  shorthand).

## Suggested shape of the jsonld.js prototype

- Add a `jsonldArray` option to `toRDF` (or a sibling `jsonld.arrayToRDF(data, mapping, options)`)
  that bypasses expansion and walks the JSON with the rules above, emitting RDF/JS quads whose
  objects may be `{ termType: "Sequence", elements: [...] }` terms (see rdf-array's
  rdf-data-factory-array for the term, `value` spelled `(e1 e2 …)`).
- Serialize sequences in the playground's N-Quads/Turtle output as `( … )`; the N3.js-array fork does
  this if swapped in, otherwise a small writer extension suffices.
- Reuse jsonld.js's IRI resolution (`prependBase`) for `base` handling, its RFC 3986 behaviour being
  what the document assumes; add percent-encoding of substituted template values.
- Error cases to surface in the playground: unmapped key/type under `otherwise: "error"`; two
  identifier keys; two base-setting keys; a literal under `inverse`; a named map that does not exist.
- A test set can be lifted straight from the document's tables (§5, §11.1): each row is JSON +
  mapping → Turtle-array.
