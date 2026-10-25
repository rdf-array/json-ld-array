---
name: readme-manifest
description: Keep this repository's README manifest of the rdf-array organisation's repositories in step with GitHub — add a new fork under its language and primary project with its upstream, elide the -array suffix, keep descriptions and the implementations table in rdf-array.md aligned, and run tools/manifest-check.py to find repositories missing from the README or listed without existing. Use after creating, renaming, forking or deleting an rdf-array repository.
---

# Maintaining the README manifest

The README's "Repositories" section is the organisation's manifest: every repository, grouped by
language, with the project each stack was forked for first and the dependencies forked with it
nested under it. `tools/manifest-check.py` compares it with GitHub.

## The rules of the list

- **Grouping.** One bold bullet per language (Java, JavaScript, Python, then any new one such as
  Rust or C++); under it, one bullet per *primary* project, the one the stack was forked for
  (jena, shex.js, comunica, jsonld.js, PyShEx), with its forked dependencies nested one level
  deeper. A dependency shared by several stacks is listed once, under the first stack that used it,
  with the others named in parentheses: "(also comunica and jsonld.js)". A primary project without
  forked dependencies says so: "No forked dependencies."
- **Names.** The fork's name is shown without its `-array` suffix, linked to the fork; the upstream
  follows in parentheses as `owner/repo`, linked. When the fork's upstream is itself a fork, name
  the original too: "([ericprud/x](…), from [linkml/x](…))".
- **Description.** One line after an em dash: what the fork does for rdf-array, in the present
  tense, naming the term or the construct (`Sequence`, `( … )`, `@list`, the Collection shape
  expression) rather than the project's general purpose; a site or playground URL when there is
  one.
- **Ordering.** Within a stack: the data model and term libraries, then parsers and serializers,
  then query, then results; or simply the order of the stack table in the fork's
  `doc/rdf-array.md`.
- **Test suites** form their own group: each W3C fork, elided like the others, with its `*-contrib`
  sibling named in full on the same bullet (contrib repositories are new, use `main`, and are not forks).
- **This repository** is the host and is not listed; the documents table at the top covers it.

## An entry

```markdown
  - [comunica](https://github.com/rdf-array/comunica-array) ([comunica/comunica](https://github.com/comunica/comunica)) —
    the SPARQL-array engine: sequence patterns with variables, ordering, CONSTRUCT, the result
    formats, Turtle, JSON-LD and RDF/XML sources, remote endpoints.
    - [traqula](https://github.com/rdf-array/traqula-array) ([comunica/traqula](https://github.com/comunica/traqula)) —
      the SPARQL parser, generator and algebra, with a collection as one sequence term.
```

## When a repository changes

1. **Created or forked:** set its GitHub description (`gh repo edit rdf-array/<name> --description
   "rdf-array: …"`) and default branch; add the README entry; add the fork to the implementations
   table in `rdf-array.md` (and regenerate `rdf-array.html`, which the Pages workflow checks); if it
   has a site, the homepage URL. Add it to the session's memory note of the forks. Leave issues off
   on a fork (GitHub's default): its issues go to rdf-array/rdf-array (`fork-array` §8).
2. **Renamed:** GitHub redirects the old name, but update every link in this repository and in the
   forks that point at it (`grep -rn "rdf-array/<old>" ~/checkouts/rdf-array/*/README.md
   ~/checkouts/rdf-array/*/doc/rdf-array.md`), the local checkout directory and its `origin`.
3. **Deleted:** remove the entry; mention the deletion in the commit message.
4. Run the check, then commit as `rdf-array: manifest: <what changed>` and push.

## The check

```bash
python3 tools/manifest-check.py              # repositories missing from or extra in the README
python3 tools/manifest-check.py --upstreams  # also prints each missing one's upstream, for the entry
```

It lists the organisation's repositories with `gh repo list rdf-array`, reads every
`https://github.com/rdf-array/<name>` link in the README, and reports repositories not linked,
links to repositories that do not exist, repositories without a GitHub description, and
descriptions still carrying the old `RDF-:` prefix. It exits non-zero on the first two kinds, so it
can guard a commit. It needs `gh` logged in with the `read:org` scope.

## Other lists to keep in step

- `rdf-array.md`'s implementations table (one row per stack) and `targets.md` when a target
  becomes a fork (move it from the table to "done").
- `html-index.html` and the `pages.yml` check loop when a rendered document is added.
- The fork's own README banner and `doc/rdf-array.md` stack table when it gains a dependency fork.
