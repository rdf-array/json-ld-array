#!/usr/bin/env python3
"""Turn json-ld-array.md (a small, regular Markdown subset) into a ReSpec HTML document.

    python3 md-to-respec.py json-ld-array.md json-ld-array.html

Handles: the leading H1 (becomes the title), paragraphs, bullet lists with continuation lines,
fenced code blocks (```json / ```turtle / ```sparql), pipe tables with a header row, inline code,
bold, italics and links. Sections come from `##` and `###` headings; a leading "N." / "N.M" is
dropped, ReSpec numbers them, and the text before the first `##` becomes the abstract and an
unnumbered introduction, so "§3.4" references in the prose keep pointing at the right section.
JSON is highlighted by ReSpec's highlight.js; Turtle and SPARQL by a small script of their own.
"""
import html
import re
import sys

INLINE_CODE = re.compile(r'`([^`]+)`')
BOLD = re.compile(r'\*\*(.+?)\*\*')
ITALIC = re.compile(r'(?<![\w*])\*(?!\*)(.+?)(?<!\*)\*(?![\w*])')
LINK = re.compile(r'\[([^\]]+)\]\((https?://[^)]+)\)')
CITE = re.compile(r'\[(RFC) (\d+)( §[^\]]*)?\]')


def inline(text):
    """Inline Markdown to HTML; code spans are protected from the other substitutions."""
    codes = []

    def stash(match):
        codes.append('<code>%s</code>' % html.escape(match.group(1), quote=False))
        return '\0%d\0' % (len(codes) - 1)

    text = INLINE_CODE.sub(stash, text)
    text = html.escape(text, quote=False).replace('&lt;br&gt;', '<br>')
    text = LINK.sub(r'<a href="\2">\1</a>', text)
    text = CITE.sub(lambda m: '[[%s%s]]%s' % (m.group(1), m.group(2), m.group(3) or ''), text)
    text = text.replace('[INFRA]', '[[INFRA]]')
    text = BOLD.sub(r'<strong>\1</strong>', text)
    text = ITALIC.sub(r'<em>\1</em>', text)
    return re.sub('\0(\\d+)\0', lambda m: codes[int(m.group(1))], text)


def slug(text):
    text = re.sub(r'`', '', text)
    text = re.sub(r'[^A-Za-z0-9]+', '-', text).strip('-').lower()
    return text


