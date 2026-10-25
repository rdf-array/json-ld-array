"""Read SPARQL JSON results (with rdf-array's {"type": "seq"}) into comparable rows."""
import json
import rdfarray as ra


def term(b):
    t = b['type']
    if t == 'uri':
        return ra.iri(b['value'])
    if t == 'bnode':
        return ra.bnode(b['value'])
    if t in ('literal', 'typed-literal'):
        lang = b.get('xml:lang', '')
        dt = b.get('datatype') or ('' if lang else ra.XSD_STRING)
        return ('lit', b['value'], dt, lang.lower(), b.get('its:dir', ''))
    if t == 'seq':
        return ra.seq(term(e) for e in b['value'])
    if t == 'triple':
        v = b['value']
        return ('triple', term(v['subject']), term(v['predicate']), term(v['object']))
    raise ValueError(t)


def rows(text):
    d = json.loads(text)
    if 'boolean' in d:
        return {'boolean': d['boolean']}
    out = []
    for b in d['results']['bindings']:
        out.append(tuple(sorted((k, ra.term_str(term(v))) for k, v in b.items())))
    return {'vars': sorted(d['head'].get('vars', [])), 'rows': out}


def same(a, b, ordered=False):
    """equal result sets; blank node labels are not compared (none of the tests return blank nodes)."""
    ra_, rb = rows(a), rows(b)
    if 'boolean' in ra_ or 'boolean' in rb:
        return ra_ == rb
    if ra_['vars'] != rb['vars']:
        return False
    return ra_['rows'] == rb['rows'] if ordered else sorted(ra_['rows']) == sorted(rb['rows'])
