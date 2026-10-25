#!/usr/bin/env python3
"""N-Triples-array / N-Quads-array in a few hundred lines, for rewriting test suites.

    python3 rdfarray.py fold [--json-ld] [--holes] IN.nq [OUT.nq]   fold rdf:first/rdf:rest ladders into sequences
    python3 rdfarray.py iso A.nq B.nq                      exit 0 when the two are isomorphic
    python3 rdfarray.py canon IN.nq                        print sorted, re-serialized quads

Terms: IRIs <...>, blank nodes _:x, literals "..."(@lang(--dir)? | ^^<dt>)?, triple terms
<<( s p o )>> (and the older << s p o >>), and sequences ( t1 t2 ... ), nested, () empty.

Folding (see the w3c-test-suites skill): a *ladder cell* is a blank node with exactly one
rdf:first and one rdf:rest (and at most an rdf:type rdf:List), in one graph, used as an object
exactly once. A chain of cells from a head to rdf:nil becomes one sequence; the head's single use
(or, in Turtle mode, its use as a subject) is replaced by the sequence, and the cells' triples go.
JSON-LD mode follows JSON-LD 1.1's fromRdf well-formedness exactly (the head must be used once, as
an object, and carry nothing but first/rest/type), so a partial ladder folds only its well-formed
tail, as the JSON-LD algorithms do. A bare rdf:nil object or subject becomes (), except in
JSON-LD mode where rdf:nil is folded only as the end of a chain or as an object.
"""
import re
import sys
from collections import defaultdict

RDF = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
FIRST, REST, NIL, TYPE, LIST = RDF + 'first', RDF + 'rest', RDF + 'nil', RDF + 'type', RDF + 'List'
XSD_STRING = 'http://www.w3.org/2001/XMLSchema#string'


# ---- terms: tuples, hashable ----
# ('iri', v) ('bnode', label) ('lit', lexical, datatype, lang, dir) ('triple', s, p, o) ('seq', (t...))
def iri(v): return ('iri', v)


def bnode(v): return ('bnode', v)


def seq(elements): return ('seq', tuple(elements))


NIL_T = iri(NIL)
EMPTY = seq(())


