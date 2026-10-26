#!/usr/bin/env python3
"""Check repos.json, the rdf-array organisation's manifest, against itself, GitHub and the forks.

    python3 tools/manifest-check.py              # all checks (needs gh, with read:org, and checkouts)
    python3 tools/manifest-check.py --offline    # only repos.json itself and the links into repos.html
    python3 tools/manifest-check.py --edges      # also print each repository's derived edges
    python3 tools/manifest-check.py --upstreams  # print the GitHub upstream of each missing repository

repos.json lists every repository, its kind, language, upstream, description and the rdf-array
repositories it depends on ("deps", "scope": "test" for test-only ones); "stack": true marks the
repositories a stack is named for. repos.html renders it. This checks:

- repos.json itself: unique names and anchors, known kinds, deps and contribOf naming known
  repositories, no cycle among runtime deps, and the repos.html#<anchor> links in README.md and
  targets.md resolving to a repository, a stack, a language section or a target;
- GitHub (`gh repo list`): repositories missing from or extra in repos.json, missing descriptions,
  descriptions with the old "RDF-:" prefix, and upstreams that differ from the fork's parent;
- the build files of the checkouts in ~/checkouts/rdf-array (or --root DIR): edges a package.json
  (dependencies, resolutions, overrides, link: paths, scripts), pyproject.toml, Cargo.toml,
  .gitmodules, fetch or update script, workflow or vendored-copy *.commit file shows but repos.json
  lacks (an error), and declared edges no build file shows (listed, unless they carry a "note").

Exits 1 on an error. See the repos-manifest skill.
"""
import json
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = HERE / 'repos.json'
ORG = 'rdf-array'
KINDS = {'implementation', 'test-suite', 'contrib', 'tool', 'meta'}
SECTIONS = {'test-suites', 'java', 'javascript', 'python', 'rust', 'meta', 'not-yet-forked',
            'issues', 'cross-repo', 'spec', 'unfiled'}


def gh(*args):
    return subprocess.check_output(['gh', *args], text=True)


# --- repos.json itself ------------------------------------------------------------------------

def check_manifest(doc, errors):
    repos = doc['repos']
    names = [r['name'] for r in repos]
    by_name = {r['name']: r for r in repos}
    for n in sorted({n for n in names if names.count(n) > 1}):
        errors.append(f'duplicate repository: {n}')
    anchors = [r['anchor'] for r in repos] + [t['anchor'] for t in doc.get('targets', [])]
    for a in sorted({a for a in anchors if anchors.count(a) > 1}):
        errors.append(f'duplicate anchor: {a}')
    for r in repos:
        if r.get('kind') not in KINDS:
            errors.append(f'{r["name"]}: unknown kind {r.get("kind")!r}')
        if r.get('stack') and r.get('kind') != 'implementation':
            errors.append(f'{r["name"]}: a stack must be an implementation')
        if r.get('contribOf') and r['contribOf'] not in by_name:
            errors.append(f'{r["name"]}: contribOf names an unknown repository {r["contribOf"]}')
        for d in r.get('deps', []):
            if d['repo'] not in by_name:
                errors.append(f'{r["name"]}: depends on an unknown repository {d["repo"]}')
    # no cycle among runtime deps
    state = {}

    def visit(n, path):
        if state.get(n) == 'done':
            return
        if state.get(n) == 'open':
            errors.append('runtime dependency cycle: ' + ' -> '.join(path + [n]))
            return
        state[n] = 'open'
        for d in by_name[n].get('deps', []):
            if d.get('scope') != 'test' and d['repo'] in by_name:
                visit(d['repo'], path + [n])
        state[n] = 'done'

    for n in by_name:
        visit(n, [])
    return by_name


def check_links(doc, errors):
    ids = {r['anchor'] for r in doc['repos']} | {t['anchor'] for t in doc.get('targets', [])} | SECTIONS
    for f in ('README.md', 'targets.md', 'html-index.html'):
        p = HERE / f
        if p.exists():
            for a in re.findall(r'repos\.html#([A-Za-z0-9_-]+)', p.read_text(encoding='utf-8')):
                if a not in ids:
                    errors.append(f'{f}: repos.html#{a} names no repository, stack, section or target')


# --- GitHub ----------------------------------------------------------------------------------

def check_github(by_name, errors, notes):
    listed = {r['name']: r for r in json.loads(gh('repo', 'list', ORG, '--limit', '200', '--json',
                                                   'name,description,parent'))}
    for n in sorted(set(listed) - set(by_name)):
        line = f'MISSING from repos.json: {n}'
        if '--upstreams' in sys.argv:
            parent = listed[n].get('parent') or {}
            line += f'  (upstream {parent.get("owner", {}).get("login", "-")}/{parent.get("name", "-")})'
        errors.append(line)
    for n in sorted(set(by_name) - set(listed)):
        errors.append(f'in repos.json but not on GitHub: {n}')
    for n, g in sorted(listed.items()):
        desc = (g.get('description') or '').strip()
        if not desc:
            notes.append(f'no GitHub description: {n}')
        elif desc.startswith('RDF-'):
            notes.append(f'description still says "RDF-:": {n}')
        parent = g.get('parent') or {}
        parent = f'{parent["owner"]["login"]}/{parent["name"]}' if parent.get('name') else None
        mine = by_name.get(n, {}).get('upstream')
        if parent and mine and parent.lower() not in (mine.lower(), (by_name[n].get('upstreamFrom') or '').lower()):
            notes.append(f'{n}: repos.json says upstream {mine}, GitHub says fork of {parent}')


