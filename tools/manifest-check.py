#!/usr/bin/env python3
"""Compare the README's repository manifest with the rdf-array organisation on GitHub.

    python3 tools/manifest-check.py              # repositories missing from or extra in the README
    python3 tools/manifest-check.py --upstreams  # also print the upstream of each missing one

Reads every https://github.com/rdf-array/<name> link in README.md, lists the organisation's
repositories with `gh repo list`, and reports: repositories not linked from the README, links to
repositories that do not exist, repositories without a GitHub description, and descriptions still
carrying the old "RDF-:" prefix. Exits 1 when a repository is missing or a link is dead.
See the readme-manifest skill.
"""
import json
import pathlib
import re
import subprocess
import sys

README = pathlib.Path(__file__).resolve().parent.parent / 'README.md'
ORG = 'rdf-array'
IGNORE = {'rdf-array'}  # this repository hosts the manifest and is not listed in it


def gh(*args):
    return subprocess.check_output(['gh', *args], text=True)


def main():
    repos = {
        repo['name']: repo
        for repo in json.loads(gh('repo', 'list', ORG, '--limit', '200', '--json',
                                  'name,description,isFork,isArchived'))
    }
    text = README.read_text(encoding='utf-8')
    linked = set(re.findall(r'https://github\.com/' + re.escape(ORG) + r'/([A-Za-z0-9_.-]+)', text))
    missing = sorted(name for name in repos if name not in linked and name not in IGNORE)
    dead = sorted(name for name in linked if name not in repos and name not in IGNORE)
    undescribed = sorted(name for name, repo in repos.items()
                         if not (repo.get('description') or '').strip() and name not in IGNORE)
    old_prefix = sorted(name for name, repo in repos.items()
                        if (repo.get('description') or '').startswith('RDF-'))

    print(f'{len(repos)} repositories in {ORG}, {len(linked - IGNORE)} linked from the README')
    for name in missing:
        line = f'MISSING from the README: {name}'
        if '--upstreams' in sys.argv:
            parent = gh('api', f'repos/{ORG}/{name}', '--jq', '.parent.full_name // "-"').strip()
            line += f'  (upstream {parent})'
        print(line)
    for name in dead:
        print(f'DEAD link in the README: {name}')
    for name in undescribed:
        print(f'no GitHub description: {name}')
    for name in old_prefix:
        print(f'description still says "RDF-:": {name}')
    if not (missing or dead or undescribed or old_prefix):
        print('the manifest is in step with GitHub')
    sys.exit(1 if (missing or dead) else 0)


if __name__ == '__main__':
    main()
