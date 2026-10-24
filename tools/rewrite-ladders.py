#!/usr/bin/env python3
"""Fold rdf:first/rdf:rest ladders in test expectations into sequence terms (rdf-array).

    python3 rewrite-ladders.py test/Parser-test.ts

Rewrites, in place, every expectation array `toBeRdfIsomorphic([ ... ])` or
`toEqualRdfQuadArray([ ... ])` whose `DF.quad(...)` entries spell a ladder: the
rdf:first/rdf:rest triples are collected, each head (a node that is never the
object of an rdf:rest) is followed to rdf:nil, every reference to the head is
replaced by `DF.sequence([ ...elements... ])`, a bare rdf:nil object becomes
`DF.sequence([])`, nested ladders resolve recursively, a node with rdf:rest but
no rdf:first contributes no element, and the ladder triples are dropped. A
block that cannot be folded (a comment inside it, an irregular ladder, a
dangling rest) is left alone and reported. Adapt the three regexes below for
another framework; the chain logic is the same. See the array-tests skill.
"""
import re, sys
T=sys.argv[1]
src=open(T,encoding='utf-8').read()
FIRST=re.compile(r"DF\.namedNode\((?:Util\.RDF \+ 'first'|'http://www\.w3\.org/1999/02/22-rdf-syntax-ns#first')\)")
REST=re.compile(r"DF\.namedNode\((?:Util\.RDF \+ 'rest'|'http://www\.w3\.org/1999/02/22-rdf-syntax-ns#rest')\)")
NIL=re.compile(r"DF\.namedNode\((?:Util\.RDF \+ 'nil'|'http://www\.w3\.org/1999/02/22-rdf-syntax-ns#nil')\)")
def split_top(s):
    parts=[];depth=0;cur=[];i=0;q=None
    while i<len(s):
        c=s[i]
        if q:
            cur.append(c)
            if c=='\\': cur.append(s[i+1]); i+=2; continue
            if c==q: q=None
        elif c in '\'"`': q=c; cur.append(c)
        elif c in '([{': depth+=1; cur.append(c)
        elif c in ')]}': depth-=1; cur.append(c)
        elif c==',' and depth==0: parts.append(''.join(cur)); cur=[]
        else: cur.append(c)
        i+=1
    if ''.join(cur).strip(): parts.append(''.join(cur))
    return parts
def find_close(s,i):
    depth=0;q=None;j=i
    while j<len(s):
        c=s[j]
        if q:
            if c=='\\': j+=2; continue
            if c==q: q=None
        elif c in '\'"`': q=c
        elif c in '([{': depth+=1
        elif c in ')]}':
            depth-=1
            if depth==0: return j
        j+=1
    raise ValueError('unbalanced')
norm=lambda e: re.sub(r'\s+',' ',e.strip())
def fmt_seq(elems): return 'DF.sequence([ '+', '.join(elems)+' ])' if elems else 'DF.sequence([])'
out=[];pos=0;blocks=0;changed=0;skipped=[]
for m in re.finditer(r'\.(toBeRdfIsomorphic|toEqualRdfQuadArray)\(\[', src):
    start=m.end()-1; end=find_close(src,start); inner=src[start+1:end]
    if not (FIRST.search(inner) or REST.search(inner) or NIL.search(inner)): continue
    blocks+=1; line_no=src[:start].count('\n')+1
    unquoted=re.sub(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|`(?:\\.|[^`\\])*`", "''", inner)
    if '//' in unquoted or '/*' in unquoted: skipped.append((line_no,'comment inside')); continue
    im=re.match(r'\n(\s*)',inner); ind=im.group(1) if im else '  '
    parsed=[]
    for e in split_top(inner):
        if not e.strip(): continue
        en=norm(e); mm=re.match(r'DF\.quad\((.*)\)$',en,re.S)
        args=[norm(a) for a in split_top(mm.group(1))] if mm else None
        if args and len(args) not in (3,4): args=None
        parsed.append((e,args))
    first={};rest={};ok=True
    for e,args in parsed:
        if not args: continue
        s,p,o=args[0],args[1],args[2]
        if FIRST.fullmatch(p):
            if s in first: ok=False
            first[s]=o
        elif REST.fullmatch(p):
            if s in rest: ok=False
            rest[s]=o
    for s in first:
        if s not in rest: ok=False
    if not ok: skipped.append((line_no,'irregular ladder')); continue
    is_nil=lambda x: NIL.fullmatch(x) is not None
    cache={}
    def resolve(x):
        if is_nil(x): return 'DF.sequence([])'
        if x in rest:
            if x in cache: return cache[x]
            elems=[];node=x;seen=set()
            while True:
                if node in seen: raise ValueError('cycle at '+node)
                seen.add(node)
                if node in first: elems.append(resolve(first[node]))
                nxt=rest.get(node)
                if nxt is None: raise ValueError('dangling '+node)
                if is_nil(nxt): break
                node=nxt
            cache[x]=fmt_seq(elems); return cache[x]
        return x
    try:
        chain_nodes=set(rest)|set(first); new_entries=[]
        for e,args in parsed:
            if args and (FIRST.fullmatch(args[1]) or REST.fullmatch(args[1])) and args[0] in chain_nodes: continue
            if not args: new_entries.append(norm(e)); continue
            nargs=[resolve(a) for a in args]
            new_entries.append(norm(e) if nargs==args else 'DF.quad('+', '.join(nargs)+')')
    except ValueError as ex:
        skipped.append((line_no,str(ex))); continue
    lines=[]
    for ne in new_entries:
        line=ind+ne+','
        if len(line)<=118: lines.append(line); continue
        mm=re.match(r'DF\.quad\((.*)\)$',ne,re.S)
        if not mm: lines.append(line); continue
        lines.append(ind+'DF.quad(')
        for a in [x.strip() for x in split_top(mm.group(1))]:
            l=ind+'  '+a+','
            if len(l)>118 and a.startswith('DF.sequence([ '):
                lines.append(ind+'  DF.sequence([')
                for x in [x.strip() for x in split_top(a[len('DF.sequence(['):-2])]: lines.append(ind+'    '+x+',')
                lines.append(ind+'  ]),')
            else: lines.append(l)
        lines.append(ind+'),')
    out.append(src[pos:start+1]); out.append('\n'+'\n'.join(lines)+'\n'+ind[:-2]); pos=end; changed+=1
out.append(src[pos:])
open(T,'w',encoding='utf-8').write(''.join(out))
print('blocks with ladders:',blocks,'rewritten:',changed,'skipped:',skipped)