# --- build files -----------------------------------------------------------------------------

def derive_edges(root, names):
    """The rdf-array repositories each checkout's build files point at: {repo: {dep: scope}}."""
    lower = {n.lower(): n for n in names}

    def ref(s):
        m = re.search(r'github\.com[/:]rdf-array/([\w.-]+?)(?:\.git)?(?:[#/@?"\s]|$)', s) \
            or re.search(r'github:rdf-array/([\w.-]+?)(?:#|"|$)', s)
        if m:
            return lower.get(m.group(1).lower())
        m = re.search(r'(?:link:|file:|path\s*=\s*")\.\./+([\w.-]+)', s)
        return lower.get(m.group(1).lower()) if m else None

    out, absent = {}, []
    for repo in sorted(names):
        d = root / repo
        if not (d / '.git').exists():
            absent.append(repo)
            continue
        files = subprocess.run(['git', '-C', str(d), 'ls-files'], capture_output=True, text=True).stdout.split('\n')
        edges = {}

        def add(dep, scope):
            if dep and dep != repo:
                edges[dep] = 'runtime' if 'runtime' in (scope, edges.get(dep)) else 'test'

        for f in files:
            if not f or 'node_modules/' in f:
                continue
            p, b = d / f, os.path.basename(f)
            try:
                if b == 'package.json':
                    pj = json.loads(p.read_text(encoding='utf-8'))
                    for spec in (pj.get('scripts') or {}).values():
                        for m in re.finditer(r'github\.com/rdf-array/[\w.-]+', str(spec)):
                            add(ref(m.group(0) + ' '), 'test')
                    for sec, scope in [('dependencies', 'runtime'), ('peerDependencies', 'runtime'),
                                       ('optionalDependencies', 'runtime'), ('resolutions', 'runtime'),
                                       ('overrides', 'runtime'), ('devDependencies', 'test')]:
                        for spec in (pj.get(sec) or {}).values():
                            if isinstance(spec, str):
                                add(ref(spec), scope)
                elif b in ('pyproject.toml', 'Cargo.toml'):
                    for line in p.read_text(encoding='utf-8', errors='replace').split('\n'):
                        if 'rdf-array/' in line or '../' in line:
                            add(ref(line), 'runtime')
                elif b == '.gitmodules':
                    for line in p.read_text(encoding='utf-8').split('\n'):
                        if 'url' in line:
                            add(ref(line), 'test')
                elif b.endswith('.commit') and b[:-7].lower() in lower:
                    add(lower[b[:-7].lower()], 'test')  # a vendored copy of a suite
                elif b.endswith(('.sh', '.yml', '.yaml')) and ('script' in f or '.github/workflows' in f
                                                              or b.startswith(('fetch', 'update'))):
                    for line in p.read_text(encoding='utf-8', errors='replace').split('\n'):
                        if 'rdf-array/' in line:
                            add(ref(line), 'test')
            except (OSError, ValueError):
                continue
        out[repo] = edges
    return out, absent


def check_builds(by_name, root, errors, notes):
    derived, absent = derive_edges(root, list(by_name))
    for repo in absent:
        if by_name[repo]['kind'] != 'meta':
            notes.append(f'no checkout of {repo} in {root}: its edges were not checked')
    for repo, edges in derived.items():
        declared = {d['repo']: d for d in by_name[repo].get('deps', [])}
        for dep, scope in sorted(edges.items()):
            if dep not in declared:
                errors.append(f'{repo}: its build files depend on {dep} ({scope}); repos.json does not')
            elif (declared[dep].get('scope') == 'test') != (scope == 'test'):
                notes.append(f'{repo} -> {dep}: repos.json says {declared[dep].get("scope", "runtime")}, '
                             f'the build files say {scope}')
        for dep, d in sorted(declared.items()):
            if dep not in edges and not d.get('note'):
                notes.append(f'{repo} -> {dep}: declared, but no build file shows it (add a "note")')
        if '--edges' in sys.argv and edges:
            print(f'  {repo} -> ' + ', '.join(dep + ('' if s == 'runtime' else ' [test]')
                                             for dep, s in sorted(edges.items())))


def main():
    doc = json.loads(MANIFEST.read_text(encoding='utf-8'))
    errors, notes = [], []
    by_name = check_manifest(doc, errors)
    check_links(doc, errors)
    if '--offline' not in sys.argv:
        check_github(by_name, errors, notes)
        root = pathlib.Path(sys.argv[sys.argv.index('--root') + 1]) if '--root' in sys.argv \
            else pathlib.Path.home() / 'checkouts' / ORG
        check_builds(by_name, root, errors, notes)
    print(f'{len(by_name)} repositories in repos.json, '
          f'{sum(1 for r in by_name.values() if r.get("stack"))} stacks, {len(doc.get("targets", []))} targets')
    for e in errors:
        print('ERROR ' + e)
    for n in notes:
        print('note  ' + n)
    if not errors:
        print('repos.json is in step' + (' (offline checks only)' if '--offline' in sys.argv else
                                         ' with GitHub and the build files'))
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