def escape(s):
    return (s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r'))


def term_str(t):
    kind = t[0]
    if kind == 'iri':
        return f'<{t[1]}>'
    if kind == 'bnode':
        return f'_:{t[1]}'
    if kind == 'lit':
        _, lex, dt, lang, direction = t
        s = f'"{escape(lex)}"'
        if lang:
            return s + '@' + lang + (f'--{direction}' if direction else '')
        if dt and dt != XSD_STRING:
            return s + f'^^<{dt}>'
        return s
    if kind == 'triple':
        return f'<<( {term_str(t[1])} {term_str(t[2])} {term_str(t[3])} )>>'
    if kind == 'seq':
        return '(' + ' '.join(term_str(e) for e in t[1]) + ')' if t[1] else '()'
    raise ValueError(t)


def quad_str(q):
    s, p, o, g = q
    return f'{term_str(s)} {term_str(p)} {term_str(o)}' + (f' {term_str(g)}' if g else '') + ' .'


# ---- parsing N-Triples-array / N-Quads-array ----
ECHAR = {'t': '\t', 'b': '\b', 'n': '\n', 'r': '\r', 'f': '\f', '"': '"', "'": "'", '\\': '\\'}


class Parser:
    def __init__(self, text):
        self.s = text
        self.i = 0

    def ws(self):
        while self.i < len(self.s):
            c = self.s[self.i]
            if c in ' \t\r\n':
                self.i += 1
            elif c == '#':
                while self.i < len(self.s) and self.s[self.i] not in '\r\n':
                    self.i += 1
            else:
                break

    def unescape(self, raw):
        out, j = [], 0
        while j < len(raw):
            c = raw[j]
            if c == '\\':
                n = raw[j + 1]
                if n == 'u':
                    out.append(chr(int(raw[j + 2:j + 6], 16))); j += 6; continue
                if n == 'U':
                    out.append(chr(int(raw[j + 2:j + 10], 16))); j += 10; continue
                out.append(ECHAR[n]); j += 2; continue
            out.append(c); j += 1
        return ''.join(out)

    def term(self):
        self.ws()
        s, i = self.s, self.i
        if s.startswith('<<(', i):
            self.i += 3
            a, b, c = self.term(), self.term(), self.term()
            self.ws(); assert s.startswith(')>>', self.i), s[self.i:self.i + 20]; self.i += 3
            return ('triple', a, b, c)
        if s.startswith('<<', i):
            self.i += 2
            a, b, c = self.term(), self.term(), self.term()
            self.ws(); assert s.startswith('>>', self.i); self.i += 2
            return ('triple', a, b, c)
        if s[i] == '<':
            j = s.index('>', i)
            self.i = j + 1
            return iri(self.unescape(s[i + 1:j]))
        if s.startswith('_:', i):
            m = re.compile(r'_:([A-Za-z0-9_\-.\u00B7-\uFFFF]*[A-Za-z0-9_\-\u00B7-\uFFFF])').match(s, i)
            self.i = m.end()
            return bnode(m.group(1))
        if s[i] == '(':
            self.i += 1
            elements = []
            while True:
                self.ws()
                if s[self.i] == ')':
                    self.i += 1
                    return seq(elements)
                elements.append(self.term())
        if s[i] == '"':
            j = i + 1
            while s[j] != '"':
                j += 2 if s[j] == '\\' else 1
            lex = self.unescape(s[i + 1:j])
            self.i = j + 1
            if s.startswith('^^', self.i):
                self.i += 2
                dt = self.term()[1]
                return ('lit', lex, dt, '', '')
            if s.startswith('@', self.i):
                m = re.compile(r'@([A-Za-z]+(?:-[A-Za-z0-9]+)*)(?:--(ltr|rtl))?').match(s, self.i)
                self.i = m.end()
                return ('lit', lex, '', m.group(1).lower(), m.group(2) or '')
            return ('lit', lex, XSD_STRING, '', '')
        raise ValueError(f'unexpected at {i}: {s[i:i + 40]!r}')

    def quads(self):
        out = []
        while True:
            self.ws()
            if self.i >= len(self.s):
                return out
            a, b, c = self.term(), self.term(), self.term()
            self.ws()
            g = None
            if self.s[self.i] != '.':
                g = self.term(); self.ws()
            assert self.s[self.i] == '.', self.s[self.i:self.i + 30]
            self.i += 1
            out.append((a, b, c, g))


def parse(text):
    return Parser(text).quads()


def read(path):
    with open(path, encoding='utf-8') as f:
        return parse(f.read())


def write(quads):
    return ''.join(quad_str(q) + '\n' for q in quads)


# ---- folding ----
def fold(quads, json_ld=False, holes=False):
    """Fold rdf:first/rdf:rest ladders into sequence terms; uses are counted per graph.

    A *cell* is a blank node with one rdf:rest, one rdf:first (none when ``holes``: JSON-LD
    toRdf's trace of a list value that converted to nothing) and at most an rdf:type rdf:List. A
    *tail* cell has nothing else, is not used inside a triple term or as a graph name, and is used
    exactly once, as the object of the previous cell's rdf:rest. A *head* starts a chain of tails ending in
    rdf:nil and is not itself the tail of an acceptable head (so the longest chain wins). In JSON-LD
    mode a head is held to JSON-LD 1.1 fromRdf's well-formedness too (nothing else, used exactly
    once in the whole dataset, as an object), so a partial ladder folds only from its first
    well-formed cell; otherwise
    (Turtle, TriG, RDF/XML) a head may carry other triples (a sequence as subject) and be used
    several times (RDF/XML reification repeats it).
    """
    quads = list(dict.fromkeys(quads))  # a dataset is a set: duplicate lines are one quad
    subj, objuse, nested = defaultdict(list), defaultdict(list), set()

    def note_nested(t, g):
        if t[0] == 'bnode':
            nested.add((t, g))
        elif t[0] == 'triple':
            for x in t[1:]:
                note_nested(x, g)
        elif t[0] == 'seq':
            for x in t[1]:
                note_nested(x, g)

    for idx, (s, p, o, g) in enumerate(quads):
        subj[(s, g)].append(idx)
        if o[0] == 'bnode':
            objuse[o].append(idx)  # blank nodes are dataset-wide: uses count across graphs
        else:
            note_nested(o, g)
        if s[0] != 'bnode':
            note_nested(s, g)
        if g is not None and g[0] == 'bnode':
            for gg in {q[3] for q in quads}:
                nested.add((g, gg))

    def cell(b, g):
        if b[0] != 'bnode':
            return None
        idxs = subj.get((b, g), [])
        firsts = [i for i in idxs if quads[i][1] == iri(FIRST)]
        rests = [i for i in idxs if quads[i][1] == iri(REST)]
        types = [i for i in idxs if quads[i][1] == iri(TYPE) and quads[i][2] == iri(LIST)]
        others = [i for i in idxs if i not in firsts and i not in rests and i not in types]
        if len(rests) != 1 or len(firsts) > 1 or (not firsts and not holes):
            return None
        return {'first': quads[firsts[0]][2] if firsts else None, 'rest': quads[rests[0]][2],
                'own': firsts + rests + types, 'others': others}

    def tail_ok(b, g):
        c = cell(b, g)
        us = objuse.get(b, [])
        return (bool(c) and not c['others'] and (b, g) not in nested and len(us) == 1
                and quads[us[0]][1] == iri(REST) and quads[us[0]][3] == g)

    memo = {}

    def chain(b, g, seen=frozenset()):
        """(elements, cells) of the chain starting at cell b, or None."""
        if (b, g) in memo:
            return memo[(b, g)]
        if b in seen:
            return None
        c = cell(b, g)
        if c is None:
            return None
        if c['rest'] == NIL_T:
            rest = ((), (b,))
        elif tail_ok(c['rest'], g):
            sub = chain(c['rest'], g, seen | {b})
            if sub is None:
                return None
            rest = (sub[0], (b,) + sub[1])
        else:
            return None
        result = (((c['first'],) if c['first'] is not None else ()) + rest[0], rest[1])
        memo[(b, g)] = result
        return result

    def head_ok(b, g):
        c = cell(b, g)
        if c is None or chain(b, g) is None:
            return False
        if json_ld:
            us = objuse.get(b, [])
            return not c['others'] and len(us) == 1 and (b, g) not in nested
        return True

    replacement, removed = {}, set()
    for (b, g) in list(subj):
        if not head_ok(b, g):
            continue
        # not the tail of a longer acceptable chain
        if any(quads[i][1] == iri(REST) and head_ok(quads[i][0], g) and tail_ok(b, g)
               for i in objuse.get(b, []) if quads[i][3] == g):
            continue
        elements, cells = chain(b, g)
        replacement[(b, g)] = elements
        for cb in cells:
            removed.update(cell(cb, g)['own'])

    def resolve(t, g):
        if (t, g) in replacement:
            return seq(resolve(e, g) for e in replacement[(t, g)])
        if t == NIL_T:
            return EMPTY
        return t

    def sub(t, g, pos):
        if (t, g) in replacement:
            return resolve(t, g)
        if t == NIL_T and (pos == 'o' or (pos == 's' and not json_ld)):
            return EMPTY
        if t[0] == 'triple':
            return ('triple', sub(t[1], g, 'x'), t[2], sub(t[3], g, 'x'))
        if t[0] == 'seq':
            return seq(sub(e, g, 'x') for e in t[1])
        return t

    out = []
    for idx, (s, p, o, g) in enumerate(quads):
        if idx in removed:
            continue
        out.append((sub(s, g, 's'), p, sub(o, g, 'o'), g))
    return out


# ---- isomorphism, with blank nodes anywhere (inside sequences and triple terms) ----
def bnodes_in(t, acc):
    if t is None:
        return
    if t[0] == 'bnode':
        acc.add(t)
    elif t[0] == 'triple':
        for x in t[1:]:
            bnodes_in(x, acc)
    elif t[0] == 'seq':
        for x in t[1]:
            bnodes_in(x, acc)


def relabel(t, m):
    if t is None:
        return None
    if t[0] == 'bnode':
        return m.get(t, t)
    if t[0] == 'triple':
        return ('triple',) + tuple(relabel(x, m) for x in t[1:])
    if t[0] == 'seq':
        return seq(relabel(x, m) for x in t[1])
    return t


def isomorphic(a, b):
    A, B = set(a), set(b)
    if len(A) != len(B):
        return False
    ba, bb = set(), set()
    for q in A:
        for t in q:
            bnodes_in(t, ba)
    for q in B:
        for t in q:
            bnodes_in(t, bb)
    if len(ba) != len(bb):
        return False
    if not ba:
        return A == B

    def colours(Q, bns):
        col = {x: 0 for x in bns}
        for _ in range(len(bns) + 1):
            sig = defaultdict(list)
            for q in Q:
                for x in bns:
                    shape = []
                    for pos, t in enumerate(q):
                        acc = set()
                        bnodes_in(t, acc)
                        if x in acc:
                            shape.append((pos, term_str(relabel(t, {y: bnode(f'c{col[y]}') for y in acc}))))
                    if shape:
                        others = tuple(term_str(relabel(t, {y: bnode(f'c{col[y]}') for y in bns})) if t else '' for t in q)
                        sig[x].append((tuple(shape), others))
            new = {x: hash((col[x], tuple(sorted(sig[x])))) for x in bns}
            if len(set(new.values())) == len(set(col.values())):
                col = new
                break
            col = new
        return col

    ca, cb = colours(A, ba), colours(B, bb)
    if sorted(ca.values()) != sorted(cb.values()):
        return False
    xs = sorted(ba, key=lambda x: (ca[x], x))
    cands = {x: [y for y in bb if cb[y] == ca[x]] for x in xs}

    def search(i, m, used):
        if i == len(xs):
            return {tuple(relabel(t, m) for t in q) for q in A} == B
        for y in cands[xs[i]]:
            if y not in used:
                m[xs[i]] = y
                if search(i + 1, m, used | {y}):
                    return True
                del m[xs[i]]
        return False

    return search(0, {}, frozenset())


def main(argv):
    cmd = argv[1]
    if cmd == 'fold':
        json_ld = '--json-ld' in argv
        holes = '--holes' in argv
        args = [a for a in argv[2:] if not a.startswith('--')]
        out = write(fold(read(args[0]), json_ld=json_ld, holes=holes))
        if len(args) > 1:
            open(args[1], 'w', encoding='utf-8').write(out)
        else:
            sys.stdout.write(out)
    elif cmd == 'iso':
        ok = isomorphic(read(argv[2]), read(argv[3]))
        print('isomorphic' if ok else 'NOT isomorphic')
        sys.exit(0 if ok else 1)
    elif cmd == 'canon':
        sys.stdout.write(''.join(sorted(quad_str(q) + '\n' for q in read(argv[2]))))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main(sys.argv)