def split_row(line):
    cells, cur, in_code = [], [], False
    for ch in line.strip().strip('|'):
        if ch == '`':
            in_code = not in_code
        if ch == '|' and not in_code:
            cells.append(''.join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    cells.append(''.join(cur).strip())
    return cells


def convert(md):
    lines = md.split('\n')
    title = None
    out = []            # list of (depth, html) for the body; depth 0 = top
    blocks = []         # the current block list being filled
    sections = []       # stack of (level, id, title, blocks)
    pre_sections = []   # blocks before the first ## (abstract + introduction)
    i = 0

    def flush_para(para):
        if para:
            blocks.append('<p>%s</p>' % inline(' '.join(s.strip() for s in para)))
            para.clear()

    para = []
    current_blocks = pre_sections
    blocks = current_blocks

    while i < len(lines):
        line = lines[i]
        if line.startswith('# ') and title is None:
            title = inline(line[2:].strip())
            i += 1
            continue
        heading = re.match(r'^(##+) (.*)$', line)
        if heading:
            flush_para(para)
            level = len(heading.group(1))
            text = re.sub(r'^\d+(\.\d+)*\.? ', '', heading.group(2)).strip()
            sec_id = slug(text)
            while sections and sections[-1][0] >= level:
                sections.pop()
            parent = sections[-1][3] if sections else None
            new_blocks = []
            entry = (level, sec_id, text, new_blocks)
            if parent is None:
                sections_top.append(entry)
            else:
                parent.append(entry)
            sections.append(entry)
            blocks = new_blocks
            i += 1
            continue
        if line.startswith('```'):
            flush_para(para)
            lang = line[3:].strip() or 'text'
            code = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code.append(lines[i])
                i += 1
            i += 1
            cls = {'json': 'json nohighlight', 'turtle': 'turtle nohighlight', 'sparql': 'sparql nohighlight'}.get(lang, 'nohighlight')
            blocks.append('<pre class="example %s">%s</pre>' % (cls, html.escape('\n'.join(code), quote=False)))
            continue
        if line.startswith('|'):
            flush_para(para)
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append(lines[i])
                i += 1
            header = split_row(rows[0])
            body = [split_row(r) for r in rows[2:]] if len(rows) > 1 and re.match(r'^\|[-| ]+\|$', rows[1]) else [split_row(r) for r in rows[1:]]
            t = ['<table class="simple">', '<thead><tr>%s</tr></thead>' % ''.join('<th>%s</th>' % inline(c) for c in header), '<tbody>']
            for r in body:
                t.append('<tr>%s</tr>' % ''.join('<td>%s</td>' % inline(c) for c in r))
            t.append('</tbody></table>')
            blocks.append('\n'.join(t))
            continue
        if re.match(r'^(\d+\.|-) ', line):
            flush_para(para)
            ordered = line[0].isdigit()
            items = []
            while i < len(lines) and (re.match(r'^(\d+\.|-) ', lines[i]) or (lines[i].startswith('   ') and lines[i].strip())):
                if re.match(r'^(\d+\.|-) ', lines[i]):
                    items.append(re.sub(r'^(\d+\.|-) ', '', lines[i]))
                else:
                    items[-1] += ' ' + lines[i].strip()
                i += 1
            tag = 'ol' if ordered else 'ul'
            blocks.append('<%s>%s</%s>' % (tag, ''.join('<li>%s</li>' % inline(it) for it in items), tag))
            continue
        if not line.strip():
            flush_para(para)
            i += 1
            continue
        para.append(line)
        i += 1
    flush_para(para)
    return title, pre_sections, sections_top


sections_top = []


def render_sections(entries, indent='  '):
    parts = []
    for level, sec_id, text, blocks in entries:
        parts.append('%s<section id="%s">' % (indent, sec_id))
        parts.append('%s<h%d>%s</h%d>' % (indent, level, inline(text), level))
        for b in blocks:
            if isinstance(b, tuple):
                parts.append(render_sections([b], indent + '  '))
            else:
                parts.append(indent + b.replace('\n', '\n' + indent))
        parts.append('%s</section>' % indent)
    return '\n'.join(parts)


TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>%(title_text)s</title>
  <script src="https://www.w3.org/Tools/respec/respec-w3c" class="remove" defer></script>
  <script class="remove">
    var respecConfig = {
      specStatus: "unofficial",
      shortName: "json-ld-array",
      editors: [{ name: "Eric Prud'hommeaux" }],
      edDraftURI: "https://rdf-array.github.io/json-ld-array/",
      latestVersion: null,
      overrideCopyright: "<p class='copyright'>Copyright &copy; 2026 the rdf-array project. This document is licensed under a <a href='https://creativecommons.org/licenses/by/4.0/'>Creative Commons Attribution 4.0 License</a>.</p>",
      lint: { "no-unused-dfns": false },
      localBiblio: {
        "RML-CORE": { title: "RML-Core: Generic Mapping Language for RDF", href: "https://w3id.org/rml/core/spec", publisher: "W3C Knowledge Graph Construction Community Group" },
        "RML-CC": { title: "RML-CC: RML Collections and Containers", href: "https://w3id.org/rml/cc/spec", publisher: "W3C Knowledge Graph Construction Community Group" },
        "RML-LV": { title: "RML-LV: RML Logical Views", href: "https://w3id.org/rml/lv/spec", publisher: "W3C Knowledge Graph Construction Community Group" },
        "RML-FNML": { title: "RML-FNML: RML Functions", href: "https://w3id.org/rml/fnml/spec", publisher: "W3C Knowledge Graph Construction Community Group" },
        "YARRRML": { title: "YARRRML", href: "https://rml.io/yarrrml/spec/", publisher: "IDLab, Ghent University" }
      }
    };
  </script>
  <style>
    table.simple { font-size: 0.9em; }
    table.simple td, table.simple th { vertical-align: top; }
    pre.example { font-size: 0.9em; line-height: 1.35; }
    .hljs-iri { color: #0b5394; }
    .hljs-pname { color: #38761d; }
    .hljs-lit { color: #a61c00; }
    .hljs-kw { color: #741b47; font-weight: bold; }
    .hljs-var { color: #b45f06; }
    .hljs-cmt { color: #777; font-style: italic; }
    .hljs-bnode { color: #666; }
    .hljs-num, .hljs-number { color: #a61c00; }
    .hljs-attr { color: #0b5394; }
    .hljs-string { color: #38761d; }
    .hljs-literal { color: #741b47; }
  </style>
</head>
<body>
  <section id="abstract">
%(abstract)s
  </section>
  <section id="sotd">
    <p>This is a design sketch for the <a href="https://github.com/rdf-array">rdf-array</a> project, generated from <a href="https://github.com/rdf-array/json-ld-array">json-ld-array.md</a> by <code>md-to-respec.py</code>. It is implemented in <a href="https://github.com/rdf-array/jsonld.js-array">jsonld.js-array</a>, which has a <a href="https://rdf-array.github.io/jsonld.js-array/">playground</a>. It is not a W3C document and has no standing anywhere.</p>
  </section>
  <section class="introductory" id="introduction">
    <h2>Introduction</h2>
%(intro)s
  </section>
%(sections)s
  <script>
  // Turtle-array and SPARQL-array highlighting: a few token classes are enough for these examples.
  (function () {
    var token = /(<[^>\\s]*>)|("""[\\s\\S]*?"""|"(?:[^"\\\\]|\\\\.)*")(@[A-Za-z0-9-]+|\\^\\^[^\\s;,.()\\]]+)?|(#[^\\n]*)|(\\?[A-Za-z_][\\w]*)|(_:[A-Za-z0-9_-]+)|(\\b(?:PREFIX|BASE|SELECT|CONSTRUCT|ASK|DESCRIBE|WHERE|DELETE|INSERT|DATA|FILTER|OPTIONAL|UNION|ORDER|BY|GROUP|LIMIT|OFFSET|BIND|VALUES|GRAPH|a)\\b)|(\\b-?\\d+(?:\\.\\d+)?(?:[eE][+-]?\\d+)?\\b)|([A-Za-z][\\w-]*:[\\w#./-]*|[A-Za-z][\\w-]*:)/g;
    function paint(pre) {
      var src = pre.textContent, out = '', last = 0, m;
      token.lastIndex = 0;
      while ((m = token.exec(src))) {
        out += esc(src.slice(last, m.index));
        var cls = m[1] ? 'hljs-iri' : m[2] ? 'hljs-lit' : m[4] ? 'hljs-cmt' : m[5] ? 'hljs-var' : m[6] ? 'hljs-bnode' : m[7] ? 'hljs-kw' : m[8] ? 'hljs-num' : 'hljs-pname';
        out += '<span class="' + cls + '">' + esc(m[0]) + '</span>';
        last = token.lastIndex;
      }
      out += esc(src.slice(last));
      pre.innerHTML = out;
    }
    function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
    var jsonToken = /("(?:[^"\\\\]|\\\\.)*")(\\s*:)?|(-?\\d+(?:\\.\\d+)?(?:[eE][+-]?\\d+)?)|\\b(true|false|null)\\b/g;
    function paintJson(pre) {
      var src = pre.textContent, out = '', last = 0, m;
      jsonToken.lastIndex = 0;
      while ((m = jsonToken.exec(src))) {
        out += esc(src.slice(last, m.index));
        if (m[1]) { out += '<span class="' + (m[2] ? 'hljs-attr' : 'hljs-string') + '">' + esc(m[1]) + '</span>' + esc(m[2] || ''); }
        else if (m[3]) { out += '<span class="hljs-number">' + esc(m[3]) + '</span>'; }
        else { out += '<span class="hljs-literal">' + esc(m[4]) + '</span>'; }
        last = jsonToken.lastIndex;
      }
      out += esc(src.slice(last));
      pre.innerHTML = out;
    }
    function tidyHeader() {
      // An unofficial draft has no published version; ReSpec prints the line anyway.
      document.querySelectorAll('.head dt').forEach(function (dt) {
        if (/^Latest published version/.test(dt.textContent)) { var dd = dt.nextElementSibling; dt.remove(); if (dd && dd.tagName === 'DD') dd.remove(); }
      });
    }
    function run() { tidyHeader(); document.querySelectorAll('pre.turtle, pre.sparql').forEach(paint); document.querySelectorAll('pre.json').forEach(paintJson); }
    if (document.respec && document.respec.ready) { document.respec.ready.then(run); } else { document.addEventListener('DOMContentLoaded', run); }
  })();
  </script>
</body>
</html>
'''


def main(src, dst):
    md = open(src, encoding='utf-8').read()
    title, pre, tops = convert(md)
    # The abstract is the first real paragraph after the italic status note; the rest is the introduction.
    status = pre[0] if pre and pre[0].startswith('<p><em>') else ''
    rest = pre[1:] if status else pre
    abstract = rest[0] if rest else ''
    intro = ([status] if status else []) + rest[1:]
    title_text = re.sub(r'<[^>]+>', '', title or 'JSON-LD-array')
    page = TEMPLATE % {
        'title_text': html.escape(title_text, quote=False),
        'abstract': '    ' + abstract,
        'intro': '\n'.join('    ' + b for b in intro),
        'sections': render_sections(tops),
    }
    open(dst, 'w', encoding='utf-8').write(page)
    print('wrote', dst, 'with', sum(1 for _ in re.finditer('<section ', page)), 'sections')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
