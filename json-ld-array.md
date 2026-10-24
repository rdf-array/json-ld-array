# JSON-LD-array: mapping conventional JSON to rdf-array

*Design sketch, 2026-10-23 (begun as a tutorial on 2026-10-21). Implemented in
[jsonld.js-array](https://github.com/rdf-array/jsonld.js-array) (`jsonld.arrayToRDF`, with a
[playground](https://rdf-array.github.io/jsonld.js-array/)), whose doc/rdf-array.md lists the
decisions the implementation added. This document is
[json-ld-array.md](https://github.com/rdf-array/rdf-array) in the organisation's meta-repository,
rendered at <https://rdf-array.github.io/rdf-array/json-ld-array.html>; [rdf-array.md](rdf-array.html)
there describes the change from RDF to rdf-array. The
names follow the rdf-array organisation: rdf-array is RDF whose data model has sequences as terms,
and Turtle-array, SPARQL-array, ShEx-array and JSON-LD-array are its syntaxes.*

JSON-LD-array is a mapping language that turns **conventional JSON** — the JSON an API already
produces — into **rdf-array**. It keeps the one idea of JSON-LD that conventional JSON needs, *a map
from JSON keys to RDF properties*, and drops the rest:

1. **No legacy simplifications.** A JSON-LD `@context` is one flat map in which prefixes, property
   terms, class terms, keyword aliases (`"id": "@id"`) and processing directives (`@vocab`, `@base`,
   `@language`, `@version`, `@protected`, …) share a namespace. JSON-LD-array gives each its own
   place: `prefixes`, `propertyMap`, `typeMap`, named maps and a few named directives.
2. **Only a transformation of conventional JSON.** The part of a document that produces RDF carries
   no directives: no `@id`, `@type` or blank node identifiers on nodes, no `@value` literal objects,
   no `@graph`, `@index` or framing. The mapping is kept apart from the data, in a document of its
   own or in reserved members (§4.3). Nodes are identified by an ordinary field that the mapping
   designates, or they are blank nodes. A graph that is not a tree still needs JSON-LD proper.
3. **No `@container: @list` or `@set`.** rdf-array has sequences, so a JSON array *is* a sequence
   term, nested arrays included, and `[]` is the empty sequence `()`. Turning a sequence into
   repeated properties (or back) is an rdf-array operation on any data, not a mapping concern (§2.1).
4. **One construct for property mappings**, `propertyMap`, written inline or referring by name to a
   map declared once at the root. At the root of the mapping it plays the role of the property
   definitions "sprinkled" through a conventional `@context`; inside a property definition or a type
   definition it says which keys may appear below, as a production in a grammar does (§4).

JSON-LD-array is to JSON-LD roughly what RML is to R2RML for JSON sources, but shaped like a context
rather than like a set of triples maps, and without JSONPath iterators: the tree structure of the
JSON *is* the iterator (§10, §11).

**Terminology.** A JSON object is a set of members, each a name/value pair ([RFC 8259 §4]). As in
JSON-LD 1.1 §1.4, an object is treated as an Infra map whose entries each have a key, the member's
name, and a value ([INFRA]). In this document "key" always means a member name in the data, and the
members of the mapping document are called attributes. A key is a plain string, compared code unit by
code unit ([RFC 8259 §8.3]) and never expanded as a compact IRI. "The identifier key", "the type key"
and the like name a key by the role its definition gives it; what names the node or gives its classes
is always that member's *value*.

## 1. One example end to end

The mapping, a document of its own, with the property maps written inline:

```json
{
  "prefixes": {
    "schema": "http://schema.org/",
    "ex":     "https://example.org/ns#",
    "xsd":    "http://www.w3.org/2001/XMLSchema#",
    "rdf":    "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs":   "http://www.w3.org/2000/01/rdf-schema#"
  },
  "base": "https://example.org/people/",
  "unmappedKeys": "error",
  "typeMap": { "Person": "schema:Person", "Organization": "schema:Organization" },
  "propertyMap": {
    "id":       { "role": "identifier", "baseTemplate": "{}/" },
    "type":     { "role": "type" },
    "name":     "schema:name",
    "age":      { "iri": "schema:age", "datatype": "xsd:integer" },
    "born":     { "iri": "schema:birthDate", "datatype": "xsd:date" },
    "homepage": { "iri": "schema:url", "valueType": "identifier" },
    "tags":     "ex:tags",
    "knows":    { "iri": "schema:knows", "valueType": "identifier",
                  "baseTemplate": "friends.ttl", "template": "#{}" },
    "address":  { "iri": "schema:address",
                  "propertyMap": { "city": "schema:addressLocality",
                                   "zip":  "schema:postalCode" } }
  }
}
```

The same mapping with the property maps declared once and referred to by name, as the productions of
a grammar are:

```json
{
  "prefixes": { "schema": "http://schema.org/", "ex": "https://example.org/ns#",
                "xsd": "http://www.w3.org/2001/XMLSchema#" },
  "base": "https://example.org/people/",
  "unmappedKeys": "error",
  "typeMap": { "Person": "schema:Person", "Organization": "schema:Organization" },
  "propertyMap": "rootMap",
  "namedPropertyMaps": {
    "rootMap": {
      "id":       { "role": "identifier", "baseTemplate": "{}/" },
      "type":     { "role": "type" },
      "name":     "schema:name",
      "age":      { "iri": "schema:age", "datatype": "xsd:integer" },
      "born":     { "iri": "schema:birthDate", "datatype": "xsd:date" },
      "homepage": { "iri": "schema:url", "valueType": "identifier" },
      "tags":     "ex:tags",
      "knows":    { "iri": "schema:knows", "valueType": "identifier",
                    "baseTemplate": "friends.ttl", "template": "#{}" },
      "address":  { "iri": "schema:address", "propertyMap": "addressMap" }
    },
    "addressMap": {
      "city": "schema:addressLocality",
      "zip":  "schema:postalCode"
    }
  }
}
```

The data, untouched API output:

```json
{ "id": "alice", "type": "Person", "name": "Alice", "age": 42,
  "born": "1984-02-29", "homepage": "https://alice.example/",
  "tags": ["rdf", "json"], "knows": ["Bob", "Eve"],
  "address": { "city": "Paris", "zip": "75001" } }
```

The result, in Turtle-array:

```turtle
<https://example.org/people/alice> a schema:Person ;
    schema:name "Alice" ; schema:age 42 ; schema:birthDate "1984-02-29"^^xsd:date ;
    schema:url <https://alice.example/> ;
    ex:tags ( "rdf" "json" ) ;
    schema:knows ( <https://example.org/people/alice/friends.ttl#Bob>
                   <https://example.org/people/alice/friends.ttl#Eve> ) ;
    schema:address [ schema:addressLocality "Paris" ; schema:postalCode "75001" ] .
```

Two things to notice. The `id` member does two jobs: its value `alice`, resolved against the base
in force, `https://example.org/people/`, names the node, and through `"baseTemplate": "{}/"` it
makes `https://example.org/people/alice/` the base for the object's other members. The `knows`
definition then sets `friends.ttl`, resolved against that base, as the base for its values, and the
template `#{}` makes each value a fragment of it. And `knows` is an array, so it is one sequence
term; an application that wants two `schema:knows` triples instead spreads it afterwards (§2.1).

## 2. The data model that keeps it simple

Every JSON value kind has one rdf-array reading; the mapping only refines it.

| JSON value | rdf-array term or triples | Refined by |
|---|---|---|
| object | a **node**: a fresh blank node, or the node that its identifier key's value names | `role`, `template`, `termType`, `flatten`, `keyedBy` |
| array | one **sequence term** holding the converted elements, in order; `[]` is `()` | the element conversion is the property's own |
| object declared `keyedBy` | a **dictionary**: one value of the property per entry, unordered | `keyedBy` |
| string | a plain literal; or an identifier of a node (an IRI, or a blank node); or a datatyped or language-tagged literal | `datatype`, `language`, `direction`, `valueType`, `template`, `termType`, `role` |
| number | `xsd:integer` when it has no fraction or exponent, otherwise `xsd:decimal` | `datatype` (for instance `xsd:double`) |
| `true` / `false` | `xsd:boolean` | — |
| `null` | nothing: no triple, and no element in a sequence | — |

The one principle behind arrays and dictionaries: **JSON arrays are ordered, so they become
sequences; JSON objects are unordered (RFC 8259), so an object used as a dictionary becomes repeated
properties.** Nothing in the mapping chooses between list and set; the JSON already did.

### 2.1 Spreading is orthogonal

Whether `schema:knows ( <…#Bob> <…#Eve> )` or `schema:knows <…#Bob>, <…#Eve>` is wanted is a
question about the RDF, not about the JSON, so JSON-LD-array does not answer it. In SPARQL-array a
sequence is spread with a position pattern, over any data however it was produced:

```sparql
DELETE { ?s schema:knows ?seq }
INSERT { ?s schema:knows ?friend }
WHERE  { ?s schema:knows ?seq . ?s schema:knows ((?friend))[*] }
```

and gathered back with an aggregate into a sequence. JSON-LD needed `@container: @list` and
`@container: @set` because RDF 1.1 had no sequence term to leave the choice to.

## 3. The mapping document

### 3.1 Top level

| Attribute | Value | Meaning |
|---|---|---|
| `prefixes` | `{ "schema": "http://schema.org/", … }` | Prefixes usable **in the mapping only**, in every `iri`, `datatype`, `class` and `typeMap` value. Root only. Data keys are never compact IRIs. |
| `base` | an IRI | The base in force at the root. Below the root the base is lexically scoped: a key with role `base` or with a `baseTemplate` establishes a new one for its object (§3.5). |
| `vocab` | an IRI | The prefix for unmapped keys under `"otherwise": "vocab"`. |
| `unmappedKeys` | `"error"`, `"ignore"`, `"vocab"`, or `{ "scope": "none" / "root" / "enclosing", "otherwise": "error" / "ignore" / "vocab" }` | How far a key is looked up beyond the maps that govern its object, and what happens to a key that is still unmapped (§3.4, rule 3). A string means `{ "scope": "none", "otherwise": that }`; the default is `{ "scope": "none", "otherwise": "error" }`. |
| `unmappedTypes` | the same shape | The same for a value of a `role: "type"` key that has no entry in the governing type maps. Defaults to the `unmappedKeys` settings. |
| `typeMap` | a map `{ "Person": "schema:Person", "Circle": { "iri": "ex:Circle", "propertyMap": … } }`, or the name of an entry of `namedTypeMaps` | Classes for the values of `role: "type"` keys. |
| `propertyMap` | a map `{ key: definition, … }`, or the name of an entry of `namedPropertyMaps` | The property definitions governing the root object. |
| `namedPropertyMaps`, `namedTypeMaps` | `{ name: map, … }` | Maps declared once and referred to by name from any `propertyMap` or `typeMap` attribute, from one another and from themselves. Root only (§4.1). |
| `groups` | proposed, §11 | Virtual properties built from several sibling keys. |

### 3.2 A property definition

The value of a key in a `propertyMap` is either a string, the property IRI, or an object:

| Attribute | Value | Meaning |
|---|---|---|
| `iri` | an IRI or prefixed name | The predicate. Required unless the role is `identifier`, `type` or `base`, or `flatten` is set. |
| `role` | `"identifier"`, `"type"`, `"base"` | `identifier`: the member's value, resolved against the enclosing base or expanded through `template`, names the node. `type`: the member's value, through the in-scope type maps, gives the node its classes. `base`: the member's value, resolved against the enclosing base, is the base for the object's other members. A role key that also has an `iri` maps its value as a literal as well. |
| `template` | a template (§3.5), such as `"https://example.org/people/{}"` | For an identifier, whether a `role: "identifier"` key or a `valueType: "identifier"` value: the expansion, resolved against the base in force, is the IRI, or under `termType: "blankNode"` the blank node's label. `{}` is the member's own value. |
| `baseTemplate` | a template | On a key with role `identifier` or `base`: the expansion, resolved against the enclosing base, is the base for the object's other members; `{}` is this member's value. On a property, a definition with an `iri`: the base for that property's values, expanded over the members of the object the property belongs to. |
| `termType` | `"iri"` (default), `"blankNode"` | What kind of identifier a `role: "identifier"` key or a `valueType: "identifier"` value produces. A blank node labelled by a template expansion is the same node wherever that label recurs in the document. |
| `datatype` | a datatype IRI | For strings and numbers: the literal's datatype, and for numbers the lexical form (`xsd:decimal` keeps `1.50`, `xsd:double` gives `1.5E0`). `rdf:JSON` keeps the whole value as a JSON literal. |
| `language`, `direction` | a BCP 47 tag, `"ltr"` / `"rtl"` | For strings: a language-tagged literal. |
| `valueType` | `"identifier"` | String values identify nodes instead of being literals: IRIs resolved against the base in force (JSON-LD's `@type: @id`) or expanded through `template`, blank nodes under `termType: "blankNode"`. |
| `inverse` | `true` | The value is the subject and the current node the object (JSON-LD's `@reverse`); an array is spread, one triple per element. |
| `flatten` | `true` | An object value is not a node: its keys are mapped as keys of the current node (JSON-LD's `@nest`). An array value is an envelope: its elements are root nodes. |
| `keyedBy` | `"identifier"`, `"language"`, `"type"`, `{ "property": iri, "valueProperty": iri }` | The value object is a dictionary (§5.4). |
| `typeMap` | a map or a name | Classes for `role: "type"` keys within this property's values. |
| `propertyMap` | a map or a name | Definitions for the keys of this property's values (§4). |

### 3.3 A type definition

A `typeMap` entry is a string, the class IRI, or `{ "iri": …, "propertyMap": … }`: a map, inline or
by name, for the keys of a node declared with that type.

### 3.4 Processing, in five rules

1. **A JSON object is a node, and two maps govern it.** Its *position map* is the `propertyMap` of
   the definition under which the object appears, or the root `propertyMap` for the root object; its
   *type map* is the `propertyMap` of the type definition its type key's value selects, if there is
   one. A map referred to by name is in scope exactly as if written inline.
2. **Identifier, base and type come first.** If a key with role `identifier` is in scope and
   present, its value, resolved against the enclosing base or expanded through its `template`, names
   the node; otherwise the node is a fresh blank node (or, with `termType: "blankNode"` and a
   `template`, a stable one). If a key with role `base`, or an identifier key with a `baseTemplate`, is in
   scope and present, its value or the template's expansion, resolved against the enclosing base, is
   the base for the object's other members; the identifier itself resolves against the enclosing
   base. If a
   key with role `type` is in scope and present, its values, through the governing type maps, are
   the node's classes. More than one identifier key, or more than one base-setting key, present in
   one object is an error; one key may be both, as `id` is in §1. These keys are read before the
   others, so member order never matters (JSON-LD has the same look-ahead for `@type`).
3. **Every other key is looked up** in the governing maps, type map first, then position map. Under
   `"scope": "none"` nothing else is in scope. Under `"scope": "root"` a key not found there is
   looked up in the root `propertyMap`, so the root maps serve as a global dictionary. Under
   `"scope": "enclosing"` it is looked up in each enclosing property map, nearest first, and then in
   the root map: lexical scoping with shadowing. A key still unmapped follows `otherwise`: an error,
   nothing, or the property `vocab` + key. The values of a type key are looked up the same way in the
   type maps, under `unmappedTypes`. Not looked up, and never unmapped, are the entry keys of a
   `keyedBy` dictionary, which are data; the keys inside a value whose datatype is `rdf:JSON`; the
   reserved `propertyMap` and `mapping` members of the embedded form (§4.3); and the keys whose values
   a template, a `from` reference or a group consumes (§3.5, §11).
4. **The value is converted** by its JSON kind (§2) under the definition found. Arrays convert element
   by element into one sequence; dictionaries convert entry by entry into repeated values; `flatten`
   attaches an object's keys to the current node or makes an array's elements root nodes; `inverse`
   swaps subject and object. Arrays under `inverse` and under the type role spread into one triple per
   element instead of forming a sequence.
5. **The root value** is a node if it is an object, one node per element if it is an array (there is
   no subject for a root sequence to hang from), and nothing if it is a scalar.

### 3.5 Bases and templates

The **base in force** starts as the root `base`. Each object inherits the base of the position it
appears in, unless one of its keys sets a new one, by `role: "base"` or by a `baseTemplate`; that base
applies to the object's other members and to everything below them. A property definition's own
`baseTemplate` sets the base for that property's values, so a key such as `knows` in §1 can place
its values in a document of their own. An object's identifier always resolves against the enclosing
base, and the base the object sets applies to its contents, as a web page's URL and the base its
links resolve against are two different things.

A **template** is a string with references in braces, after RFC 6570's simple string expansion:

| Reference | Value |
|---|---|
| `{}` | the own value of the member whose definition carries the template |
| `{key}` | the value of the member named `key` in the object the template describes (the object itself for `identifier` and `baseTemplate` on a property definition; the member's siblings for a template on a key) |
| `{../key}` | the value of the member named `key` in the enclosing object; an array is transparent to `..` |
| `{#}` | the 1-based position of the element in the array that holds it, as SPARQL-array's position patterns count |

A substituted value is percent-encoded as an IRI component, R2RML's IRI-safe rule, so a value holding
`/` cannot step out of its path segment; a value substituted into a blank node label is taken as it
is. A relative expansion is resolved against the base in force (RFC 3986). A template whose reference
has no value produces no term, and so no triple. A member whose value is only consumed by a template
needs no definition of its own.

### 3.6 Output

Processing yields rdf-array triples, all in the default graph. Their terms are IRIs, blank nodes,
literals and sequences; a sequence holds the converted elements of one JSON array, in order.

- **In an API**, a sequence is the term of the host's rdf-array data model. In the RDF/JS data model
  of the rdf-array forks (types-array, rdf-data-factory-array) it is
  `{ termType: "Sequence", elements: [ …terms… ], value }`, where `value` is the N-Triples-style
  spelling `(e1 e2 …)` and `DataFactory.sequence(elements)` makes one; jena-array's is `Node_Seq`,
  rdflib-array's `rdflib.term.Sequence`.
- **As text**, the output is N-Quads-array or Turtle-array: a sequence is written `( e1 e2 … )`,
  nested freely, `()` when empty.
- **Blank node labels.** A fresh blank node's label is the processor's choice. A stable one,
  from `termType: "blankNode"` and a template, is labelled with the expansion; a mapping whose
  expansions use characters outside those N-Triples allows in a blank node label produces output
  that a writer must relabel.
- **Numbers.** The lexical form of a literal from a JSON number is the number as written in the
  JSON text (`1.70` stays `1.70` in an `xsd:decimal`) when the processor's JSON parser exposes it,
  and otherwise the shortest spelling of the parsed number; an exponent is expanded for
  `xsd:decimal`, and `xsd:double` takes JSON-LD's canonical form (`1.5E0`).
- **IRIs** are resolved against the base in force by RFC 3986 §5.2, after template values have been
  percent-encoded (§3.5).

### 3.7 Errors

A processor stops at the first error and reports it with its *path*, the keys and array indices
from the data root to the offending value (`/address/street`, `/phones/1/number`). Errors in the
mapping document are reported before any data is read, except a reference to an undeclared named
map, which is reported where it is first used. The codes are those of the reference
implementation (§12).

| Condition | Code |
|---|---|
| the mapping is not an object; an attribute has the wrong type; a definition has an unknown attribute, a `role` other than `identifier`, `type` or `base`, a `valueType` other than `identifier`, a `termType` other than `iri` or `blankNode`, an unknown `keyedBy`, a `template` on a non-identifier role, or neither `iri`, `role`, `flatten` nor a `keyedBy` predicate; `unmappedKeys` or `unmappedTypes` has an unknown `scope` or `otherwise` | `invalid mapping` |
| a `propertyMap` or `typeMap` names a map that `namedPropertyMaps` or `namedTypeMaps` does not declare | `unknown named map` |
| a key is unmapped and `otherwise` is `error` | `unmapped key` |
| a type value has no entry in the governing type maps and `unmappedTypes` says `error` | `unmapped type` |
| `otherwise` is `vocab` but the mapping has no `vocab` | `no vocab` |
| more than one identifier key present in one object | `two identifiers` |
| more than one base-setting key present in one object | `two bases` |
| an identifier value that is an object or an array; a type value that is not a string | `invalid identifier`, `invalid type value` |
| a literal value under `inverse` (a literal cannot be a subject) | `literal subject` |
| a value that its datatype cannot hold (a fraction as `xsd:integer`); a language tag on a non-string | `invalid literal` |
| `flatten` on a value that is neither an object nor an array | `invalid flatten` |
| `keyedBy` on a value that is not an object, or a dictionary entry of the wrong kind (a non-object under `identifier` or `type`, a non-string under `language`) | `invalid dictionary` |
| a `from` reference to a member whose value is not a string, where a string is needed (an `iri`, a `datatype`, a `language`) | `invalid from`, `invalid predicate` |

## 4. Scopes: where a `propertyMap` can appear and what it reaches

| Where | What its definitions apply to | JSON-LD 1.1 counterpart |
|---|---|---|
| the mapping root | the root object's keys, and under `"scope": "root"` or `"enclosing"` every key not mapped deeper | the term definitions of the root `@context` |
| inside a property definition (**property-scoped**), inline or by name | the keys of that property's value objects; under `"scope": "enclosing"` also everything nested below, until shadowed | a property-scoped context, which propagates |
| inside a `typeMap` entry (**type-scoped**), inline or by name | the keys of a node declared with that type, this node only | a type-scoped context, which does not propagate |
| embedded in a data object as its `propertyMap` member (§4.3) | that object's keys, as its position map | an embedded `@context` in a node object; at the document root, the conventional root `@context` |

### 4.1 Grammar first, scoping on request

A map defines the keys allowed at the position it governs, as a production in a yacc grammar defines
what may appear at that point. A map referred to by name is in scope exactly as if its definitions
were written inline at the reference: `"propertyMap": "addressMap"` and the inline object are the same
mapping, and `namedPropertyMaps` is the grammar's table of productions. Maps may refer to one another
and to themselves, so a recursive JSON shape (comments within comments) is a recursive map; the
expansion is bounded because the data is finite: recursion could only be unbounded if a document
implied a reference to another document, and eventually to itself, which JSON-LD-array does not do.
Named maps are declared at the root only, as grammar rules are: a name then means one thing wherever
it is used, and no second scoping question arises about where a name is visible. Nothing prevents
relaxing this later; nothing seems to call for it.

By default (`"scope": "none"`) a key must be in one of the two maps that govern its object, which is
the strict, grammar-like reading. Two relaxations widen the lookup for mappings meant as dictionaries
rather than grammars: `"scope": "root"` makes the root `propertyMap` and `typeMap` global, so a key
unknown to the local map falls back to them; `"scope": "enclosing"` makes every enclosing property
map visible, nearest first, with an inner definition **shadowing** an outer one for the same key —
ordinary lexical scoping, as XML namespaces behave, where an `xmlns` declaration on any element is in
scope for its descendants and one on the root for the document. JSON-LD 1.1's property-scoped
contexts behave like `"enclosing"`, its type-scoped contexts like a type map under `"none"`; its
`@propagate` flag and "previous context" bookkeeping are what the two fixed rules replace.

### 4.2 Which constructs may appear where

| Construct | mapping root | property-scoped | type-scoped | embedded in data |
|---|---|---|---|---|
| `prefixes`, `vocab`, `unmappedKeys`, `unmappedTypes`, `namedPropertyMaps`, `namedTypeMaps` | yes | no | no | in `mapping` at the data root |
| `base` | yes | through `role: "base"` and `baseTemplate` | through `role: "base"` and `baseTemplate` | in `mapping` at the data root |
| `typeMap` | yes | yes | no | in `mapping` at the data root |
| `propertyMap` | yes | yes | yes | yes, any object |
| `role: identifier` / `type` / `base` keys | yes | yes | yes | yes |
| `template`, `baseTemplate`, `termType`, `datatype`, `language`, `direction`, `valueType`, `inverse`, `flatten`, `keyedBy` | in any property definition | in any property definition | in any property definition | in any property definition |

### 4.3 The embedded form

Goal 2 is about the part of a document that produces RDF: it carries no directives. The mapping
itself may travel with the data, as a conventional JSON-LD document carries its `@context`, through
two reserved members. Any data object may contain a `propertyMap` member, a map or a name, which is
the position map of that object (and under `"scope": "enclosing"` is in scope below it). The root
data object may instead contain a `mapping` member holding a complete mapping document, with its
`prefixes`, `base`, directives, named maps and root `propertyMap`; that is the conventional root
`@context`, separated into its parts. An external mapping and embedded members may be combined, the
embedded one being the nearer. The price of not using `@` is that a data member named `propertyMap`
(anywhere) or `mapping` (at the root) cannot be data; JSON-LD paid the same price with a different
coin, every key beginning with `@`.

## 5. JSON to Turtle-array, by example

All rows assume the prefixes of §1 and `"base": "https://example.org/people/"`. The subject `[]`
stands for the blank node of the enclosing object.

### 5.1 Literals

| JSON | property definition | Turtle-array |
|---|---|---|
| `{ "name": "Alice" }` | `"name": "schema:name"` | `[] schema:name "Alice" .` |
| `{ "age": 42 }` | `"age": "schema:age"` | `[] schema:age 42 .` (`xsd:integer`) |
| `{ "height": 1.70 }` | `"height": "schema:height"` | `[] schema:height 1.70 .` (`xsd:decimal`; JSON-LD gives `"1.7E0"^^xsd:double`) |
| `{ "score": 0.5 }` | `"score": { "iri": "ex:score", "datatype": "xsd:double" }` | `[] ex:score 0.5e0 .` |
| `{ "active": true }` | `"active": "ex:active"` | `[] ex:active true .` |
| `{ "born": "1984-02-29" }` | `"born": { "iri": "schema:birthDate", "datatype": "xsd:date" }` | `[] schema:birthDate "1984-02-29"^^xsd:date .` |
| `{ "title": "Bonjour" }` | `"title": { "iri": "schema:name", "language": "fr" }` | `[] schema:name "Bonjour"@fr .` |
| `{ "nickname": null }` | `"nickname": "ex:nickname"` | nothing |
| `{ "raw": { "a": [1, 2] } }` | `"raw": { "iri": "ex:raw", "datatype": "rdf:JSON" }` | `[] ex:raw """{"a":[1,2]}"""^^rdf:JSON .` |

### 5.2 Nodes, identifiers and bases

| JSON | property definition | Turtle-array |
|---|---|---|
| `{ "address": { "city": "Paris" } }` | `"address": { "iri": "schema:address", "propertyMap": { "city": "schema:addressLocality" } }` | `[] schema:address [ schema:addressLocality "Paris" ] .` |
| `{ "id": "alice", "name": "Alice" }` | `"id": { "role": "identifier" }` | `<https://example.org/people/alice> schema:name "Alice" .` |
| `{ "id": 42, "name": "Bob" }` | `"id": { "role": "identifier", "template": "https://example.org/people/{}" }` | `<https://example.org/people/42> schema:name "Bob" .` |
| `{ "homepage": "https://alice.example/" }` | `"homepage": { "iri": "schema:url", "valueType": "identifier" }` | `[] schema:url <https://alice.example/> .` |
| `{ "editorId": 5 }` | `"editorId": { "iri": "schema:editor", "valueType": "identifier", "template": "https://example.org/people/{}" }` | `[] schema:editor <https://example.org/people/5> .` |
| `{ "id": "alice", "knows": ["Bob", "Eve"] }` | `"id": { "role": "identifier", "baseTemplate": "{}/" }`, `"knows": { "iri": "schema:knows", "valueType": "identifier", "baseTemplate": "friends.ttl", "template": "#{}" }` | `<…/people/alice> schema:knows ( <…/people/alice/friends.ttl#Bob> <…/people/alice/friends.ttl#Eve> ) .` |
| `{ "id": "alice", "docs": { "base": "https://docs.example/alice/", "main": "cv.html" } }` | `"docs": { "iri": "ex:docs", "propertyMap": { "base": { "role": "base" }, "main": { "iri": "ex:main", "valueType": "identifier" } } }` | `<…/people/alice> ex:docs [ ex:main <https://docs.example/alice/cv.html> ] .` |
| `{ "id": "alice", "alt": "x", "ref": "y" }` | `"alt": { "role": "identifier" }` as well | error: two identifier keys in one object |
| `{ "type": "Person" }` | `"type": { "role": "type" }` with `"typeMap": { "Person": "schema:Person" }` | `[] a schema:Person .` |
| `{ "type": ["Person", "Organization"] }` | same | `[] a schema:Person, schema:Organization .` (like `inverse`, the type role spreads an array: a node has classes, not a sequence of them) |
| `{ "attributes": { "name": "Alice" } }` | `"attributes": { "flatten": true }` | `[] schema:name "Alice" .` |
| `{ "data": [ { "name": "A" }, { "name": "B" } ], "meta": { "page": 1 } }` | `"data": { "flatten": true }`, `"meta"` unmapped under `"otherwise": "ignore"` | `[] schema:name "A" . [] schema:name "B" .` as two root nodes |
| `{ "children": [ { "name": "C1" }, { "name": "C2" } ] }` | `"children": { "iri": "ex:parent", "inverse": true, "propertyMap": { "name": "schema:name" } }` | `_:c1 ex:parent [] . _:c2 ex:parent [] .` with `_:c1 schema:name "C1"` etc. |

### 5.3 Arrays are sequences

| JSON | property definition | Turtle-array |
|---|---|---|
| `{ "tags": ["rdf", "json"] }` | `"tags": "ex:tags"` | `[] ex:tags ( "rdf" "json" ) .` |
| `{ "tags": [] }` | same | `[] ex:tags () .` (JSON-LD: no triple at all, or `rdf:nil` under `@list`) |
| `{ "tags": ["rdf"] }` | same | `[] ex:tags ( "rdf" ) .` (a one-element sequence is not the element) |
| `{ "matrix": [[1, 2], [3, 4]] }` | `"matrix": "ex:matrix"` | `[] ex:matrix ( (1 2) (3 4) ) .` (JSON-LD 1.0: "list of lists" error) |
| `{ "members": [ { "name": "A" }, { "name": "B" } ] }` | `"members": { "iri": "ex:members", "propertyMap": { "name": "schema:name" } }` | `[] ex:members ( [ schema:name "A" ] [ schema:name "B" ] ) .` |
| `{ "codes": ["A1", "B2"] }` | `"codes": { "iri": "ex:code", "valueType": "identifier" }` | `[] ex:code ( <https://example.org/people/A1> <https://example.org/people/B2> ) .` |
| `{ "names": ["Dog", "Hund"] }` | `"names": { "iri": "rdfs:label", "language": "en" }` | `[] rdfs:label ( "Dog"@en "Hund"@en ) .` (one language per property; a dictionary gives one per value, §5.4) |
| `{ "mixed": ["a", 1, null, { "x": 1 }] }` | `"mixed": { "iri": "ex:mixed", "propertyMap": { "x": "ex:x" } }` | `[] ex:mixed ( "a" 1 [ ex:x 1 ] ) .` (the `null` leaves no element; see §8) |

### 5.4 Dictionaries are repeated properties

| JSON | property definition | Turtle-array |
|---|---|---|
| `{ "people": { "alice": { "name": "Alice" }, "bob": { "name": "Bob" } } }` | `"people": { "iri": "ex:people", "keyedBy": "identifier", "propertyMap": { "name": "schema:name" } }` | `[] ex:people <…/alice>, <…/bob> . <…/alice> schema:name "Alice" . <…/bob> schema:name "Bob" .` |
| `{ "label": { "en": "Dog", "de": "Hund" } }` | `"label": { "iri": "rdfs:label", "keyedBy": "language" }` | `[] rdfs:label "Dog"@en, "Hund"@de .` |
| `{ "prices": { "EUR": 10, "USD": 11 } }` | `"prices": { "iri": "ex:price", "keyedBy": { "property": "ex:currency", "valueProperty": "rdf:value" } }` | `[] ex:price [ ex:currency "EUR" ; rdf:value 10 ], [ ex:currency "USD" ; rdf:value 11 ] .` |
| `{ "parts": { "Wheel": { "n": 4 }, "Seat": { "n": 2 } } }` | `"parts": { "iri": "ex:part", "keyedBy": "type", "typeMap": { "Wheel": "ex:Wheel", "Seat": "ex:Seat" }, "propertyMap": { "n": "ex:n" } }` | `[] ex:part [ a ex:Wheel ; ex:n 4 ], [ a ex:Seat ; ex:n 2 ] .` |

Entry order is not preserved, by design: JSON objects are unordered. Data whose dictionary order
matters belongs in an array of objects with the key as a field.

### 5.5 Scopes

| JSON | mapping | Turtle-array |
|---|---|---|
| `{ "geo": { "lat": 48.8, "long": 2.3 } }` | `"geo": { "iri": "schema:geo", "propertyMap": { "lat": "schema:latitude", "long": "schema:longitude" } }` | `[] schema:geo [ schema:latitude 48.8 ; schema:longitude 2.3 ] .` |
| `{ "lat": 48.8 }` | same mapping, `lat` at the root | error: `lat` is not in the root map, whatever the scope setting |
| `{ "org": { "name": "ACME", "city": "Lyon" } }` | root `"name": "schema:name"`, `"city": "schema:addressLocality"`; `"org": { "iri": "schema:worksFor", "propertyMap": { "name": "schema:legalName" } }`, default scope | error on `city`: under `"scope": "none"` only `org`'s map governs its value |
| same | same with `"unmappedKeys": { "scope": "root" }` or `"enclosing"` | `[] schema:worksFor [ schema:legalName "ACME" ; schema:addressLocality "Lyon" ] .` (`name` shadowed by `org`'s map, `city` found at the root) |
| `{ "address": { "city": "Paris" } }` | `"address": { "iri": "schema:address", "propertyMap": "addressMap" }` with `"namedPropertyMaps": { "addressMap": { "city": "schema:addressLocality" } }` | `[] schema:address [ schema:addressLocality "Paris" ] .` (the same as the inline map) |
| `{ "text": "root", "replies": [ { "text": "child", "replies": [ { "text": "grandchild", "replies": [] } ] } ] }` | `"propertyMap": "comment"`, `"namedPropertyMaps": { "comment": { "text": "ex:text", "replies": { "iri": "ex:replies", "propertyMap": "comment" } } }` | `[] ex:text "root" ; ex:replies ( [ ex:text "child" ; ex:replies ( [ ex:text "grandchild" ; ex:replies () ] ) ] ) .` (a recursive map, bounded by the data) |
| `{ "shapes": [ { "type": "Circle", "r": 1 }, { "type": "Square", "s": 2 } ] }` | `"shapes": { "iri": "ex:shapes", "propertyMap": { "type": { "role": "type" } }, "typeMap": { "Circle": { "iri": "ex:Circle", "propertyMap": { "r": "ex:radius" } }, "Square": { "iri": "ex:Square", "propertyMap": { "s": "ex:side" } } } }` | `[] ex:shapes ( [ a ex:Circle ; ex:radius 1 ] [ a ex:Square ; ex:side 2 ] ) .` |
| `{ "type": "Circle", "inner": { "r": 1 } }` | the same type definitions in the root `typeMap`, `"type": { "role": "type" }` and `"inner": "ex:inner"` at the root | error on `r`: a type map covers its node only, not `inner` |
| `{ "propertyMap": { "n": "https://example.org/ns#n" }, "n": 1 }` | embedded form, no mapping document | `[] ex:n 1 .` |
| `{ "mapping": { "prefixes": { "ex": "https://example.org/ns#" }, "propertyMap": { "n": "ex:n" } }, "n": 1 }` | embedded form with a complete mapping at the root | `[] ex:n 1 .` |

## 6. What JSON-LD's keywords become

| JSON-LD 1.1 | JSON-LD-array |
|---|---|
| `@context` (inline, remote, `@import`ed, `@version`ed, `@protected`) | one local mapping document; or the embedded `mapping` and `propertyMap` members |
| prefix terms (`"schema": "http://schema.org/"`) | `prefixes`, usable in the mapping only |
| property terms | `propertyMap` entries, inline or in `namedPropertyMaps` |
| class terms | `typeMap`, inline or in `namedTypeMaps` |
| keyword aliases (`"id": "@id"`, `"type": "@type"`) | `role: "identifier"`, `role: "type"` |
| `@vocab` | `"otherwise": "vocab"` with `vocab` |
| `@base` | `base` at the root; `role: "base"` and `baseTemplate` below it |
| `@type: @id`, `@type: @vocab` on a term | `valueType: "identifier"`, with `template` and `termType` |
| `@type: xsd:…` on a term | `datatype` |
| `@language`, `@direction` on a term | `language`, `direction` |
| default `@language` in a context | none: language is declared per property |
| `@container: @list` | nothing: arrays are sequences |
| `@container: @set` | nothing: dictionaries are repeated properties; spreading is an rdf-array operation |
| `@container: @index` + `@index` property, `@id`, `@language`, `@type` | `keyedBy` |
| `@nest` | `flatten: true` |
| `@reverse` | `inverse: true` |
| property-scoped `@context` | `propertyMap` in a property definition |
| type-scoped `@context` | `propertyMap` in a `typeMap` entry |
| `@propagate` | `unmappedKeys.scope` (§4.1) |
| `@id` templates (never standardized) | `template` |
| `@json` | `datatype: rdf:JSON` |
| `@graph`, `@included`, `@value` objects, `@index` values, blank node identifiers, `@embed` / framing | out of scope: not conventional JSON |

## 7. The corners JSON-LD painted itself into, and how JSON-LD-array stays out of them

| JSON-LD corner | What went wrong | JSON-LD-array |
|---|---|---|
| One flat `@context` for prefixes, properties, classes, aliases and directives | Any term could also act as a prefix in 1.0, so `"name": "x"` made `"name:foo"` a compact IRI; 1.1 had to restrict prefixes to terms whose IRI ends in a gen-delim character or that say `"@prefix": true`. | Separate maps. Prefixes are a mapping-side convenience; data keys are plain strings looked up whole. |
| `@type` does double duty | The node's class (`"@type": "Person"`) and a value's coercion (`"@type": "@id"`, a datatype) share a keyword; `@type: @id` resolved against `@base` when people wanted `@vocab`, so 1.1 added `@type: @vocab`. | `role: "type"` for the class, `datatype` and `valueType` for the value. |
| Arrays are unordered unless declared | A JSON array is a set unless its term says `@container: @list`; `[]` yields no triple (`rdf:nil` only under `@list`); 1.0 forbade lists of lists outright. | Arrays are sequences, `[]` is `()`, nesting is free, nothing is declared. |
| Native numbers | A non-integer becomes `xsd:double` in the canonical form `1.5E0`; a term typed `xsd:decimal` still gets that form, an invalid decimal; JavaScript processors lose integers beyond 2⁵³. | The datatype decides the lexical form; fractions default to `xsd:decimal`, and a parser that keeps the JSON lexical form keeps `1.70`. |
| Three meanings of `null` | A `null` value is dropped, `"term": null` undefines a term, `"@context": null` resets the active context. | `null` drops a value; there is nothing to undefine or reset. |
| Unmapped keys | Silently dropped without `@vocab`; with `@vocab` every key, typos included, becomes a property. | `unmappedKeys`, default `"error"`, and a scope setting that says how far a key may be looked up. |
| Identifying nodes from conventional JSON | Only through the `"id": "@id"` alias, and only when the field is already an IRI or a relative reference: a numeric id or a composed IRI cannot be expressed (IRI templates were requested and declined), and `@base` can only be changed by a new context. | `role: "identifier"`, `template`, and a base that any object can set with `role: "base"` or `baseTemplate`. |
| `@reverse` | Values must be nodes, lists are forbidden, and reverse terms cannot carry most other mappings. | `inverse: true` spreads arrays into one triple per element; a literal value is an error, as it must be. |
| Scoped contexts (1.1) | Property-scoped contexts propagate, type-scoped ones do not, `@propagate` overrides either, and processors keep a "previous context" to revert to; it is the hardest part of the 1.1 algorithms. | Maps govern positions; `unmappedKeys.scope` chooses none, root or enclosing fallback, once for the whole mapping. |
| Remote contexts | Fetched over HTTP at processing time, hence caching, outages, link headers, `@import`, `@protected` against redefinition by a later context, `@version` negotiation. | One local document, nothing fetched or merged; named maps replace the reuse that `@import` gave. |
| Default `@language` | Applies to every untyped string, identifiers and codes included, unless each term opts out with `"@language": null`. | Language is declared where it belongs, on the property. |
| Compaction and framing | Going from RDF back to the JSON shape an application expects needed framing, which 1.0 left unstandardized. | JSON-LD-array maps trees; the inverse mapping is well defined for a tree-shaped graph (a sequence is an array, repeated values of a `keyedBy` property are a dictionary) and out of scope for anything else. |
| Blank node predicates, `@index`, `@included`, generalized RDF | Added to round-trip arbitrary RDF through JSON. | Not expressible: JSON-LD-array is for conventional JSON only. |

## 8. Decisions to confirm

- **`null` inside an array** leaves no element, which shifts the positions after it. The
  alternative is an explicit placeholder term; rdf-array has none today.
- **Fractional numbers default to `xsd:decimal`**, not JSON-LD's `xsd:double`; `datatype` gives
  the double back.
- **An inverse property and the type role spread an array** instead of making a sequence the
  subject or the class. Every other array is a sequence, `knows` in §1 included: a mapping that wants
  repeated `schema:knows` triples spreads them afterwards (§2.1).
- **`valueType: "identifier"`, not `"iri"`.** A value that identifies a node may name a blank node
  as well as an IRI once `termType: "blankNode"` exists, so "iri" would be a misnomer; "identifier"
  also mirrors `role: "identifier"`: the role says the value identifies *this* node, the value type
  says it identifies *another*.
- **Strict by default.** `unmappedKeys` defaults to `{ "scope": "none", "otherwise": "error" }`,
  the grammar reading; §11 argues for `"otherwise": "ignore"` as the friendlier default for data from
  APIs that grow.
- **Named maps are root-only**, like the rules of a grammar (§4.1).
- **`prefixes` are root-only**, so a prefixed name means the same thing everywhere in the mapping;
  `base` is lexically scoped (§3.5).
- **The embedded form** reserves two member names in the data, `propertyMap` and `mapping`.
- **Templates** take any member of the object they describe, the enclosing object's members and the
  position; composing an identifier from the values of a *different* object still needs the
  structure of the JSON to put them in reach.

## 9. Names for these things

**A context inside a property definition.** JSON-LD 1.1 calls it a *scoped context*: a
*property-scoped context* when it sits in a term definition and applies to that property's values, a
*type-scoped context* when it sits in a class term and applies to nodes of that type. The JSON-LD API
stores it in the term definition as the term's *local context*, and a `@context` written inside a
node object in the data is an *embedded context*. In programming-language terms the behaviour under
`"scope": "enclosing"` is *lexical (static) scoping* with *shadowing*: definitions are attached to a
position in the syntax tree and visible in its subtree, as opposed to the *dynamic scoping* of, say,
ANTLR 3's rule and global `scope` attributes, which follow the call chain. The default `"scope": "none"`
is the reading of a grammar, where a production names the symbols that may follow and nothing else.
Compilers call the data structure a chain of *environments* or nested *symbol tables*; attribute
grammars call what is passed down an *inherited attribute*; XML Namespaces call the same arrangement
*in-scope namespaces*.

**A property map.** JSON-LD calls the whole map a *context*, each entry a *term definition* (an
*expanded term definition* when it is an object), and the part that names the property the term's
*IRI mapping*; the set held by a processor is the *active context*'s term definitions, which some
implementations call the *term map*. RDFa Core calls the same entries *term mappings*. In R2RML and
RML, where mappings are triples rather than JSON, the counterpart of one property definition is a
*predicate-object map*, assembled from *term maps* (constant-, reference- or template-valued), and
the counterpart of this whole document is a *triples map*. JSON-LD-array calls it a *property map*
(`propertyMap`), its entries *property definitions*, and a map declared at the root and referred to
by name a *named map*, the counterpart of a grammar's production.

## 10. JSON-LD, JSON-LD-array and RML side by side

RML, the RDF Mapping Language, generalizes W3C's R2RML from relational tables to CSV, XML and JSON
sources. It is maintained by the W3C Knowledge Graph Construction Community Group as a family of
modules (RML-Core, RML-IO, RML-CC for collections and containers, RML-FNML for functions, RML-star,
RML-LV for logical views), with YARRRML as a YAML shorthand. Where JSON-LD annotates the keys of the
data and JSON-LD-array maps them, RML describes the *output*: each **triples map** names a logical
source and an iterator that selects records, a **subject map** that mints each record's subject, and
**predicate-object maps** that emit the triples, every part of which is a **term map** that is
constant-valued, reference-valued (a field of the record) or template-valued.

| Aspect | JSON-LD 1.1 | JSON-LD-array | RML (R2RML vocabulary plus the RML modules) |
|---|---|---|---|
| Shape of the mapping | a `@context`: annotations on the data's own keys, inline or fetched | a mapping document shaped like a context, given beside the data or embedded as `mapping` / `propertyMap` members | an RDF document of triples maps, usually Turtle, or YARRRML in YAML; nothing in the data |
| Unit of work | a node object | a JSON object: every object is a node, governed by the maps of its position and type | an iteration of a logical source: `rml:iterator` (a JSONPath such as `$.people[*]`) selects the records, one subject each |
| Nested objects | nested node objects, linked by their position | nested nodes, linked by their position; `flatten` for wrapper objects and envelopes | a nested reference (`address.city`) on the same subject, or a second triples map with its own iterator joined back to the parent; a nested record sees its parent's fields only through RML-LV logical views |
| Subject identity | `@id`, an IRI or a relative reference, reached from conventional JSON by aliasing (`"id": "@id"`) | `role: "identifier"`, resolved against a lexically scoped base or expanded from a template over the object's members; a fresh or a stable blank node otherwise | a subject map: constant, reference or template over any fields, with `rr:termType` IRI or blank node; a blank node minted from a template is the same node for the same value |
| Classes | `@type` with class terms | `role: "type"` through `typeMap`: the class comes from a data field | `rr:class` on the subject map: the class comes from the mapping's structure; or an `rdf:type` predicate-object map |
| Predicates | terms, or any key under `@vocab` | keys resolved through the governing property maps, inline or named | predicate maps, usually constant but reference- or template-valued predicates can be built from the data |
| Literals | native types become `xsd:integer`, `xsd:double`, `xsd:boolean`; `@type` and `@language` per term; a default `@language` | native types become `xsd:integer`, `xsd:decimal`, `xsd:boolean`; `datatype`, `language`, `direction` per key; `rdf:JSON` for opaque subtrees | R2RML's natural datatype mapping; `rr:datatype` and `rr:language` constants, and in RML `rml:datatypeMap` and `rml:languageMap` taken from the data |
| IRIs from values | `@type: @id`, resolved against `@base` | `valueType: "identifier"`, resolved against the base in force or expanded from a template | an object map with `rr:termType rr:IRI`: reference or template, percent-encoded to an IRI-safe string |
| Several values | arrays are sets; `@list` for order; 1.0 forbade lists of lists | arrays are sequences, ordered; `keyedBy` dictionaries are repeated properties | a reference that yields several values emits several triples; RML-CC gather maps build `rdf:List`, `rdf:Seq`, `rdf:Bag` or `rdf:Alt`, with `rml:append` or `rml:cartesianProduct` strategies and `rml:allowEmptyListAndContainer` |
| Dictionaries | `@container: @index`, `@id`, `@language`, `@type` | `keyedBy` | awkward: JSONPath selects values, not member names, so processors need extensions to reach the keys |
| Links within a document | a node object carrying the target's `@id` | the same IRI minted twice: `identifier` on one side, `valueType: "identifier"` on the other | a referencing object map with `rr:joinCondition`, or the idiom of using the same template in both maps |
| Reverse relations | `@reverse`: no literals, no lists | `inverse`, spreading arrays | another triples map with the roles swapped; no construct needed |
| Scoping and reuse of definitions | embedded and scoped contexts, remote contexts, `@import`, `@protected` | `propertyMap` at root, property and type level, inline or named; `unmappedKeys.scope` for none, root or enclosing fallback | none: each triples map stands alone; prefixes come from Turtle; YARRRML adds `$(…)` references and templates for brevity |
| Named graphs | `@graph` | none | `rr:graphMap` on subject and predicate-object maps |
| Transforming values | none | none | RML-FNML: functions described with the Function Ontology, and conditions through functions in implementations |
| Quoted triples | JSON-LD-star, not standardized | none | RML-star `rml:StarMap` |
| Unmapped data | dropped, or everything becomes a property under `@vocab` | `unmappedKeys` and `unmappedTypes`: a scope and an `otherwise` | only referenced data is read: positive selection, so there is nothing to drop |
| Missing values and `null` | dropped; `null` also undefines terms and resets contexts | dropped | a reference with no value produces no triple |
| Direction | both ways: expansion, compaction, framing | JSON to RDF; the inverse is defined for tree-shaped graphs | one way, source to RDF; `rr:inverseExpression` only hints at the reverse for tables |
| Status | W3C Recommendation (2020) | this sketch | R2RML a W3C Recommendation (2012); the RML modules W3C Community Group reports (2023–2025); processors such as RMLMapper, Morph-KGC and SDM-RDFizer |

## 11. Conventions worth borrowing from RML

RML's one organizing idea is the **term map**: whatever part of an output triple is being produced,
subject, predicate, object or graph, and in RML also the datatype and the language of a literal, it
comes from a map of one of three kinds, **constant**, **reference** (a field of the current record)
or **template** (a string with `{field}` references, percent-encoded when it makes an IRI). JSON-LD has
only constants in the context and positions in the data. JSON-LD-array has adopted templates (§3.5);
the rest of the triad, and the conventions that follow from it, are proposed here.

| RML convention | What it gives conventional JSON | In JSON-LD-array |
|---|---|---|
| Template-valued subject maps over several fields, IRI-safe | identifiers composed from several fields, numeric ids, no relative-IRI tricks | **adopted**: `template` on identifier keys and values, `baseTemplate`, and an `identifier` attribute on the mapping root or on a property definition, `"identifier": { "template": "https://example.org/people/{id}" }`, describing the object itself; `role: "identifier"` on a key is then the shorthand for `"identifier": { "from": "key" }` |
| Constant, reference or template, everywhere | one rule for every attribute that names a term, learned once | proposed: every term-naming attribute (`iri`, `identifier`, `class`, `datatype`, `language`, the predicate of a `keyedBy`) takes a string constant, `{ "from": "key" }` (the value of a sibling member; `"."` the own value, `"../id"` the enclosing object's) or `{ "template": "…{key}…" }` |
| `rr:termType rr:BlankNode` with a template: stable blank nodes | anonymous nodes that several places refer to consistently, without minting IRIs | **adopted**: `"identifier": { "template": "address-of-{id}", "termType": "blankNode" }` |
| `rr:class` on the subject map: class by structure | nodes typed by where they sit, when the data has no type field | proposed: `class` on a property definition whose values are objects, and on the mapping root for the root object; `typeMap` stays for data-driven types |
| The same template as the join | foreign keys in flat JSON become links without a join | **adopted**: `valueType: "identifier"` with a `template` on the referring key; both sides mint the same IRI |
| One record, several subjects | a flat record split into a thing and its address, its measurement, its contact point | proposed: a `groups` attribute beside `propertyMap`, declaring *virtual properties* that do not mirror a data key: each is built from named sibling keys, which it consumes |
| Reference- or template-valued predicate maps | dictionaries whose keys are property names | proposed: `keyedBy: { "predicate": { "template": "…{}" } }` |
| `rml:languageMap`, `rml:datatypeMap` | the language or datatype sits in a sibling field | proposed: `"language": { "from": "lang" }`, `"datatype": { "from": "unit" }`; a member read this way is consumed and needs no definition of its own |
| Positive selection: only referenced data is read | tolerance of the fields an API adds next month | proposed: `"otherwise": "ignore"` as the default, `"error"` staying as a lint mode |
| `rml:iterator`: say where the records are | API envelopes such as `{ "data": [ … ], "meta": { … } }` | **adopted**: `flatten: true` on an array-valued key makes its elements root nodes |
| RML-LV logical views: a nested record sees its parent | identifiers and links that need the parent's id | **adopted**: `{../key}` and `{#}` in templates (§3.5), which RML cannot see without a view and a sequence keeps anyway |
| RML-CC gather maps | — | nothing: a sequence does what a gather map does, `rml:allowEmptyListAndContainer` is always on (`[]` is `()`), and `rml:cartesianProduct` has no analogue because elements are never multiplied |

Not worth borrowing: logical sources and iterators (the tree is the iterator), join conditions
(nesting and shared templates replace them), the RDF syntax of the mapping (JSON stays), graph maps,
and FNML functions, which are a separate concern that a later `transform` hook could take up.

### 11.1 The borrowed conventions at work

A flat record, the most conventional JSON there is:

```json
{ "id": 7, "first": "Ada", "last": "Lovelace",
  "street": "12 St James's Square", "city": "London",
  "bio": "Mathematician", "lang": "en",
  "editorId": 5, "works": [101, 102],
  "prices": { "GBP": 10, "EUR": 12 },
  "phones": [ { "number": "+44 20 7946 0000" },
              { "number": "+1 212 555 0100" } ] }
```

| Mapping (adopted and proposed syntax) | Turtle-array |
|---|---|
| root: `"identifier": { "template": "https://example.org/people/{id}" }`, `"class": "schema:Person"`, `"propertyMap": { "first": "schema:givenName", "last": "schema:familyName", … }` | `<…/people/7> a schema:Person ; schema:givenName "Ada" ; schema:familyName "Lovelace" .` |
| `"groups": { "home": { "iri": "schema:address", "members": ["street", "city"], "class": "schema:PostalAddress", "identifier": { "template": "address-of-{id}", "termType": "blankNode" }, "propertyMap": { "street": "schema:streetAddress", "city": "schema:addressLocality" } } }` | `<…/people/7> schema:address _:address-of-7 .`<br>`_:address-of-7 a schema:PostalAddress ; schema:streetAddress "12 St James's Square" ; schema:addressLocality "London" .` |
| `"bio": { "iri": "schema:description", "language": { "from": "lang" } }` | `<…/people/7> schema:description "Mathematician"@en .` (`lang` is consumed) |
| `"editorId": { "iri": "schema:editor", "valueType": "identifier", "template": "https://example.org/people/{}" }` | `<…/people/7> schema:editor <…/people/5> .` |
| `"works": { "iri": "schema:author", "inverse": true, "valueType": "identifier", "template": "https://example.org/works/{}" }` | `<…/works/101> schema:author <…/people/7> .`<br>`<…/works/102> schema:author <…/people/7> .` |
| `"prices": { "keyedBy": { "predicate": { "template": "https://example.org/ns#price-{}" } } }` | `<…/people/7> ex:price-GBP 10 ; ex:price-EUR 12 .` |
| `"phones": { "iri": "schema:contactPoint", "class": "schema:ContactPoint", "identifier": { "template": "https://example.org/people/{../id}/phone/{#}" }, "propertyMap": { "number": "schema:telephone" } }` | `<…/people/7> schema:contactPoint ( <…/people/7/phone/1> <…/people/7/phone/2> ) .`<br>`<…/people/7/phone/1> a schema:ContactPoint ; schema:telephone "+44 20 7946 0000" .`<br>`<…/people/7/phone/2> a schema:ContactPoint ; schema:telephone "+1 212 555 0100" .` |
| envelope `{ "data": [ …, … ], "meta": { "page": 1 } }` with `"data": { "flatten": true }` and `"otherwise": "ignore"` | one root node per element of `data`; nothing from `meta` |

If the proposals are adopted, they fold into §3 as follows: `identifier`, `class` and `groups` join
the attribute tables; `iri`, `datatype`, `language` and the `keyedBy` predicate accept the three
forms, constant, `from` and `template`; and `unmappedKeys` changes its `otherwise` default to
`"ignore"`.

## 12. Implementations and tests

**jsonld.js-array** ([rdf-array/jsonld.js-array](https://github.com/rdf-array/jsonld.js-array)) is the
reference implementation, added to jsonld.js beside its unchanged JSON-LD processor:
`jsonld.arrayToRDF(data, mapping, {format})` returns RDF/JS quads, or N-Quads-array
(`application/n-quads`) or Turtle-array (`text/turtle`) text; `jsonld.array.parseJSON` keeps the
lexical form of numbers; `jsonld.array.compileMapping` validates a mapping once for reuse; errors carry
the codes of §3.7 in `details.code` and the path in `details.path`. It implements §2 to §5 and, as
extensions, every proposal of §11. Its `doc/rdf-array.md` records the decisions the implementation
took, which this document has since adopted. A [playground](https://rdf-array.github.io/jsonld.js-array/)
runs it in the browser over the examples of this document.

**Tests.** Every row of the tables in §5 and §11.1 is a test case: JSON data and a mapping in, the
Turtle-array out, or one of the errors of §3.7. jsonld.js-array's `tests/array.js` holds them as
mocha tests, with the error cases and malformed mappings besides. They are to move into a shared
manifest of the rdf-array conformance suite (`jla:ToRdfTest`: `mf:action` the data, `jla:mapping`
the mapping, `mf:result` the N-Quads-array), so that a second implementation starts from the same
expectations.

**A second implementation** needs an rdf-array data model with the sequence term, an RFC 3986
resolver, a JSON parser that can report the source text of numbers (or the acceptance that `1.70`
becomes `1.7`), and a writer for N-Quads-array or Turtle-array. It walks the JSON once, by the rules
of §3.4 and §3.5; nothing in the mapping language needs the JSON-LD expansion algorithm.
