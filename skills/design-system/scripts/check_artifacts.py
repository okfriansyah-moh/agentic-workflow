#!/usr/bin/env python3
"""Read-only structural checks for requirements-based design packages (stdlib only)."""
from __future__ import annotations

import argparse
import importlib.util
import os
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

LAYERS = ('primitive', 'semantic', 'component')
IMAGES = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'}
VISUALS = IMAGES | {'.mp4', '.webm', '.mov'}
PLATFORMS = {'web', 'mobile', 'desktop', 'console', 'unspecified'}
PRODUCT_TYPES = {'application', 'game', 'unspecified'}


def output_wording_errors(paths):
    """Use the shared final-output check; a missing checker is a failure."""
    helper = Path(os.environ.get('PERSONAL_WORDING_CHECKER', str(Path(__file__).resolve().parents[3] / 'resources' / 'wording' / 'check_output_wording.py')))
    if not helper.is_file():
        return ['Output wording checker missing; validate with the shared personal checker before delivery.']
    spec = importlib.util.spec_from_file_location('personal_output_wording', helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    findings, errors = module.scan_paths(paths)
    return ['Output wording: '+message for message in findings+errors]


class Page(HTMLParser):
    def __init__(self, text: str, markdown=False):
        super().__init__()
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.ancestors: dict[str, set[str]] = {}
        self.stack: list[tuple[str, str | None]] = []
        self.links: list[str] = []
        self.resources: list[str] = []
        self.styles: list[str] = []
        self.targets: set[str] = set()
        self.inline_css: list[str] = []
        self.in_style = False
        if markdown:
            text = re.sub(r'^\s*(`{3,}|~{3,}).*?^\s*\1[^\n]*$', '', text, flags=re.M | re.S)
            text = re.sub(r'`[^`\n]*`', '', text)
        self.text = text
        self.feed(text)
        self.explicit_ids = set(self.ids)
        if markdown:
            slugs = {}
            for heading in re.findall(r"^ {0,3}#{1,6}\s+(.+?)(?:\s+#+)?\s*$", text, re.M):
                slug = re.sub(r"[^\w\s-]", "", heading.lower()).strip().replace(" ", "-")
                count = slugs.get(slug, 0)
                slugs[slug] = count + 1
                self.ids.add(slug + (f"-{count}" if count else ""))
            # Inline Markdown paths, including angle-quoted paths with spaces.
            for match in re.finditer(r'(!?)\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+"[^"\n]*")?\s*\)', text):
                (self.resources if match[1] else self.links).append(match[2] or match[3])
            definitions = dict(re.findall(r'^\s*\[([^\]]+)\]:\s*<?([^\s>]+)>?', text, re.M))
            for match in re.finditer(r'(!?)\[([^\]]+)\]\[([^\]]*)\]', text):
                key = match[3] or match[2]
                if key in definitions:
                    (self.resources if match[1] else self.links).append(definitions[key])

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'style':
            self.in_style = True
        if a.get('style'):
            self.inline_css.append(a['style'])
        if a.get('id'):
            if a['id'] in self.ids:
                self.duplicate_ids.add(a['id'])
            self.ancestors[a['id']] = {identity for _, identity in self.stack if identity}
            self.ids.add(a['id'])
        if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            self.stack.append((tag, a.get('id')))
        if a.get('data-design-target'):
            self.targets.add(a['data-design-target'])
        if tag == 'a' and a.get('href'):
            self.links.append(a['href'])
        if tag in {'img', 'script', 'source', 'video', 'audio'} and a.get('src'):
            self.resources.append(a['src'])
        if tag == 'link' and a.get('href'):
            self.resources.append(a['href'])
            if 'stylesheet' in a.get('rel', '').split():
                self.styles.append(a['href'])

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                self.stack = self.stack[:index]
                break
        if tag == 'style':
            self.in_style = False

    def handle_data(self, data):
        if self.in_style:
            self.inline_css.append(data)

    def section(self, anchor: str) -> str:
        match = re.search(r'<[^>]+\bid\s*=\s*[\"\']' + re.escape(anchor) + r'[\"\'][^>]*>', self.text)
        if not match:
            return ''
        start = match.end()
        end = re.search(r'<[^>]+\bid\s*=|^#{1,6}\s', self.text[start:], re.M)
        # A heading immediately following an explicit anchor belongs to this section.
        rest = self.text[start:]
        heading = re.match(r'\s*(?:</a>\s*)?#{1,6}\s[^\n]*\n', rest)
        if heading:
            start += heading.end()
            rest = self.text[start:]
            end = re.search(r'<[^>]+\bid\s*=|^#{1,6}\s', rest, re.M)
        content = rest[:end.start()] if end else rest
        return (heading[0] if heading else '') + content


def strings(value, nonempty=False):
    return isinstance(value, list) and (bool(value) or not nonempty) and all(isinstance(x, str) and bool(x) for x in value)


def check(root: Path, prd: Path, layout: str = 'auto') -> list[str]:
    # Preserve the public check(root, prd) API; prd can now be a PRD, GDD, or brief.
    root, prd = root.resolve(), prd.resolve()
    errors: list[str] = output_wording_errors([root])
    if layout not in {'auto', 'standard', 'legacy'}:
        return [f'Unsupported layout: {layout}']
    standard = layout == 'standard' or (layout == 'auto' and (root / 'mockup').is_dir())
    preview = root / 'mockup' if standard else root

    def require(ok, message):
        if not ok:
            errors.append(message)
        return bool(ok)

    def inside(path):
        return path == root or root in path.parents

    def artifact(path):
        return inside(path.resolve()) and path.is_file() and path.stat().st_size > 0

    for name in ['design-system.md', 'tokens.json', 'coverage.json'] + ([] if standard else ['verification.md']):
        require(artifact(root / name), f'Missing/empty artifact: {name}')
    if errors:
        return errors
    if standard:
        spec = (root / 'design-system.md').read_text()
        section = re.search(r'^## Validation and handoff[^\n]*\n(.*?)(?=^## |\Z)', spec, re.M | re.S)
        require(bool(section and re.search(r'[A-Za-z0-9]', re.sub(r'^#+[^\n]*', '', section[1], flags=re.M))),
                'Standard specification needs substantive consolidated ## Validation and handoff content.')
        for path in root.rglob('*'):
            if path.is_file() and path.suffix.lower() in VISUALS | {'.html', '.css', '.js', '.mjs', '.woff', '.woff2', '.ttf', '.otf'}:
                require(preview in path.resolve().parents, f'Mockup resource must be under mockup/: {path.relative_to(root)}')
    if not prd.is_file():
        return [f'Source does not exist: {prd}']
    source_bytes = prd.read_bytes()
    source_text = source_bytes.decode('utf-8')
    try:
        coverage = json.loads((root / 'coverage.json').read_text())
        tokens = json.loads((root / 'tokens.json').read_text())
    except (ValueError, UnicodeError) as e:
        return [f'Invalid JSON: {e}']
    if not isinstance(coverage, dict) or not isinstance(tokens, dict):
        return ['coverage.json and tokens.json must contain JSON objects.']
    version = coverage.get('schema_version', 1)
    if not require(type(version) is int and version in {1, 2}, 'Unsupported coverage schema_version.'):
        return errors
    legacy = version == 1
    source = coverage.get('source', {})
    if not isinstance(source, dict):
        return ['coverage.source must be an object.']
    require(isinstance(source.get('path'), str) and (root / source.get('path', '')).resolve() == prd,
            'coverage source.path must identify the supplied source.')
    require(source.get('sha256') == hashlib.sha256(source_bytes).hexdigest(), 'Source digest differs; refresh coverage against current source.')
    cited_sources = {prd}
    supporting = source.get('supporting_documents', [])
    if not isinstance(supporting, list):
        errors.append('source.supporting_documents must be an array.')
        supporting = []
    for doc in supporting:
        if not isinstance(doc, dict) or not isinstance(doc.get('path'), str):
            errors.append('Each supporting source needs path and sha256.')
            continue
        path = (root / doc['path']).resolve()
        require(path.is_file(), f'Supporting source missing: {doc["path"]}')
        if path.is_file():
            require(doc.get('sha256') == hashlib.sha256(path.read_bytes()).hexdigest(), f'Supporting source digest differs: {doc["path"]}')
            cited_sources.add(path)

    def source_ids(key, prefix, needed=False):
        rows = set(re.findall(r'^\|\s*(' + prefix + r'-\d{3})\s*\|', source_text, re.M))
        explicit = source.get(key)
        if explicit is None:
            require(bool(rows) or not needed, f'Source has no {prefix} definition rows; provide source.{key} excerpt mappings.')
            return rows
        if not require(isinstance(explicit, dict), f'source.{key} must map IDs to source excerpts.'):
            return set()
        for rid, excerpt in explicit.items():
            require(isinstance(rid, str) and bool(re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', rid)), f'Invalid source ID: {rid}')
            require(isinstance(excerpt, str) and bool(excerpt.strip()) and excerpt in source_text,
                    f'Source excerpt missing for {rid}.')
        require(not rows or set(explicit) == rows, f'source.{key} must match all {prefix} definition rows.')
        require(bool(explicit) or not needed, f'source.{key} cannot be empty.')
        return set(explicit)

    frs = source_ids('requirements', 'FR', True)
    acs = source_ids('acceptance', 'AC')
    nfrs = source_ids('quality_requirements', 'NFR')
    target_map = {}
    if not legacy:
        targets = coverage.get('targets')
        if not isinstance(targets, list):
            return errors + ['coverage.targets must be an array.']
        require(bool(targets), 'Declare at least one target, using unspecified when unresolved.')
        for target in targets:
            if not isinstance(target, dict) or not isinstance(target.get('id'), str):
                errors.append('Each target needs a string id.')
                continue
            tid = target['id']
            require(bool(re.fullmatch(r'[a-z][a-z0-9-]*', tid)) and tid not in target_map, f'Invalid/duplicate target: {tid}')
            require(target.get('platform') in PLATFORMS and target.get('product_type') in PRODUCT_TYPES,
                    f'Target {tid} needs a supported platform and product_type.')
            target_map[tid] = target
    web = legacy or any(t.get('platform') == 'web' for t in target_map.values())
    required = ([] if legacy and not standard else ['index.md', 'components.md']) + ([str((preview / name).relative_to(root)) for name in ['index.html', 'components.html', 'tokens.css']] if web else [])
    for name in required:
        require(artifact(root / name), f'Missing/empty artifact: {name}')
    if errors:
        return errors

    pages: dict[Path, Page] = {}
    for p in root.rglob('*'):
        if p.suffix.lower() not in {'.html', '.md'} or not p.is_file():
            continue
        if not inside(p.resolve()):
            errors.append(f'Document symlink escapes package: {p}')
            continue
        pages[p.resolve()] = Page(p.read_text(), p.suffix.lower() == '.md')

    def resolve_url(owner: Path, value: str, resource=False):
        url = urlsplit(value)
        if url.scheme or url.netloc:
            if resource and url.scheme != 'data':
                errors.append(f'Remote/runtime resource in {owner.relative_to(root)}: {value}')
            return None
        target = (owner.parent / unquote(url.path)).resolve() if url.path else owner
        # A primary-source citation in the spec is not a review-runtime resource.
        if not resource and (owner == root / 'design-system.md' or (standard and owner in {root / 'index.md', preview / 'index.html'})) and target in cited_sources:
            return None
        if not require(inside(target), f'Local link escapes package in {owner.relative_to(root)}: {value}'):
            return None
        require(artifact(target), f'Broken/empty local link in {owner.relative_to(root)}: {value}')
        if url.fragment and target.suffix.lower() in {'.md', '.html'}:
            require(target in pages and unquote(url.fragment) in pages[target].ids,
                    f'Missing explicit anchor in {owner.relative_to(root)}: {value}')
        return target

    def css_imports(text):
        result = []
        pattern = r'@import\s+(?:url\(\s*(?:"([^"]+)"|\'([^\']+)\'|([^\s)]+))\s*\)|"([^"]+)"|\'([^\']+)\')'
        for match in re.finditer(pattern, text):
            result.append(next(value for value in match.groups() if value is not None))
        return result

    def style_reaches(path: Path, token_css: Path, seen: set[Path]):
        if path == token_css:
            return artifact(path)
        if path in seen or not artifact(path) or path.suffix != '.css':
            return False
        seen.add(path)
        imports = css_imports(path.read_text())
        return any((q := resolve_url(path, u, True)) is not None and style_reaches(q, token_css, seen) for u in imports)

    def validate_css(owner, text):
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
        urls = css_imports(text)
        for match in re.finditer(r'url\(\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s)]+))\s*\)', text):
            urls.append(next(value for value in match.groups() if value is not None))
        for value in urls:
            # Fragment-only filter/mask references depend on the rendered document.
            if not value.startswith('#'):
                resolve_url(owner, value, True)

    for p in root.rglob('*.css'):
        if not artifact(p):
            errors.append(f'Missing/escaped CSS resource: {p}')
            continue
        validate_css(p.resolve(), p.read_text())

    token_css = (preview / 'tokens.css').resolve()
    html_present = any(p.suffix == '.html' for p in pages)
    if html_present:
        require(artifact(token_css), 'HTML previews require shared tokens.css.')
    for p, page in pages.items():
        for value in page.links:
            resolve_url(p, value)
        for value in page.resources:
            resolve_url(p, value, True)
        for text in page.inline_css:
            validate_css(p, text)
        if p.suffix == '.html':
            require(not page.duplicate_ids, f'Duplicate HTML IDs in {p.relative_to(root)}: {sorted(page.duplicate_ids)}')
            styles = page.styles + [u for text in page.inline_css for u in css_imports(text)]
            require(any((q := resolve_url(p, u, True)) is not None and style_reaches(q, token_css, set()) for u in styles),
                    f'HTML does not consume shared tokens.css: {p.relative_to(root)}')

    inventory, dispositions = coverage.get('screens'), coverage.get('requirements')
    if not isinstance(inventory, list) or not isinstance(dispositions, list):
        return errors + ['coverage screens and requirements must be arrays.']
    require(bool(inventory), 'No product screen/flow artifacts declared.')
    screen_map = {}

    def visual_links(owner, page):
        return {q for u in page.links + page.resources if (q := resolve_url(owner, u, u in page.resources)) is not None and q.suffix.lower() in VISUALS}

    for s in inventory:
        if not isinstance(s, dict) or not isinstance(s.get('id'), str):
            errors.append('Each screen must be an object with a string id.')
            continue
        sid = s['id']
        require(bool(sid) and sid not in screen_map, f'Empty/duplicate screen id: {sid}')
        screen_map[sid] = s
        if not isinstance(s.get('file'), str):
            errors.append(f'Screen {sid} lacks file path.')
            continue
        f = (root / s['file']).resolve()
        if standard:
            require(preview in f.parents, f'Screen {sid} must be under mockup/.')
        fmt = 'html' if legacy else s.get('format')
        suffixes = {'html': {'.html'}, 'image': IMAGES, 'storyboard': {'.md'}, 'preview': VISUALS}
        require(fmt in suffixes and f.suffix.lower() in suffixes.get(fmt, set()) and artifact(f), f'Screen {sid} has missing or incompatible {fmt} artifact: {s["file"]}')
        require(isinstance(s.get('title'), str) and bool(s['title']) and strings(s.get('roles'), True), f'Screen {sid} needs title and roles/player context.')
        if not legacy:
            require(strings(s.get('targets'), True) and all(t in target_map for t in s['targets']), f'Screen {sid} references missing/unknown targets.')
        if fmt == 'html':
            require(isinstance(s.get('viewports'), list) and bool(s['viewports']) and all(type(v) is int and v > 0 for v in s['viewports']), f'Screen {sid} needs positive viewport widths.')
        else:
            require(strings(s.get('render_contexts'), True), f'Screen {sid} needs render_contexts.')
        if fmt == 'storyboard':
            require(f in pages and bool(visual_links(f, pages[f])), f'Storyboard {sid} needs local visual examples.')
        refs, acceptance = s.get('requirements'), s.get('acceptance', [])
        require(strings(refs, True) and all(x in frs for x in refs), f'Screen {sid} has missing/unknown requirement IDs.')
        require(strings(acceptance, bool(acs)) and all(x in acs for x in acceptance), f'Screen {sid} has missing/unknown acceptance IDs.')
        states, locations = s.get('states'), s.get('state_locations')
        if not strings(states, True) or not isinstance(locations, dict):
            errors.append(f'Screen {sid} needs nonempty states and state_locations.')
            continue
        require(len(set(states)) == len(states) and set(states) == set(locations), f'Screen {sid} states and locations must match without duplicates.')
        for state in states:
            loc = locations.get(state)
            if fmt == 'html':
                require(isinstance(loc, str) and loc.startswith('#') and f in pages and unquote(loc[1:]) in pages[f].ids, f'Screen {sid} state {state} has no real HTML ID anchor.')
                continue
            if not isinstance(loc, dict) or not all(isinstance(loc.get(k), str) and bool(loc[k]) for k in ('file', 'label', 'annotation')):
                errors.append(f'Screen {sid} state {state} needs file, label and annotation.')
                continue
            visual = (root / loc['file']).resolve()
            require(artifact(visual) and visual.suffix.lower() in VISUALS | {'.md'}, f'Screen {sid} state {state} has missing/incompatible visual.')
            if visual.suffix == '.md':
                require(visual in pages and bool(visual_links(visual, pages[visual])), f'State storyboard {sid}/{state} needs local visuals.')
            url = urlsplit(loc['annotation'])
            ann = (root / unquote(url.path)).resolve()
            anchor = unquote(url.fragment)
            ok = not url.scheme and not url.netloc and inside(ann) and ann.suffix == '.md' and ann in pages and anchor in pages[ann].explicit_ids
            require(ok, f'Screen {sid} state {state} needs a real Markdown annotation anchor.')
            if ok:
                section = pages[ann].section(anchor)
                require(loc['label'] in section, f'Screen {sid} state {state} label absent from annotation section.')
                section_page = Page(section, True)
                linked = {q for u in section_page.links + section_page.resources if (q := resolve_url(ann, u, u in section_page.resources)) is not None}
                require(visual in linked or (visual == ann and bool(visual_links(ann, section_page))), f'Screen {sid} state {state} annotation must link its visual.')

    declared = {}
    for r in dispositions:
        if not isinstance(r, dict) or not isinstance(r.get('id'), str):
            errors.append('Each requirement disposition needs a string id.')
            continue
        rid = r['id']
        require(rid not in declared, f'Duplicate requirement disposition: {rid}')
        declared[rid] = r
        kind, refs = r.get('disposition'), r.get('screens', [])
        require(kind in {'visual', 'cross-cutting', 'technical', 'deferred'}, f'Unknown disposition for {rid}.')
        if not strings(refs):
            errors.append(f'Requirement {rid} screens must be a string array.')
            continue
        require(all(x in screen_map for x in refs), f'Requirement {rid} references unknown screens.')
        require(bool(refs) if kind in {'visual', 'cross-cutting'} else isinstance(r.get('notes'), str) and bool(r['notes'].strip()), f'Requirement {rid} needs visual mappings or technical/deferred rationale.')
        for sid in refs:
            require(sid in screen_map and isinstance(screen_map[sid].get('requirements'), list) and rid in screen_map[sid]['requirements'], f'Mapping disagrees: {rid} -> {sid}')
    require(set(declared) == frs, f'Requirement dispositions differ from source: missing={sorted(frs-set(declared))}, unknown={sorted(set(declared)-frs)}')
    for sid, s in screen_map.items():
        refs = s.get('requirements', [])
        if strings(refs):
            for rid in refs:
                require(rid in declared and isinstance(declared[rid].get('screens'), list) and sid in declared[rid]['screens'], f'Mapping disagrees: {sid} -> {rid}')

    # Independently addressable states may span inventory entries in one document.
    state_ids = {}
    for screen in screen_map.values():
        file = (root / screen.get('file', '')).resolve()
        if file.suffix == '.html':
            for loc in screen.get('state_locations', {}).values() if isinstance(screen.get('state_locations'), dict) else []:
                if isinstance(loc, str) and loc.startswith('#'):
                    state_ids.setdefault(file, set()).add(unquote(loc[1:]))
    for file, ids in state_ids.items():
        if file in pages:
            for identity in ids:
                parents = pages[file].ancestors.get(identity, set()) & ids
                require(not parents, f'Nested independent state {identity} inside {sorted(parents)} in {file.relative_to(root)}.')

    def reconcile(key, expected):
        entries = coverage.get(key)
        if entries is None and not standard:
            return  # Legacy contracts did not require these disposition arrays.
        if entries is None and not expected:
            return
        if not require(isinstance(entries, list), f'coverage.{key} must be an array.'):
            return
        seen = set()
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get('id'), str):
                errors.append(f'Each {key} disposition needs a string id.')
                continue
            identity = entry['id']
            require(identity not in seen, f'Duplicate {key} disposition: {identity}')
            seen.add(identity)
            kind = entry.get('disposition')
            require(kind in {'visual', 'cross-cutting', 'technical', 'deferred'}, f'Unknown disposition for {identity}.')
            refs, locs = entry.get('screens', []), entry.get('locations', [])
            if not require(strings(refs) and strings(locs), f'Invalid mappings for {identity}.'):
                continue
            require(all(ref in screen_map for ref in refs), f'{identity} references unknown screens.')
            if kind in {'visual', 'cross-cutting'}:
                require(bool(refs or locs), f'{identity} needs visual mappings.')
            else:
                require(isinstance(entry.get('notes'), str) and bool(entry['notes'].strip()), f'{identity} needs nonvisual rationale.')
            for loc in locs:
                target = resolve_url(root / 'coverage.json', loc)
                fragment = unquote(urlsplit(loc).fragment)
                if target and target.suffix == '.html':
                    require(fragment in state_ids.get(target, set()), f'{identity} location must identify a declared state: {loc}')
                elif target:
                    require(any(target == (root / screen.get('file', '')).resolve() for screen in screen_map.values()) or
                            any(isinstance(value, dict) and loc == value.get('annotation') for screen in screen_map.values()
                                for value in screen.get('state_locations', {}).values()), f'{identity} location must identify a declared visual: {loc}')
        require(seen == expected, f'{key} dispositions differ from source: missing={sorted(expected-seen)}, unknown={sorted(seen-expected)}')

    reconcile('quality_requirements', nfrs)
    reconcile('acceptance_criteria', acs)

    def reachable_from(index):
        reached, queue = set(), [index.resolve()]
        while queue:
            p = queue.pop()
            if p in reached:
                continue
            reached.add(p)
            if p in pages:
                for u in pages[p].links + pages[p].resources:
                    q = resolve_url(p, u, u in pages[p].resources)
                    if q is not None and q not in reached:
                        queue.append(q)
        return reached

    html_gallery = str((preview / 'index.html').relative_to(root))
    galleries = [html_gallery] if legacy and not standard else ['index.md'] + ([html_gallery] if web else [])
    for gallery in galleries:
        reachable = reachable_from(root / gallery)
        catalog = str((preview / 'components.html').relative_to(root)) if gallery.endswith('.html') else 'components.md'
        if standard and (root / gallery).resolve() in pages:
            index = (root / gallery).resolve()
            links = [resolve_url(index, u) for u in pages[index].links if urlsplit(u).path]
            links = [p for p in links if p is not None and p != index]
            require(bool(links) and links[0] == root / 'design-system.md', f'First document link in {gallery} must be design-system.md.')
        needed = ['design-system.md', catalog] + [s['file'] for s in screen_map.values() if isinstance(s.get('file'), str)]
        for s in screen_map.values():
            for loc in s.get('state_locations', {}).values() if isinstance(s.get('state_locations'), dict) else []:
                if isinstance(loc, dict) and isinstance(loc.get('annotation'), str):
                    needed.append(unquote(urlsplit(loc['annotation']).path))
        for name in needed:
            require((root / name).resolve() in reachable, f'Artifact is unreachable from {gallery}: {name}')

    flat = {}
    for layer in LAYERS:
        values = tokens.get(layer)
        if not isinstance(values, dict) or not values:
            errors.append(f'Token layer {layer} must be a nonempty object.')
            continue
        for name, value in values.items():
            require(bool(re.fullmatch(r'[a-z][a-z0-9-]*', name)), f'Invalid token key: {layer}.{name}')
            require(isinstance(value, (str, int, float)) and not isinstance(value, bool), f'Token {layer}.{name} must be a string/number leaf.')
            flat[f'{layer}.{name}'] = value
    overrides = tokens.get('overrides', {})
    if not isinstance(overrides, dict):
        errors.append('tokens.overrides must be a target-keyed object.')
        overrides = {}
    effective = {'base': flat}
    for tid, layers in overrides.items():
        require(tid in target_map, f'Token override references unknown target: {tid}')
        if not isinstance(layers, dict):
            errors.append(f'Override {tid} must be layer objects.')
            continue
        values = dict(flat)
        for layer, entries in layers.items():
            if layer not in LAYERS or not isinstance(entries, dict):
                errors.append(f'Invalid override layer: {tid}/{layer}')
                continue
            for name, value in entries.items():
                key = f'{layer}.{name}'
                require(key in flat, f'Override {tid} has no base token: {key}')
                require(isinstance(value, (str, int, float)) and not isinstance(value, bool), f'Invalid override value: {tid}/{key}')
                values[key] = value
        effective[tid] = values
    for context, values in effective.items():
        aliases = {key: m[1] for key, value in values.items() if isinstance(value, str) and (m := re.fullmatch(r'\{([^{}]+)\}', value))}
        for key, target in aliases.items():
            require(target in values, f'Unknown token alias ({context}): {key} -> {target}')
        for start in aliases:
            seen, current = set(), start
            while current in aliases:
                if current in seen:
                    errors.append(f'Cyclic token alias ({context}) starting at {start}')
                    break
                seen.add(current)
                current = aliases[current]

    html_targets = {tid for tid, target in target_map.items() if target.get('platform') == 'web'}
    for screen in screen_map.values():
        if screen.get('format') == 'html' and strings(screen.get('targets')):
            html_targets.update(screen['targets'])
    for path, page in pages.items():
        if path.suffix == '.html':
            html_targets.update(page.targets)
            if not legacy:
                require(all(tid in target_map for tid in page.targets), f'HTML has undeclared target attribute: {path.relative_to(root)}')
    if artifact(token_css):
        css = token_css.read_text()
        rules = re.findall(r'([^{}]+)\{([^{}]*)\}', css)
        declarations, target_declarations = {}, {}
        for selector, body in rules:
            props = dict(re.findall(r'(--[a-zA-Z0-9_-]+)\s*:\s*([^;{}]+);', body))
            if match := re.search(r'\[data-design-target\s*=\s*[\"\']([^\"\']+)[\"\']\]', selector):
                tid = match[1]
                require(tid in overrides, f'CSS target override not declared in JSON: {tid}')
                target_declarations.setdefault(tid, {}).update(props)
            else:
                declarations.update(props)
        css_values = tokens.get('css_values', {})
        if not isinstance(css_values, dict):
            errors.append('tokens.css_values must be a token-keyed object.')
            css_values = {}
        for key, value in css_values.items():
            context, token_key = key.split('/', 1) if '/' in key else ('base', key)
            token_value = effective.get(context, {}).get(token_key)
            require(token_key in effective.get(context, {}) and isinstance(value, str) and bool(value), f'Invalid CSS conversion: {key}')
            require(not (isinstance(token_value, str) and re.fullmatch(r'\{([^{}]+)\}', token_value)), f'CSS conversion cannot replace alias: {key}')
        for context, values in effective.items():
            if context != 'base' and context not in html_targets and context not in target_declarations:
                continue
            # Base export plus only the tokens actually overridden on a target.
            keys = values if context == 'base' else {f'{layer}.{name}' for layer, entries in overrides[context].items() if isinstance(entries, dict) for name in entries}
            props = declarations if context == 'base' else target_declarations.get(context, {})
            for key in keys:
                prop = '--' + key.replace('.', '-', 1)
                value = values[key]
                alias = re.fullmatch(r'\{([^{}]+)\}', value) if isinstance(value, str) else None
                conversion_key = key if context == 'base' else context + '/' + key
                expected = 'var(--' + alias[1].replace('.', '-', 1) + ')' if alias else css_values.get(conversion_key, str(value))
                require(props.get(prop, '').strip() == expected, f'CSS value/alias differs for {context}/{key}.')
    return list(dict.fromkeys(errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    parser.add_argument('--source', '--prd', dest='source', required=True, type=Path)
    parser.add_argument('--layout', choices=['auto', 'standard', 'legacy'], default='auto')
    args = parser.parse_args()
    try:
        errors = check(args.package, args.source, args.layout)
    except (OSError, UnicodeError, TypeError, ValueError, AttributeError, KeyError) as e:
        errors = [f'Cannot validate malformed/unreadable package: {e}']
    for error in errors:
        print('ERROR:', error)
    if errors:
        return 1
    print('PASS: structural source coverage, artifact links and token consistency. Target runtime/a11y evidence requires separate review.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
