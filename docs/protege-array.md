---
template: page
title: OWL-array in Protégé
description: rdf-array's FHIR example in Protégé 5.6.9: FHIR RDF writes every repeating element as a list ( … ); read as one term each, with OWL-array's semantics for the term, HermiT classifies observations and patients by what is inside the lists.
eyebrow: rdf-array · OWL-array in Protégé · demo
---
# Protégé reasons into FHIR's lists

FHIR RDF writes every repeating element as a Turtle list `( … )`. Read as [rdf-array](rdf-array.html),
the list is one term; [OWL-array](owl-array.html) gives the term a meaning; Protégé 5.6.9, with one
bundle swapped and one plugin added, classifies observations and patients by what is inside the
lists. Protégé itself is not modified.

The data is rdf-array's [FHIR example](../examples/fhir/index.html): the
[SWAT4LS 2016](https://www.w3.org/2016/Talks/1205-swat4ls-egp/reasoning.html) FHIR reasoning process
(recognizers of codings, connective tissue to SNOMED CT, DL queries over its hierarchy) over the
FHIR RDF of today. Two jars make it run. [owlapi-array](https://github.com/rdf-array/owlapi-array)
replaces Protégé's OWL API bundle under the same symbolic name and version, so every other plugin
loads unchanged. [protege-owl-array](https://github.com/rdf-array/protege-owl-array) adds
**HermiT 1.4.3 (OWL-array)** to the Reasoner menu: the bundled HermiT behind a decorator that hands
it the meaning of each list. The screenshots are Protégé's own window, painted to PNG by the
walk-through harness in protege-owl-array; its log is
[walkthrough.txt](../examples/fhir/protege/walkthrough.txt). Click a detail for the whole window.

## One axiom, three readings

`CodeableConcept.coding` is 0..*. FHIR RDF writes it as a list, and the FHIR ontology,
[fhir.ttl](https://build.fhir.org/fhir.ttl), types it as it types every other element:

```turtle
ex:cc fhir:coding ( [ fhir:system [ fhir:l <http://snomed.info/sct> ] ; fhir:code [ fhir:v "69896004" ] ] [ … ] ) .

fhir:CodeableConcept SubClassOf: fhir:coding only fhir:Coding       # fhir.ttl
```

- **OWL 2 DL over RDF 1.1, which is Protégé as shipped.** `rdf:first` and `rdf:rest` are OWL's own
  syntax, so the OWL API's RDF parser consumes the ladder wherever it stands and keeps nothing of
  it. Measured with the stock OWL API 4.5.29 on [subject-amy.ttl](../examples/fhir/subject-amy.ttl):
  189 triples, 0 reported unparsed, no warning; each `fhir:coding` points to a blank node with no
  other triple, and every element of a list, the 8 codings among them, is a blank node that nothing
  refers to. The axiom is satisfied by the empty node. This is what FHIR's
  [RDF page](https://build.fhir.org/rdf.html) means by lists "cause problems for OWL 2".
- **OWL 2 DL over rdf-array, the axiom as published.** The value of `fhir:coding` is one term, the
  sequence. The axiom types the sequence as a Coding; no FHIR element is a sequence
  (`fhir:Base DisjointWith: ra:Sequence` in [fhir-min.ttl](../examples/fhir/fhir-min.ttl)), so the
  data is inconsistent. That is the right answer: the axiom was written about the elements.
- **OWL-array.** The axiom says what fhir.ttl means, and adds the cardinality that the list form
  makes true:
  ```manchester
  fhir:CodeableConcept SubClassOf: fhir:coding only (ra:Sequence and ra:member only fhir:Coding),
                                  fhir:coding max 1
  ```
  Every construct here is OWL 2 DL today: Protégé's expression editor and every DL reasoner accept
  it, with `ra:member` an ordinary object property. What is new is the meaning of `ra:member` and of
  the term it reaches into.

## What OWL-array adds to OWL 2

One change to the [Direct Semantics](https://www.w3.org/TR/owl2-direct-semantics/). The object
domain of an interpretation holds, beside the ordinary individuals, the *sequences*: finite tuples
whose elements are individuals, data values or sequences. A sequence term denotes the tuple of its
elements' denotations,
<code>( t<sub>1</sub> … t<sub>n</sub> )<sup>I</sup> = ( t<sub>1</sub><sup>I</sup> … t<sub>n</sub><sup>I</sup> )</code>,
and `()` the empty tuple. Nothing else changes: no new class expression, no new axiom type, no
change to `OWLReasoner`. Three things follow.

- **Identity is by elements.** `( ex:a )` and `( ex:b )` are the same individual exactly when
  `ex:a owl:sameAs ex:b`. No IRI or blank node stands for a sequence, and no triple is about one.
- **A sort of its own.** No IRI, blank node or literal denotes a tuple, so `ra:Sequence` is disjoint
  from every class of ordinary individuals, as the literals are.
- **Closed.** A sequence's members are its elements, in order. There is nothing more to learn about
  them from other triples.

The built-ins have a fixed extension in every interpretation, as `owl:Thing` and
`owl:topObjectProperty` do. An ontology uses them; it does not define them.

| Built-in | In every interpretation, for a sequence `s` |
|---|---|
| `ra:Sequence` | the sequences, and nothing else |
| `ra:member`, `ra:memberValue` | `s ra:member e` for each element `e` that is an individual or a sequence; `ra:memberValue` for each literal element |
| `ra:length` | functional: the number of elements, an `xsd:nonNegativeInteger` |
| `ra:first`, `ra:last` | functional: the first and the last element (`ra:firstValue`, `ra:lastValue` when it is a literal) |

`ra:member` is a set view of the tuple: `( ex:a ex:a )` has one member, and OWL does not assume
distinct names denote distinct things. Positions are counted by `ra:length`, so a bound on the
length is one datatype facet, not a nested restriction per element. The rest of the fine print,
including the OWL 2 EL and RL profiles, is [owl-array.md §3](owl-array.html#sequences-in-the-data).

### How a stock reasoner decides it

owlapi-array's `SequenceAwareReasonerFactory` wraps any `OWLReasonerFactory`. For each sequence term
<code>s = ( e<sub>1</sub> … e<sub>n</sub> )</code> in the imports closure it gives the reasoner, and
only the reasoner, an individual for `s` and ordinary assertions:

<pre><code>s <span class="k">a</span> ra:Sequence .   s ra:length n .
s ra:member e<sub>1</sub> , … , e<sub>n</sub> .   s ra:first e<sub>1</sub> .   s ra:last e<sub>n</sub> .
s <span class="k">a</span> [ ra:member <span class="k">only</span> { e<sub>1</sub> … e<sub>n</sub> } ]     <span class="c"># the closure, when the elements are named</span></code></pre>

Nested sequences expand recursively, and equal terms get the same individual. The expansion is
linear in the number of elements, its output is OWL 2 DL, and HermiT runs it unchanged. A result
that mentions an expansion individual is mapped back to its term on the way out. The ontology you
edit and save never sees any of this.

What a ladder cannot give. Over `rdf:first`/`rdf:rest`, nothing: OWL 2 DL reserves them. Over a
ladder rebuilt from individuals
([Drummond et al. 2006](https://research.manchester.ac.uk/en/publications/putting-owl-in-order-patterns-for-sequences-in-owl/),
the [Collections Ontology](https://www.semantic-web-journal.net/content/collections-ontology-creating-and-handling-collections-owl-2-dl-frameworks)),
a list is open, since nothing says a cell has no other successor, so `only` over its members is not
decided from the data; "last" needs a transitive property that no cardinality may use; a length is
one nested restriction per element; and classification of 450-element lists took minutes. Each
limit comes from deriving a list's structure from triples. Here the term is the structure, and the
reasoner is told it.

## Set it up

Git, Maven and a JDK 11 or newer. `assemble.sh` starts from the stock Protégé 5.6.9 zip and swaps
in the two jars, built from source on the first run:

```bash
git clone https://github.com/rdf-array/protege-owl-array.git
git clone https://github.com/rdf-array/rdf-array.git
cd protege-owl-array
./assemble.sh Protege-5.6.9-owl-array
JAVA_HOME=$(/usr/libexec/java_home -v 21) \
  Protege-5.6.9-owl-array/run.sh ../rdf-array/examples/fhir/subjects.ttl
```

The `java_home` line is macOS; elsewhere set `JAVA_HOME` to any JDK 11 or newer. `subjects.ttl`
imports Amy's, Bob's and Sue's records, the arthritis and blood-pressure definitions, the 2016
talk's SNOMED CT extract, the part of the FHIR ontology they use, and the OWL-array vocabulary; its
`catalog-v001.xml` maps each import to the file beside it.

## FHIR/RDF, lists everywhere

Amy's rheumatoid-arthritis observation, from [subject-amy.ttl](../examples/fhir/subject-amy.ttl):
two codings, SNOMED CT first and ICD-10 second, and the SNOMED CT concept IRI that FHIR's generator
adds as a type when the code system has an IRI stem. ICD-10 has none, so that coding is reachable
only through the list.

```turtle
amy:Obs1 a fhir:Observation ;
  fhir:code [
     a sct:69896004 ;
     fhir:coding ( [
       fhir:system [ fhir:v "http://snomed.info/sct"^^xsd:anyURI ; fhir:l <http://snomed.info/sct> ] ;
       fhir:code [ fhir:v "69896004" ] ;
       fhir:display [ fhir:v "Rheumatoid arthritis" ]
     ] [
       fhir:system [ fhir:v "http://hl7.org/fhir/sid/icd-10"^^xsd:anyURI ; fhir:l <http://hl7.org/fhir/sid/icd-10> ] ;
       fhir:code [ fhir:v "M06.9" ] ;
       fhir:display [ fhir:v "Rheumatoid arthritis, unspecified" ]
     ] ) ;
     fhir:text [ fhir:v "Rheumatoid arthritis" ]
  ] ;
  fhir:subject [ fhir:reference [ fhir:v "Patient/amy" ] ; fhir:l amy:asPatient ] .
```

Sue's observation has one ICD-10 coding and no concept IRI. Everything a reasoner learns about it
comes from inside the list:

```turtle
sue:Obs1 a fhir:Observation ;
  fhir:code [
     fhir:coding ( [
       fhir:system [ fhir:v "http://hl7.org/fhir/sid/icd-10"^^xsd:anyURI ; fhir:l <http://hl7.org/fhir/sid/icd-10> ] ;
       fhir:code [ fhir:v "M05.9" ] ;
       fhir:display [ fhir:v "Seropositive rheumatoid arthritis, unspecified" ]
     ] ) ] ;
  fhir:subject [ fhir:reference [ fhir:v "Patient/sue" ] ; fhir:l sue:asPatient ] .
```

Lists nest. Sue's names are a list, and the one name holds a list of two given names:

```turtle
sue:asPatient a fhir:Patient ;
  fhir:name ( [
     fhir:family [ fhir:v "Jones" ] ;
     fhir:given ( [ fhir:v "Sue" ] [ fhir:v "Ann" ] )
  ] ) .
```

The domain logic is the 2016 talk's, in [arthritis.ttl](../examples/fhir/arthritis.ttl): a
recognizer per code (a Coding whose system is SNOMED CT and whose code is "69896004"), and one
general class inclusion per concept that reaches into the list at any position:

```manchester
:Coding-of-sct-69896004 EquivalentTo: :Coding-in-SNOMED and fhir:code some (fhir:v value "69896004")

fhir:coding some (ra:member some (:Coding-of-sct-69896004 or :Coding-of-icd10-M06.9))
    SubClassOf sct:69896004              # the type arc FHIR's generator adds when it can
```

## Open it; every list is parsed

Protégé opens `subjects.ttl` and follows the nine imports: 10 ontologies, 1,171 axioms, no triple
unparsed, `rdf:first` in no signature, and the 16 lists in the data are 16 sequence terms.

[![Protégé's Active ontology tab for subjects.ttl, with the ontology metrics: 1,171 axioms, 488
logical axioms, 160 classes, 42 object properties, 13 individuals.](../examples/fhir/protege/loaded.png
"The Active ontology tab after opening `subjects.ttl`.")](../examples/fhir/protege/loaded.png)

In the Individuals tab a sequence shows where a blank node would, by its node ID: Sue's
`fhir:identifier` and `fhir:name` are `_:seq_…`, the base64url of the list's spelling, until
owlapi-array's Manchester renderer, which Protégé's renderer extends, writes `( … )`.

[![sue:asPatient in the Individuals tab. Its property assertions include fhir:identifier and
fhir:name, each pointing to a term whose name begins with _:seq_.](../examples/fhir/protege/detail-sue-patient.png
"sue:asPatient before reasoning: `fhir:identifier` and `fhir:name` are sequence terms.")](../examples/fhir/protege/sue-patient.png)

## Start the reasoner

Pick **HermiT 1.4.3 (OWL-array)** in the Reasoner menu and start it. The closure is consistent. Sue
is now a "Patient with an observation of rheumatoid arthritis", in yellow:

[![sue:asPatient with the reasoner running. Under Types, fhir:Patient is asserted and 'Patient with
an observation of rheumatoid arthritis' is inferred, highlighted in
yellow.](../examples/fhir/protege/detail-sue-patient-inferred.png
"sue:asPatient with HermiT (OWL-array) running.")](../examples/fhir/protege/sue-patient-inferred.png)

The only evidence is the ICD-10 code M05.9 inside the coding list of Sue's observation. The class
inclusion of §4 makes her CodeableConcept an instance of `sct:239791005`, SNOMED CT's hierarchy
makes the observation one of rheumatoid arthritis, and `fhir:subject` leads to Sue:

[![sue:Obs1 with the reasoner running. Under Types, fhir:Observation is asserted and 'Observation of
Seropositive rheumatoid arthritis' is inferred.](../examples/fhir/protege/detail-sue-obs1-inferred.png
"sue:Obs1, classified from a coding found inside its list.")](../examples/fhir/protege/sue-obs1-inferred.png)

Amy's observation gets three types. Two depend on the shape of the list, not on any one coding:

[![amy:Obs1 with the reasoner running. Under Types, fhir:Observation is asserted, and 'Observation
coded in more than one system', 'Observation of Rheumatoid arthritis' and 'Observation whose primary
coding is SNOMED CT' are inferred.](../examples/fhir/protege/detail-amy-obs1-inferred.png
"amy:Obs1: one type from the concept, two from the list's first element and length.")](../examples/fhir/protege/amy-obs1-inferred.png)

```manchester
# 'Observation whose primary coding is SNOMED CT'
fhir:Observation and fhir:code some (fhir:coding some (ra:first some :Coding-in-SNOMED))

# 'Observation coded in more than one system'
fhir:Observation and fhir:code some (fhir:coding some (ra:length some xsd:integer[>= 2]))
```

## Ask the DL Query tab

Tick **Instances** and type a class expression. Protégé names an entity by its `rdfs:label` and
parses the names it displays, so a SNOMED CT class is typed `'sct:Rheumatoid arthritis (disorder)'`,
not `sct:Rheumatoid_arthritis-disorder`.

### A coding at any position: `ra:member`

[![The DL Query tab with the query fhir:Observation and fhir:code some (fhir:coding some (ra:member
some 'Coding: ICD-10 M05.9, Seropositive rheumatoid arthritis, unspecified')). Instances:
sue:Obs1.](../examples/fhir/protege/detail-query-10-ra-member.png
"Observations with an ICD-10 M05.9 coding anywhere in the list: sue:Obs1.")](../examples/fhir/protege/query-10-ra-member.png)

### The first or the last coding: `ra:first`, `ra:last`

[![The DL Query tab with the query fhir:Observation and fhir:code some (fhir:coding some (ra:first
some 'Coding in SNOMED CT')). Instances: amy:Obs1.](../examples/fhir/protege/detail-query-14-ra-first.png
"First coding in SNOMED CT: amy:Obs1 only. Bob's SNOMED CT coding is second.")](../examples/fhir/protege/query-14-ra-first.png)

[![The DL Query tab with the query fhir:Observation and fhir:code some (fhir:coding some (ra:last
some 'Coding in SNOMED CT')). Instances: amy:Obs2 and bob:Obs1.](../examples/fhir/protege/detail-query-15-ra-last.png
"Last coding in SNOMED CT: amy:Obs2 (LOINC, then SNOMED CT) and bob:Obs1 (ICD-10, then SNOMED CT).")](../examples/fhir/protege/query-15-ra-last.png)

### The length of the list: `ra:length`

[![The DL Query tab with the query 'Observation coded in more than one system'. Instances: amy:Obs1,
amy:Obs2 and bob:Obs1.](../examples/fhir/protege/detail-query-16-several-codings.png
"\"Observation coded in more than one system\", a coding list of length ≥ 2: every observation but Sue's.")](../examples/fhir/protege/query-16-several-codings.png)

### A list inside a list

[![The DL Query tab with the query fhir:Patient and fhir:name some (ra:member some (fhir:given some
(ra:length some xsd:integer[>= 2]))). Instances: sue:asPatient.](../examples/fhir/protege/detail-query-23-ra-length.png
"Patients with a name of at least two given names: sue:asPatient (\"Sue\", \"Ann\").")](../examples/fhir/protege/query-23-ra-length.png)

All 24 queries of the example list in the tab the instances that the OWL API run,
[FhirReasoning.java](../examples/fhir/FhirReasoning.java), finds. A selection; the full table is
[§4 of the example](../examples/fhir/index.html#in-prot-g).

<div class="table-wrap">
<table>
<thead><tr><th>Typed in the DL Query tab</th><th>Instances</th></tr></thead>
<tbody>
<tr><td><code>'Observation of Rheumatoid arthritis'</code></td><td class="ans">amy:Obs1 bob:Obs1 sue:Obs1</td></tr>
<tr><td><code>'Observation of Seronegative rheumatoid arthritis'</code></td><td class="ans">bob:Obs1</td></tr>
<tr><td><code>fhir:Observation and fhir:code some (fhir:coding some (ra:member some 'Coding in ICD-10'))</code></td><td class="ans">amy:Obs1 bob:Obs1 sue:Obs1</td></tr>
<tr><td><code>'Patient with an observation of rheumatoid arthritis'</code></td><td class="ans">amy:asPatient bob:asPatient sue:asPatient</td></tr>
<tr><td><code>fhir:Observation and fhir:code some (fhir:coding some (ra:length value 1))</code></td><td class="ans">sue:Obs1</td></tr>
<tr><td><code>'bp:Observation of blood pressure with a systolic reading of 140 mm[Hg] or more'</code></td><td class="ans">amy:Obs2</td></tr>
<tr><td><code>'bp:Observation of blood pressure with exactly two components'</code></td><td class="ans">amy:Obs2</td></tr>
<tr><td><code>fhir:Observation and fhir:code some (fhir:coding some ra:EmptySequence)</code></td><td class="ans">(none)</td></tr>
</tbody>
</table>
</div>

## Limits, as found

- **No closure over blank nodes.** The closure of §2 is an `ObjectOneOf`, which OWL 2 DL allows over
  named individuals only. Every FHIR element is a blank node, so no FHIR list gets one: `some` over
  members is unaffected, `only` holds where an axiom gives it, but "observations all of whose
  codings are ICD-10" finds nothing where it should find sue:Obs1. Naming the elements inside the
  reasoner's view only would settle it
  ([rdf-array#20](https://github.com/rdf-array/rdf-array/issues/20)).
- **ELK sees no FHIR data.** **ELK 0.6.0 (OWL-array)**, the expansion without the closure that OWL 2
  EL cannot express, answers only the 2 queries whose answer is empty: ELK skips anonymous
  individuals, and every FHIR element is one. The same fix.
- **A sequence is never an answer.** Protégé's query results list named individuals; the
  observations and patients appear, their codings and lists do not
  ([rdf-array#21](https://github.com/rdf-array/rdf-array/issues/21)).
- **`xsd:date` stops HermiT.** FHIR writes dates as `xsd:date`, outside the OWL 2 datatype map, and
  HermiT refuses the literal at load time. The example leaves birth dates out; real FHIR data needs
  them retyped or a reasoner that takes them.
- **Saving round-trips.** arthritis.ttl (OWL's own `owl:unionOf` lists) and subject-sue.ttl (lists
  of blank nodes, nested) save as Turtle and RDF/XML and read back with the same axioms. RDF/XML has
  no spelling for a list holding a literal
  ([rdf-array#18](https://github.com/rdf-array/rdf-array/issues/18)); FHIR has none, since every
  element is a node.
- **The FHIR ontology's generator.** fhir.ttl's `allValuesFrom` on a repeating element types the
  list (§1). The fix is mechanical, `ra:member only` for every element whose maximum cardinality is
  *, and belongs in kindling's `FhirTurtleGenerator`, a [target](../management/repos.html#not-yet-forked).

---

Run on 2026-10-27: Protégé 5.6.9 (platform-independent zip) on Java 21, macOS, with owlapi-array
`1200076f9` and protege-owl-array 0.1.0, both built from source by `assemble.sh`. The stock-parser
measurement of §1: OWL API 4.5.29 from Maven Central, `subject-amy.ttl` loaded through the catalog.
Sources: [examples/fhir](https://github.com/rdf-array/rdf-array/tree/main/examples/fhir) · the
example's [write-up](../examples/fhir/index.html) · [OWL-array](owl-array.html) ·
[protege-owl-array](https://github.com/rdf-array/protege-owl-array) ·
[owlapi-array](https://github.com/rdf-array/owlapi-array).
