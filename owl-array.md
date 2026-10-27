# OWL-array: OWL over rdf-array

*Definition, 2026-10-26; implemented in
[owlapi-array](https://github.com/rdf-array/owlapi-array) (OWL API 4.5.29, the 4.5 line that
Protégé 5.6 loads), 2026-10-26; a worked example over FHIR RDF, [examples/fhir](examples/fhir/index.html),
2026-10-27. This document is [owl-array.md](https://github.com/rdf-array/rdf-array) in the
organisation's meta-repository, rendered at <https://rdf-array.github.io/rdf-array/owl-array.html>;
[rdf-array.md](rdf-array.html) describes the change from RDF to rdf-array, and
[shacl-array.md](shacl-array.html) settles the same questions for SHACL. The `.claude/skills/owl-array`
skill in the same repository carries the implementation plan.*

OWL-array is OWL 2 ([OWL 2 Direct Semantics], [OWL 2 Mapping to RDF Graphs]) over the rdf-array data
model, in which `( … )` is one term, a *sequence*, and `()` is the empty sequence. It changes two
things and adds one small vocabulary:

1. **OWL's own lists are sequences.** The RDF mapping of OWL 2 spells the arguments of
   `owl:unionOf`, `owl:intersectionOf`, `owl:oneOf`, `owl:members`, `owl:propertyChainAxiom`,
   `owl:hasKey`, `owl:disjointUnionOf`, `owl:withRestrictions` and SWRL's `swrl:body` and
   `swrl:head` as RDF lists. Read with Turtle-array they are sequences, and a sequence is the only
   list: an `rdf:first`/`rdf:rest` ladder is triples (§2).
2. **A sequence in the data is an individual with built-in structure.** `ex:paper bibo:authorList
   ( ex:ada ex:alan )` holds one term. OWL-array reads that term as an individual of the class
   `ra:Sequence` whose members, length, first and last element are given by properties with a
   meaning the semantics fixes: `ra:member`, `ra:memberValue`, `ra:length`, `ra:first`, `ra:last`.
   Nothing about the term is asserted in triples, nothing is reserved vocabulary, and a class
   expression can constrain the members of a list-valued property while staying in OWL 2 DL (§3).

The second is the reason to do it. FHIR RDF writes a repeated element as a list, and its ontology
could not say what the list holds; in OWL-array it says so with a restriction on a restriction:

```turtle
PREFIX fhir: <http://hl7.org/fhir/>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX ra:   <https://rdf-array.github.io/rdf-array/vocab#>

fhir:CodeableConcept rdfs:subClassOf
  [ a owl:Restriction ; owl:onProperty fhir:coding ;
    owl:allValuesFrom [ a owl:Restriction ; owl:onProperty ra:member ; owl:allValuesFrom fhir:Coding ] ] .

ex:cc fhir:coding ( [ fhir:system [ fhir:v "http://loinc.org"^^xsd:anyURI ] ; fhir:code [ fhir:v "8480-6" ] ] ) .
```

In Manchester syntax, `fhir:coding only (ra:member only fhir:Coding)`. No construct in that axiom
is new: the OWL API, Protégé's expression editor and every OWL 2 DL reasoner accept it today,
treating `ra:member` as an ordinary object property. What is new is the meaning of `ra:member`,
and of the `( … )` term in the data it constrains; from the two, a reasoner concludes that the
blank node inside the list is a `fhir:Coding`. A worked example, the SWAT4LS 2016 FHIR reasoning
process over today's FHIR RDF, is [examples/fhir](examples/fhir/index.html).

## 1. Why

OWL 2 DL reserves `rdf:List`, `rdf:first`, `rdf:rest` and `rdf:nil` for its own syntax. An ontology
document whose data holds an RDF list leaves `rdf:first` triples unconsumed and is not OWL 2 DL,
so BIBO's `bibo:authorList` and SKOS's `skos:memberList` push their users into OWL Full, and no DL
class expression can look into a list at all. The workaround, since
[Drummond et al. 2006](https://research.manchester.ac.uk/en/publications/putting-owl-in-order-patterns-for-sequences-in-owl/),
has been to rebuild the ladder out of individuals under new names (a cell class, functional
"contents" and "next" properties, a transitive "followed by"), as OWL-S's `ObjectList` and the
[Collections Ontology](https://www.semantic-web-journal.net/content/collections-ontology-creating-and-handling-collections-owl-2-dl-frameworks)
did. Its limits are well documented: the structure is open (nothing says a cell has no other
successor), a fixed length cannot be stated without nesting one restriction per element, the
"last" element needs a transitive property that no cardinality may use, and classification of
450-element lists took minutes. Every one of those limits comes from deriving a list's structure
from triples. rdf-array makes the list a term; OWL-array gives the term a meaning.

| Use case | Data | What an OWL-array ontology can say |
|---|---|---|
| Bibliographic author order (`bibo:authorList`) | `ex:p bibo:authorList ( ex:ada ex:alan ex:grace )` | every author is a `foaf:Agent`; the first author has an affiliation; a paper has at least three authors |
| SKOS ordered collections (`skos:memberList`) | `ex:c skos:memberList ( ex:low ex:mid ex:high )` | every member is a `skos:Concept`; the list is not empty |
| Steps of a protocol, recipe or workflow | `ex:recipe ex:steps ( ex:chop ex:fry ex:serve )` | every step is a `Step`; the last step is a `Serving`; the first step needs no input |
| Geometry and measurements | `ex:ring ex:points ( ( 0 0 ) ( 0 1 ) ( 1 1 ) ( 0 0 ) )` | a ring has at least four points; each point is a pair of decimals |
| FHIR RDF (R5 writes repeated elements as lists) | `ex:cc fhir:coding ( [ fhir:system … ] )` | every coding is a `fhir:Coding` with a system and a code |
| Tuples and n-ary values | `ex:alice ex:salaryHistory ( ( 2019 50000 ) ( 2020 52000 ) )` | every entry is a pair; the pairs' members are numbers |
| Colours and other fixed-length values | `ex:red ex:rgb ( 255 0 0 )` | an `ex:rgb` value has three integer members; the class of things whose colour is `( 255 0 0 )` |

## 2. Lists in OWL's syntax

Everywhere the RDF mapping of OWL 2 reads a list, OWL-array reads a sequence term:

| Vocabulary | In Turtle-array |
|---|---|
| `owl:unionOf`, `owl:intersectionOf` (classes and data ranges) | `[ owl:unionOf ( ex:Cat ex:Dog ) ]` |
| `owl:oneOf` (individuals, or literals in a data range) | `[ owl:oneOf ( ex:red ex:green ) ]`, `[ owl:oneOf ( "a" "b" ) ]` |
| `owl:members`, `owl:distinctMembers` (AllDisjointClasses, AllDisjointProperties, AllDifferent) | `[ a owl:AllDifferent ; owl:members ( ex:a ex:b ex:c ) ]` |
| `owl:propertyChainAxiom` | `ex:uncle owl:propertyChainAxiom ( ex:parent ex:brother )` |
| `owl:hasKey` | `ex:Person owl:hasKey ( ex:ssn )` |
| `owl:disjointUnionOf` | `ex:Animal owl:disjointUnionOf ( ex:Cat ex:Dog )` |
| `owl:withRestrictions` | `[ owl:onDatatype xsd:integer ; owl:withRestrictions ( [ xsd:minInclusive 0 ] ) ]` |
| `owl:onProperties` (n-ary data ranges, not in OWL 2 DL) | `[ owl:onProperties ( ex:x ex:y ) ]` |
| SWRL `swrl:body`, `swrl:head`, `swrl:arguments` | `[ a swrl:Imp ; swrl:body ( … ) ; swrl:head ( … ) ]` |

Written in Turtle-array these are sequences already, so an OWL ontology written in Turtle reads
unchanged. As in SHACL-array, three consequences follow:

- **A ladder is not a list.** An ontology document that spells a list as `rdf:first`/`rdf:rest`
  triples (N-Triples written by an RDF 1.1 tool, say) leaves those triples unconsumed, exactly as a
  list in the data did before: the document is not OWL 2 DL and a parser reports the triples.
  Convert it first.
- **`()` is the empty list; `rdf:nil` is not.** A SWRL rule with no body writes `swrl:body ()`.
  `owl:unionOf ()` is as ill-formed as it was.
- **Lists hold no blank-node structure.** `owl:unionOf ( [ a owl:Restriction ; … ] )` is a sequence
  holding a blank node whose own triples are ordinary triples of the document.

What a processor writes follows: the RDF renderers spell every OWL list as `( … )` in Turtle and
as `rdf:parseType="Collection"` in RDF/XML, and never as a ladder. The Functional-style, OWL/XML and
Manchester syntaxes have no RDF lists and are unchanged by this part.

## 3. Sequences in the data

### 3.1 Semantics

The direct semantics changes in one place. The object domain of an interpretation contains, beside
the ordinary individuals, the *sequences*: finite tuples whose elements are individuals, data
values or sequences. A sequence term `( t1 … tn )` denotes the tuple of its elements' denotations,
`( t1^I … tn^I )`; `()` denotes the empty tuple. Consequently:

- **Identity is by elements.** Two sequence terms denote the same individual exactly when their
  elements denote the same things, pairwise: `( ex:a )` and `( ex:b )` are the same individual in
  every interpretation in which `ex:a owl:sameAs ex:b`, and `( 1 2 )` is the same term in every
  document, as `"1"^^xsd:integer` is.
- **Sequences are a sort of their own.** No IRI, blank node or literal denotes a tuple, so a
  sequence is never `owl:sameAs` an IRI-named individual, as a literal is not, and `ra:Sequence` is
  disjoint from every class of ordinary individuals.
- **A sequence is closed.** Its members are exactly its elements, in order; there is nothing more
  to learn about them from other triples.

Where a sequence may stand in an ontology: wherever the structural specification allows an
*individual*, with one restriction. It may be the subject or object of a property assertion, the
individual of a class assertion, an element of another sequence, a nominal in `owl:hasValue` and
`owl:oneOf`, a party to `owl:sameAs` and `owl:differentFrom`, and an annotation value or subject.
A sequence holding an anonymous individual anywhere inside is itself anonymous, and goes only where
OWL 2 DL lets an anonymous individual go: not into `owl:hasValue`, `owl:oneOf`, `owl:sameAs`,
`owl:differentFrom` or a negative property assertion.
A sequence is never a class, a property, a datatype or an ontology IRI. The RDF-based semantics
(OWL 2 Full) is not addressed here.

### 3.2 The vocabulary

The `ra:` namespace, `https://rdf-array.github.io/rdf-array/vocab#`, holds the built-in entities of
OWL-array. Like `owl:Thing` and `owl:topObjectProperty`, each has an extension the semantics fixes
in every interpretation. An ontology uses them in class expressions and property axioms; it does
not define them, and an axiom *about* one of them (a range on `ra:member`, say) constrains every
sequence in the world, as an axiom about `owl:topObjectProperty` would.

| Term | Kind | In every interpretation, for a sequence `s` |
|---|---|---|
| `ra:Sequence` | class | the sequences, and nothing else |
| `ra:member` | object property | `s ra:member e` for each element `e` of `s` that is an individual or a sequence |
| `ra:memberValue` | data property | `s ra:memberValue v` for each element `v` of `s` that is a literal |
| `ra:length` | functional data property | `s ra:length n`, `n` the number of elements of `s`, an `xsd:nonNegativeInteger` |
| `ra:first`, `ra:last` | functional object properties | the first and the last element of `s`, when it is an individual or a sequence |
| `ra:firstValue`, `ra:lastValue` | functional data properties | the first and the last element of `s`, when it is a literal |

`ra:first ⊑ ra:member`, `ra:last ⊑ ra:member`, `ra:firstValue ⊑ ra:memberValue` and
`ra:lastValue ⊑ ra:memberValue` hold by construction; so does `∃ra:member.⊤ ⊑ ra:Sequence` and the
like for every property above. Three classes are definable and are defined, with the declarations
and these axioms, in the vocabulary ontology [vocab/owl-array.ttl](vocab/owl-array.ttl), which an
ontology may import so that an editor knows the entities:

| Class | Definition |
|---|---|
| `ra:EmptySequence` | `ra:Sequence and ra:length value 0`, the class of `()` |
| `ra:ObjectSequence` | `ra:Sequence and not (ra:memberValue some rdfs:Literal)`: no literal members |
| `ra:DataSequence` | `ra:Sequence and not (ra:member some owl:Thing)`: no individual members |

The vocabulary ontology is plain OWL 2 DL and says the same thing read as RDF 1.1 or as rdf-array.
Importing it is a convenience, not a requirement: the meaning of the built-ins does not come from
its axioms.

### 3.3 What an ontology can say

The use cases of §1, in Manchester syntax, with the Turtle-array of the first:

```
Class: ex:Paper
  SubClassOf: bibo:authorList only (ra:member only foaf:Agent)        # every author is an agent
  SubClassOf: bibo:authorList only (ra:first some (foaf:Person and ex:affiliation some ex:Org))
Class: ex:BigPaper
  EquivalentTo: ex:Paper and bibo:authorList some (ra:length some xsd:integer[>= 3])
Class: skos:OrderedCollection
  SubClassOf: skos:memberList only (ra:member only skos:Concept)
  SubClassOf: skos:memberList only (not ra:EmptySequence)
Class: ex:Recipe
  SubClassOf: ex:steps only (ra:member only ex:Step), ex:steps only (ra:last some ex:Serving)
Class: ex:Ring
  SubClassOf: ex:points only (ra:length some xsd:integer[>= 4]
                              and ra:member only (ra:length value 2 and ra:memberValue only xsd:decimal))
Class: ex:Swatch
  SubClassOf: ex:rgb only (ra:length value 3 and ra:memberValue only xsd:integer[>= 0, <= 255])
Class: ex:RedThing
  EquivalentTo: ex:rgb value ( 255 0 0 )                               # a sequence as a nominal
ObjectProperty: dc:creator
  SubPropertyChain: bibo:authorList o ra:member                        # flattens the list by axiom
ObjectProperty: ex:firstAuthor
  SubPropertyChain: bibo:authorList o ra:first
```

```turtle
PREFIX bibo: <http://purl.org/ontology/bibo/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX ra:   <https://rdf-array.github.io/rdf-array/vocab#>

ex:Paper rdfs:subClassOf
  [ a owl:Restriction ; owl:onProperty bibo:authorList ;
    owl:allValuesFrom [ a owl:Restriction ; owl:onProperty ra:member ; owl:allValuesFrom foaf:Agent ] ] .

ex:p a ex:Paper ; bibo:authorList ( ex:ada ex:alan ex:grace ) .
```

The two quantifiers stay separate: `bibo:authorList only (ra:member only C)` says every author of
every author list is a `C`; `bibo:authorList some (ra:member some C)` says some list has some `C`;
`bibo:authorList only (ra:member some C)` says every list has one. A property chain through
`ra:member` or `ra:first` gives an existing vocabulary a view of the list: with the chain above,
`ex:p dc:creator ex:ada` is entailed, and every class expression ever written over `dc:creator`
applies to list members. Such a chain makes its super-property non-simple, so `dc:creator` can no
longer appear in a cardinality restriction; that is OWL 2's usual rule.

### 3.4 Entailments

From the ontology above, a reasoner that implements OWL-array (§6) concludes:

- `ex:ada a foaf:Agent`, `ex:alan a foaf:Agent`, `ex:grace a foaf:Agent`;
- `ex:p a ex:BigPaper`, since `( ex:ada ex:alan ex:grace ) ra:length 3`;
- `ex:p dc:creator ex:ada`, `ex:p ex:firstAuthor ex:ada`;
- `( ex:ada ex:alan ex:grace ) a ra:Sequence`, `ra:ObjectSequence`, and `not ra:EmptySequence`;
- if `ex:ada owl:sameAs ex:adaL`, then `ex:p bibo:authorList ( ex:adaL ex:alan ex:grace )`;
- `ex:ring a ex:Ring` with three points is inconsistent, and `ex:red ex:rgb ( 255 0 )` with
  `ex:red a ex:Swatch` is inconsistent;
- `ex:x ex:rgb ( 255 0 0 )` entails `ex:x a ex:RedThing`; `( 255 0 0 ) owl:differentFrom ( 0 0 255 )`
  holds in every interpretation.

Nothing follows about the members of a list from the list alone: `( ex:ada ex:alan )` says that
`ex:ada` is a member of it and nothing more, as a triple says nothing more than itself.

### 3.5 Counting, and literal members

Two consequences of OWL 2's semantics are worth knowing before writing cardinalities:

- **`ra:member` counts distinct individuals, not positions.** `( ex:a ex:a ex:a )` has one member,
  and `( ex:a ex:b ex:c )` has three only in interpretations where the three are different, which
  OWL does not assume. "At least three authors" is `ra:length some xsd:integer[>= 3]`, which is
  crisp; "three different authors" adds `ra:member min 3 foaf:Person` to it. The same holds for
  `ra:memberValue` and repeated literals.
- **`ra:member only C` says nothing about literal members.** It is vacuously true of `( 1 2 3 )`.
  To require that every element is an individual in `C`, write `ra:ObjectSequence and ra:member
  only C`; for literals, `ra:DataSequence and ra:memberValue only D`.

### 3.6 Profiles

OWL 2 EL has no `only`, so an EL ontology constrains members through a property chain and a range:
`bibo:authorList o ra:member SubPropertyOf: ex:author`, `ex:author Range: foaf:Agent`. OWL 2 RL
keeps `only` over members in superclass position, which is where the examples above use it, and
has no datatype facets, so length bounds are outside RL. The vocabulary ontology uses functional
object properties, complements and unions, which EL and QL lack; an EL or QL ontology relies on the
built-in meaning without importing it.

## 4. Writing a sequence in each OWL syntax

| Syntax | A sequence | Notes |
|---|---|---|
| Turtle-array, TriG-array, N-Triples-array | `( ex:a "x" ( 1 2 ) )`, `()` | as rdf-array.md |
| RDF/XML | `<ex:p rdf:parseType="Collection">…</ex:p>` | one term, `()` when empty; a literal element needs a nested description, so RDF/XML cannot write every sequence |
| Functional-style syntax | `Sequence( ex:a "x"^^xsd:string Sequence( "1"^^xsd:integer "2"^^xsd:integer ) )`, `Sequence( )` | a new production under `Individual` |
| OWL/XML | `<Sequence> <NamedIndividual IRI="…"/> <Literal>…</Literal> <Sequence/> </Sequence>` | likewise |
| Manchester syntax | `( ex:a "x" ( 1 2 ) )`, `( )` | in individual positions only: `Facts:`, `value`, `{ … }`, `SameAs:`, `DifferentFrom:`, `Individual:` |

Until a syntax's grammar is taught the spelling, an implementation may round-trip a sequence as an
anonymous individual whose node ID encodes the sequence reversibly, so that the same document read
back gives the same term; owlapi-array does so for the Functional-style, OWL/XML and Manchester
syntaxes in its first cut, and labels such a node ID `_:seq…`. A sequence never has an IRI.

## 5. What OWL-array does not add

- **No ladder reading.** `rdf:first`/`rdf:rest` triples are triples in OWL's syntax and in the data,
  and leave an ontology outside OWL 2 DL as they always did. OWL-array does not fold them.
- **No `ra:rest`.** A property to the sequence of the remaining elements would rebuild the ladder
  as individuals, with every limit of §1: it is left out on purpose. `ra:first` and `ra:last` cover
  the positions ontologies ask for; the remaining ones are reached, for now, by SPARQL-array's
  position patterns rather than by class expressions.
- **No positional class constructor.** A tuple type, `ra:tupleOf ( C1 … Cn )`, meaning "exactly n
  members, the i-th in Ci", and a regular content model over members are the natural next layer,
  as they are for SHACL-array and ShEx-array. The name `ra:tupleOf` is reserved and not defined.
- **No datatype reading.** A literal-only sequence is still an individual with `ra:memberValue`s,
  not a value of a sequence datatype. OWL 2 DL keeps individuals and data values apart, and a
  datatype could never say "every author is a Person"; one reading is simpler than two.
- **No counting by position** through `ra:member` (§3.5), and no uniqueness constraint: SHACL 1.2's
  `sh:uniqueMembers` has no OWL-array counterpart, since OWL cannot say that two positions differ.
- **No identity for sequences beyond their elements.** A sequence has no IRI and no label; an
  editor displays it by its spelling.

## 6. Reasoning with a reasoner that does not know sequences

The semantics of §3 is normative; how a reasoner meets it is not. The first implementations give
an existing OWL 2 DL reasoner (HermiT, JFact, ELK for EL) the meaning of the built-ins by
*expansion*: a decorator around the reasoner rewrites the ontology it sees, and nothing is added to
the ontology the user edits or saves. For each sequence term `s` in the imports closure, with
elements `e1 … en`:

- `s` becomes an individual: a named one, with a canonical IRI derived from the term's spelling,
  when `s` holds no anonymous individual, so that it can stand in `owl:hasValue` and `owl:oneOf`;
  an anonymous one otherwise. The IRI is an artefact of the expansion and never leaves it. Whether
  the anonymous individuals themselves should be named inside the expansion, so that every sequence
  is closed, is [rdf-array#20](https://github.com/rdf-array/rdf-array/issues/20); FHIR RDF, in which
  every element is a blank node, is the case that decides it.
- `ClassAssertion( ra:Sequence s )` and `DataPropertyAssertion( ra:length s n )`.
- `ObjectPropertyAssertion( ra:member s ei )` for each individual element and
  `DataPropertyAssertion( ra:memberValue s vi )` for each literal element, with `ra:first`,
  `ra:last`, `ra:firstValue` and `ra:lastValue` for the ends.
- **Closure:** `ClassAssertion( ra:member only { the individual elements } s )`, or
  `ra:member max 0` when there are none, and the same for `ra:memberValue` with a `DataOneOf`.
  Closure is what makes `ra:member only C` decidable on `s` and what no ladder could supply; it
  is omitted for an EL reasoner, which cannot express it and cannot ask the questions that need it.
- Nested sequences are expanded recursively; equal terms get the same individual, which gives
  identity by elements for ground sequences. Identity under `owl:sameAs` of elements (§3.1) is a key
  on positions; an expansion may add `HasKey` axioms per length for it, which OWL 2 restricts to
  named individuals, exactly the sequences that are named here.

The expansion is linear in the number of elements, complete for the sequences spelled in the
ontology, and sound for the rest: of a sequence that a class expression merely asserts to exist, a
reasoner knows what the vocabulary ontology's axioms say. The vocabulary ontology is added to the
closure the reasoner sees. Reasoner results that mention expansion individuals are mapped back to
sequence terms on the way out.

## 7. Tests

- **owlapi-array's own tests**, from the OWL API's `contract` module: every round-trip test whose
  RDF spells a list reads it as a sequence, and a test that depended on a ladder is flagged with the
  reason, never dropped, as the `array-tests` skill prescribes.
- **New tests**, in the fork: parsing `( … )` nested, empty and holding a blank node property list, in
  Turtle and RDF/XML; equality of sequence terms by elements; rendering and round trips through every
  syntax, with the node-ID stopgap where a grammar lacks the spelling; §2's lists as sequences;
  the examples of §3.3 checked against a DL reasoner through the expansion of §6, as entailments and
  as inconsistencies; the two caveats of §3.5 as tests that the naive reading does not hold.
- **The FHIR example**, [examples/fhir](examples/fhir/index.html): the SWAT4LS 2016 FHIR reasoning
  process over today's FHIR RDF, 24 DL queries with their expected answers and one inconsistency, run
  through owlapi-array and HermiT by its `FhirReasoning.java`; to become a test in the fork.
- **owl-tests-contrib**, if a second implementation follows: the same cases in a manifest, with a
  requirement term `ra:OwlArray` added to the test vocabulary with it.

## 8. Implementations

| Implementation | OWL's lists as sequences | Data sequences | Reasoning | Status |
|---|---|---|---|---|
| [owlapi-array](https://github.com/rdf-array/owlapi-array) (OWL API 4.5.29) | Turtle and RDF/XML parsers and renderers; RDF/XML refuses a sequence holding a literal ([#18](https://github.com/rdf-array/rdf-array/issues/18)); the Rio formats still use ladders ([#19](https://github.com/rdf-array/rdf-array/issues/19)); Functional-style, OWL/XML and Manchester carry a sequence as a `_:seq_…` node ID | an `OWLSequence` individual, equal by elements | the expansion of §6 as `SequenceAwareReasonerFactory`, tested with HermiT 1.4.5; no closure when a sequence holds an anonymous individual ([#20](https://github.com/rdf-array/rdf-array/issues/20)) | the term, parsers, renderers and decorator done 2026-10-26; the FHIR example a test, blank nodes inside sequences written inside them, 2026-10-27: 4703 tests, 0 failures, 316 flagged; see its `doc/rdf-array.md` |
| Protégé 5.6.9 against owlapi-array | its `bundles/owlapi-osgidistribution.jar` replaced by owlapi-array's, same symbolic name and version; no editor change | displayed by node ID, `_:seq_…`, until the Manchester renderer learns `( … )`; never a DL Query answer ([#21](https://github.com/rdf-array/rdf-array/issues/21)) | "HermiT 1.4.3 (OWL-array)" and "ELK 0.6.0 (OWL-array)" in the reasoner menu, from [protege-owl-array](https://github.com/rdf-array/protege-owl-array); ELK skips the blank nodes that hold FHIR data | done 2026-10-27: [examples/fhir](examples/fhir/index.html) §4, the 24 DL queries answered in the DL Query tab as through the OWL API |

## 9. Decisions and precedent

- **An individual, not a data value, and not syntax only.** The datatype alternative (§5) could not
  reach IRI or blank-node members; leaving data sequences unread would have left the motivating
  cases out. The individual reading is the only one that lets a class expression say "every author
  is a Person".
- **Built-in properties, not a new restriction kind.** `owl:onPropertyMembers`, a restriction whose
  `allValuesFrom` applied to the members of a property's values, was considered. It fuses two
  quantifiers (every value, every member) and would need new class expressions in every syntax,
  parser, renderer and reasoner interface. Nesting an ordinary restriction on `ra:member` needs none
  of that, composes with property chains, and matches SHACL 1.2's `sh:memberShape` plus
  `sh:minListLength`, ShEx-array's `((S))[m, n]`, JSON Schema's `items` plus `minItems`, and the
  array types of property-graph schemas (Neo4j's `LIST<INTEGER NOT NULL>` constraints, PG-Schema's
  `STRING ARRAY {1,2}`): a constraint on members and bounds on length.
- **Identity by elements, no IRI.** An earlier draft named each sequence with a reversible URN and
  an `rdfs:label`. That makes `( ex:a )` and `( ex:b )` different individuals when `ex:a owl:sameAs
  ex:b`, and no other rdf-array implementation gives a sequence an identity beyond its elements.
  The canonical IRI survives only inside the expansion (§6).
- **No companion ontology.** The same draft materialised the `ra:` assertions into an ontology
  imported beside the source. The length of `( 1 2 3 )` is a fact about the term, as the value of
  `"3"^^xsd:integer` is; it is computed where it is needed, not stored.
- **No `ra:rest`**, for the reasons of §5.
- Precedent for description logic over sequences is thin and all of it builds proxies:
  [Drummond et al.](https://research.manchester.ac.uk/en/publications/putting-owl-in-order-patterns-for-sequences-in-owl/)
  (2006), who also showed regular-expression-like matching over classes of lists by nesting;
  the [Collections Ontology](https://www.semantic-web-journal.net/content/collections-ontology-creating-and-handling-collections-owl-2-dl-frameworks)
  with indexed `co:ListItem`s; the ontology design patterns' Sequence pattern. The theory that
  bears on OWL-array is Baader and Sattler's on
  [aggregates](https://iccl.inf.tu-dresden.de/web/LATPub267) (a built-in `ra:length` on a closed
  term avoids the undecidability of counting over open chains), Lutz, Areces, Horrocks and
  Sattler's on [keys](https://jair.org/index.php/jair/article/view/10412) (identity by elements is a
  key on positions, decidable over named individuals), and temporal description logics over
  [finite traces](https://bia.unibz.it/esploro/outputs/conferenceProceeding/Temporal-description-logics-over-finite-traces/991005772379101241)
  for the content-model layer to come. Property graphs have arrays only of primitive values and
  constrain them by element type and count; none lets an array hold a node, which is the case
  that matters here.

[OWL 2 Direct Semantics]: https://www.w3.org/TR/owl2-direct-semantics/
[OWL 2 Mapping to RDF Graphs]: https://www.w3.org/TR/owl2-mapping-to-rdf/
