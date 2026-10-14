"""Behavior checks for valid packages and consequential traceability/link/token defects."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import sys

sys.dont_write_bytecode = True

spec = importlib.util.spec_from_file_location('artifact_checker', Path(__file__).resolve().parents[1] / 'scripts/check_artifacts.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PackageFixture:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.prd = self.base/'PRD.md'
        self.prd.write_text('# Fixture PRD\n| FR-001 | Public catalog |\n| FR-002 | Operational follow-up |\n| AC-001 | Render catalog |\n')
        self.root = self.base/'design-system'
        (self.root/'mockups').mkdir(parents=True)
        for name in ['design-system.md','verification.md']:
            (self.root/name).write_text('# Fixture design data\n')
        (self.root/'tokens.json').write_text(json.dumps({'primitive':{'ink':'#111111'},'semantic':{'text':'{primitive.ink}'},'component':{'label':'{semantic.text}'}}))
        (self.root/'tokens.css').write_text(':root { --primitive-ink: #111111; --semantic-text: var(--primitive-ink); --component-label: var(--semantic-text); }')
        (self.root/'index.html').write_text('<!doctype html><link rel="stylesheet" href="tokens.css"><a href="design-system.md">Spec</a><a href="components.html">Components</a><a href="mockups/catalog.html#ready">Catalog</a>')
        (self.root/'components.html').write_text('<!doctype html><link rel="stylesheet" href="tokens.css"><button>Example</button>')
        (self.root/'mockups/catalog.html').write_text('<!doctype html><link rel="stylesheet" href="../tokens.css"><main id="ready">Catalog</main><section id="loading">Loading</section>')
        self.coverage = {'source':{'path':'../PRD.md','sha256':hashlib.sha256(self.prd.read_bytes()).hexdigest()},'screens':[{'id':'catalog','title':'Catalog','file':'mockups/catalog.html','roles':['Visitor'],'requirements':['FR-001'],'acceptance':['AC-001'],'states':['ready','loading'],'state_locations':{'ready':'#ready','loading':'#loading'},'viewports':[390,1440]}],'requirements':[{'id':'FR-001','disposition':'visual','screens':['catalog']},{'id':'FR-002','disposition':'technical','screens':[],'notes':'Operations concern; no product screen.'}]}
        self.save_coverage()

    def save_coverage(self):
        (self.root/'coverage.json').write_text(json.dumps(self.coverage))

    def errors(self):
        return module.check(self.root,self.prd)


class ArtifactCheckerTest(PackageFixture, unittest.TestCase):
    def test_valid_package(self):
        self.assertEqual(self.errors(),[])

    def test_stale_source(self):
        self.prd.write_text(self.prd.read_text()+'Changed policy.\n')
        self.assertTrue(self.errors())

    def test_missing_required_visual_mapping(self):
        self.coverage['requirements'][0]['screens']=[]
        self.save_coverage()
        self.assertTrue(self.errors())

    def test_unaccounted_requirement(self):
        self.coverage['requirements'].pop()
        self.save_coverage()
        self.assertTrue(self.errors())

    def test_nonexistent_acceptance(self):
        self.coverage['screens'][0]['acceptance']=['AC-999']
        self.save_coverage()
        self.assertTrue(self.errors())

    def test_missing_state_anchor(self):
        self.coverage['screens'][0]['state_locations']['loading']='#invented'
        self.save_coverage()
        self.assertTrue(self.errors())

    def test_unreachable_screen(self):
        p=self.root/'index.html'
        p.write_text(p.read_text().replace('<a href="mockups/catalog.html#ready">Catalog</a>',''))
        self.assertTrue(self.errors())

    def test_broken_asset(self):
        p=self.root/'mockups/catalog.html'
        p.write_text(p.read_text()+'<img src="missing-poster.png" alt="Poster">')
        self.assertTrue(self.errors())

    def test_link_escapes_package(self):
        p=self.root/'index.html'
        p.write_text(p.read_text()+'<a href="../PRD.md">Outside package</a>')
        self.assertTrue(self.errors())

    def test_remote_runtime_dependency(self):
        p=self.root/'index.html'
        p.write_text(p.read_text()+'<script src="https://example.com/runtime.js"></script>')
        self.assertTrue(self.errors())

    def test_tokens_not_consumed(self):
        p=self.root/'components.html'
        p.write_text('<!doctype html><button>Example</button>')
        self.assertTrue(self.errors())

    def test_css_value_drift(self):
        p=self.root/'tokens.css'
        p.write_text(p.read_text().replace('#111111','#222222'))
        self.assertTrue(self.errors())

    def test_cyclic_token_aliases(self):
        tokens=json.loads((self.root/'tokens.json').read_text())
        tokens['primitive']['ink']='{component.label}'
        (self.root/'tokens.json').write_text(json.dumps(tokens))
        p=self.root/'tokens.css'
        p.write_text(p.read_text().replace('#111111','var(--component-label)'))
        self.assertTrue(self.errors())

    def test_imported_shared_style(self):
        (self.root/'common.css').write_text('@import "tokens.css";')
        p=self.root/'components.html'
        p.write_text(p.read_text().replace('tokens.css','common.css'))
        self.assertEqual(self.errors(),[])

class PlatformArtifactCheckerTest(PackageFixture, unittest.TestCase):
    def neutral(self, platform='mobile', product_type='application', fmt='image'):
        # Switch the legacy fixture to a native/game package without HTML or CSS.
        for p in self.root.rglob('*.html'):
            p.unlink()
        (self.root/'tokens.css').unlink()
        (self.root/'mockups/catalog.png').write_bytes(bytes.fromhex('89504e470d0a1a0a'))
        (self.root/'mockups/loading.png').write_bytes(bytes.fromhex('89504e470d0a1a0a'))
        (self.root/'mockups/catalog-notes.md').write_text('<a id="ready"></a>\n## Ready\n[Ready visual](catalog.png)\n<a id="loading"></a>\n## Loading\n[Loading visual](loading.png)\n')
        (self.root/'index.md').write_text('[Spec](design-system.md)\n[Components](components.md)\n[Catalog](mockups/catalog.png)\n[States](mockups/catalog-notes.md)\n')
        (self.root/'components.md').write_text('# Components\n[Visual example](mockups/catalog.png)\n')
        self.coverage['schema_version']=2
        self.coverage['targets']=[{'id':'phone','platform':platform,'product_type':product_type}]
        screen=self.coverage['screens'][0]
        screen.update(format=fmt,file='mockups/catalog.png',targets=['phone'],render_contexts=['Portrait phone; illustrative fixture'])
        screen.pop('viewports')
        screen['state_locations']={state:{'file':f'mockups/{"catalog" if state=="ready" else state}.png','label':state.capitalize(),'annotation':f'mockups/catalog-notes.md#{state}'} for state in screen['states']}
        self.save_coverage()

    def test_mobile_images_need_no_html_css(self):
        self.neutral()
        self.assertEqual(self.errors(),[])

    def test_game_engine_unspecified_storyboard(self):
        self.neutral('console','game','storyboard')
        screen=self.coverage['screens'][0]
        screen['file']='mockups/catalog-notes.md'
        self.save_coverage()
        self.assertEqual(self.errors(),[])

    def test_neutral_unspecified_target(self):
        self.neutral('unspecified','unspecified')
        self.assertEqual(self.errors(),[])

    def test_supplied_game_preview(self):
        self.neutral('desktop','game','preview')
        (self.root/'mockups/play.mp4').write_bytes(b'fixture supplied preview')
        self.coverage['screens'][0]['file']='mockups/play.mp4'
        p=self.root/'index.md'
        p.write_text(p.read_text()+'[Play capture](mockups/play.mp4)\n')
        self.save_coverage()
        self.assertEqual(self.errors(),[])

    def test_non_html_state_missing_label(self):
        self.neutral()
        self.coverage['screens'][0]['state_locations']['ready']['label']='Invented'
        self.save_coverage()
        self.assertTrue(any('label absent' in e for e in self.errors()))

    def test_non_html_missing_annotation_anchor(self):
        self.neutral()
        self.coverage['screens'][0]['state_locations']['ready']['annotation']='mockups/catalog-notes.md#absent'
        self.save_coverage()
        self.assertTrue(self.errors())

    def test_non_html_annotation_links_different_visual(self):
        self.neutral()
        self.coverage['screens'][0]['state_locations']['ready']['file']='mockups/loading.png'
        self.save_coverage()
        self.assertTrue(any('annotation must link' in e for e in self.errors()))

    def test_non_html_missing_visual_file(self):
        self.neutral()
        (self.root/'mockups/loading.png').unlink()
        self.assertTrue(self.errors())

    def test_non_html_unreachable_annotations(self):
        self.neutral()
        p=self.root/'index.md'
        p.write_text(p.read_text().replace('[States](mockups/catalog-notes.md)\n',''))
        self.assertTrue(any('unreachable' in e for e in self.errors()))

    def test_storyboard_without_visuals(self):
        self.neutral('desktop','game','storyboard')
        self.coverage['screens'][0]['file']='mockups/catalog-notes.md'
        (self.root/'mockups/catalog-notes.md').write_text('<a id="ready"></a>Ready\n<a id="loading"></a>Loading\n')
        self.save_coverage()
        self.assertTrue(any('needs local visual' in e for e in self.errors()))

    def test_image_format_rejects_html(self):
        self.neutral()
        self.coverage['screens'][0]['file']='mockups/catalog-notes.md'
        self.save_coverage()
        self.assertTrue(self.errors())

    def test_unknown_target(self):
        self.neutral()
        self.coverage['screens'][0]['targets']=['imaginary']
        self.save_coverage()
        self.assertTrue(self.errors())

    def test_gdd_source_excerpts(self):
        self.neutral('desktop','game')
        self.prd.write_text('# GDD\nPlayers can pause play.\nPaused menu remains readable.\nNetwork handling is technical.\n')
        self.coverage['source'].update(sha256=hashlib.sha256(self.prd.read_bytes()).hexdigest(),requirements={'GAME-PAUSE':'Players can pause play.','GAME-NET':'Network handling is technical.'},acceptance={'CHECK-PAUSE':'Paused menu remains readable.'})
        self.coverage['screens'][0].update(requirements=['GAME-PAUSE'],acceptance=['CHECK-PAUSE'])
        self.coverage['requirements'][0]['id']='GAME-PAUSE'
        self.coverage['requirements'][1]['id']='GAME-NET'
        self.save_coverage()
        self.assertEqual(self.errors(),[])
        self.coverage['source']['requirements']['GAME-PAUSE']='Invented requirement.'
        self.save_coverage()
        self.assertTrue(self.errors())

    def test_brief_without_acceptance_definitions(self):
        self.neutral()
        self.prd.write_text('Show catalog.\nRecord operations.\n')
        self.coverage['source'].update(sha256=hashlib.sha256(self.prd.read_bytes()).hexdigest(),requirements={'FR-001':'Show catalog.','FR-002':'Record operations.'})
        self.coverage['screens'][0]['acceptance']=[]
        self.save_coverage()
        self.assertEqual(self.errors(),[])

    def test_explicit_ids_cannot_hide_fr_table_rows(self):
        self.neutral()
        self.coverage['source']['requirements']={'FR-001':'Public catalog'}
        self.coverage['requirements'].pop()
        self.save_coverage()
        self.assertTrue(self.errors())

    def test_target_token_override(self):
        self.neutral()
        p=self.root/'tokens.json'
        tokens=json.loads(p.read_text())
        tokens['overrides']={'phone':{'primitive':{'ink':'#222222'}}}
        p.write_text(json.dumps(tokens))
        self.assertEqual(self.errors(),[])
        tokens['overrides']['phone']['primitive']['ink']='{component.label}'
        p.write_text(json.dumps(tokens))
        self.assertTrue(any('Cyclic' in e for e in self.errors()))

    def test_override_unknown_token_or_target(self):
        self.neutral()
        p=self.root/'tokens.json'
        tokens=json.loads(p.read_text())
        tokens['overrides']={'unselected':{'primitive':{'new-color':'#222222'}}}
        p.write_text(json.dumps(tokens))
        self.assertTrue(self.errors())

    def test_combined_web_mobile_shared_tokens(self):
        self.coverage.update(schema_version=2,targets=[{'id':'web','platform':'web','product_type':'application'},{'id':'phone','platform':'mobile','product_type':'application'}])
        self.coverage['screens'][0].update(format='html',targets=['web','phone'])
        (self.root/'index.md').write_text('[Spec](design-system.md)\n[Components](components.md)\n[Catalog](mockups/catalog.html#ready)\n')
        (self.root/'components.md').write_text('[Visual catalog](components.html)\n')
        p=self.root/'tokens.json'
        tokens=json.loads(p.read_text())
        tokens['overrides']={'phone':{'primitive':{'ink':'#222222'}}}
        p.write_text(json.dumps(tokens))
        css=self.root/'tokens.css'
        css.write_text(css.read_text()+'\n[data-design-target="phone"] { --primitive-ink: #222222; }')
        self.save_coverage()
        self.assertEqual(self.errors(),[])
        css.write_text(css.read_text().replace('#222222','#333333'))
        self.assertTrue(self.errors())

    def test_optional_browser_preview_requires_css(self):
        self.neutral()
        (self.root/'demo.html').write_text('<main>Browser simulation</main>')
        self.assertTrue(any('tokens.css' in e for e in self.errors()))

    def test_numeric_token_export_conversion(self):
        p=self.root/'tokens.json'
        tokens=json.loads(p.read_text())
        tokens['primitive']['space']=16
        tokens['css_values']={'primitive.space':'16px'}
        p.write_text(json.dumps(tokens))
        css=self.root/'tokens.css'
        css.write_text(css.read_text().replace('}', '--primitive-space: 16px; }'))
        self.assertEqual(self.errors(),[])

    def test_primary_source_citation_allowed_only_in_spec(self):
        self.neutral()
        p=self.root/'design-system.md'
        p.write_text(p.read_text()+'[Source](../PRD.md)\n')
        self.assertEqual(self.errors(),[])
        p=self.root/'index.md'
        p.write_text(p.read_text()+'[Escape](../PRD.md)\n')
        self.assertTrue(self.errors())

    def test_non_html_unknown_token_alias(self):
        self.neutral()
        p=self.root/'tokens.json'
        tokens=json.loads(p.read_text())
        tokens['semantic']['text']='{primitive.missing}'
        p.write_text(json.dumps(tokens))
        self.assertTrue(self.errors())


    def test_state_label_in_different_section_is_not_enough(self):
        self.neutral()
        self.coverage['screens'][0]['state_locations']['ready']['label']='Loading'
        self.save_coverage()
        self.assertTrue(any('label absent' in e for e in self.errors()))

    def test_markdown_broken_local_image(self):
        self.neutral()
        p=self.root/'components.md'
        p.write_text(p.read_text()+'![Missing visual](missing.png)\n')
        self.assertTrue(any('Broken' in e for e in self.errors()))

    def test_markdown_fenced_examples_are_not_actual_links(self):
        self.neutral()
        p=self.root/'design-system.md'
        p.write_text(p.read_text()+'\n```html\n<a href="missing.html">Example syntax</a>\n```\n`[Example](missing.md)`\n')
        self.assertEqual(self.errors(),[])

    def test_v2_web_requires_markdown_baseline(self):
        self.coverage.update(schema_version=2,targets=[{'id':'web','platform':'web','product_type':'application'}])
        self.coverage['screens'][0].update(format='html',targets=['web'])
        self.save_coverage()
        self.assertTrue(any('index.md' in e for e in self.errors()))

    def test_unknown_schema_version(self):
        self.coverage['schema_version']=3
        self.save_coverage()
        self.assertTrue(self.errors())

    def test_target_css_unit_conversion(self):
        self.coverage.update(schema_version=2,targets=[{'id':'web','platform':'web','product_type':'application'}])
        self.coverage['screens'][0].update(format='html',targets=['web'])
        (self.root/'index.md').write_text('[Spec](design-system.md)\n[Components](components.md)\n[Catalog](mockups/catalog.html)\n')
        (self.root/'components.md').write_text('[Visual catalog](components.html)\n')
        p=self.root/'tokens.json'
        tokens=json.loads(p.read_text())
        tokens['primitive']['space']=16
        tokens['overrides']={'web':{'primitive':{'space':20}}}
        tokens['css_values']={'primitive.space':'16px','web/primitive.space':'20px'}
        p.write_text(json.dumps(tokens))
        css=self.root/'tokens.css'
        css.write_text(css.read_text().replace('}', '--primitive-space: 16px; }')+'\n[data-design-target="web"] { --primitive-space: 20px; }')
        self.save_coverage()
        self.assertEqual(self.errors(),[])

    def test_cli_source_and_prd_aliases(self):
        import subprocess
        self.neutral()
        for flag in ('--source','--prd'):
            result=subprocess.run([sys.executable,str(Path(module.__file__)),str(self.root),flag,str(self.prd)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_cli_malformed_package_reports_without_traceback(self):
        import subprocess
        self.coverage['screens'][0]['requirements']=[{'invalid':'id'}]
        self.save_coverage()
        result=subprocess.run([sys.executable,str(Path(module.__file__)),str(self.root),'--source',str(self.prd)],capture_output=True,text=True)
        self.assertEqual(result.returncode,1)
        self.assertIn('ERROR:',result.stdout)
        self.assertNotIn('Traceback',result.stdout+result.stderr)


    def test_markdown_heading_links_and_explicit_state_anchors(self):
        self.neutral()
        p=self.root/'components.md'
        p.write_text('# Component anatomy\n[Anatomy](#component-anatomy)\n[Visual](mockups/catalog.png)\n')
        self.assertEqual(self.errors(),[])
        p=self.root/'mockups/catalog-notes.md'
        p.write_text(p.read_text().replace('<a id="ready"></a>',''))
        self.assertTrue(any('annotation anchor' in e for e in self.errors()))

    def test_supporting_source_citation_and_freshness(self):
        self.neutral()
        doc=self.base/'decisions.md'
        doc.write_text('Use the phone target.\n')
        self.coverage['source']['supporting_documents']=[{'path':'../decisions.md','sha256':hashlib.sha256(doc.read_bytes()).hexdigest()}]
        self.save_coverage()
        p=self.root/'design-system.md'
        p.write_text(p.read_text()+'[Decisions](../decisions.md)\n')
        self.assertEqual(self.errors(),[])
        doc.write_text('Changed target decision.\n')
        self.assertTrue(any('Supporting source digest differs' in e for e in self.errors()))


    def test_unquoted_css_import(self):
        (self.root/'common.css').write_text('@import url(tokens.css);')
        p=self.root/'components.html'
        p.write_text(p.read_text().replace('tokens.css','common.css'))
        self.assertEqual(self.errors(),[])

    def test_remote_css_resources_and_missing_css_asset(self):
        p=self.root/'tokens.css'
        original=p.read_text()
        for rule in ('@import url(https://example.com/remote.css);','body { background: url("https://example.com/poster.png"); }','body { background: url(missing.png); }'):
            p.write_text(original+'\n'+rule)
            self.assertTrue(self.errors())

    def test_unused_native_override_needs_no_css_in_mixed_package(self):
        self.coverage.update(schema_version=2,targets=[{'id':'web','platform':'web','product_type':'application'},{'id':'phone','platform':'mobile','product_type':'application'}])
        self.coverage['screens'][0].update(format='html',targets=['web'])
        (self.root/'index.md').write_text('[Spec](design-system.md)\n[Components](components.md)\n[Catalog](mockups/catalog.html)\n')
        (self.root/'components.md').write_text('[Visual catalog](components.html)\n')
        p=self.root/'tokens.json'
        tokens=json.loads(p.read_text())
        tokens['overrides']={'phone':{'primitive':{'ink':'#222222'}}}
        p.write_text(json.dumps(tokens))
        self.save_coverage()
        self.assertEqual(self.errors(),[])
        page=self.root/'components.html'
        page.write_text(page.read_text()+'<section data-design-target="phone">Phone example</section>')
        self.assertTrue(any('phone/primitive.ink' in e for e in self.errors()))


    def test_inline_css_resources(self):
        p=self.root/'components.html'
        original=p.read_text()
        for inline in ('<style>.card { background-image: url(https://example.com/image.png); }</style>', '<div style="background-image: url(missing.png)">Card</div>'):
            p.write_text(original+inline)
            self.assertTrue(self.errors())
        (self.root/'local.png').write_bytes(b'fixture image')
        p.write_text(original+'<style>.card { background-image: url(local.png); }</style>')
        self.assertEqual(self.errors(),[])

    def test_inline_shared_token_import(self):
        p=self.root/'components.html'
        p.write_text('<style>@import url(tokens.css);</style><button>Example</button>')
        self.assertEqual(self.errors(),[])



class StandardArtifactCheckerTest(PackageFixture, unittest.TestCase):
    def standard(self, native=False):
        if native:
            PlatformArtifactCheckerTest.neutral(self)
        else:
            self.coverage.update(schema_version=2, targets=[{'id':'web','platform':'web','product_type':'application'}])
            self.coverage['screens'][0].update(format='html', targets=['web'])
            (self.root/'index.md').write_text('[Spec](design-system.md)\n[Source](../PRD.md)\n[Components](components.md)\n[Catalog](mockups/catalog.html#ready)\n')
            (self.root/'components.md').write_text('[Examples](mockup/components.html)\n')
        (self.root/'mockups').rename(self.root/'mockup')
        for name in ['index.html','components.html','tokens.css']:
            p=self.root/name
            if p.exists():
                text=p.read_text().replace('mockups/','').replace('href="design-system.md"','href="../design-system.md"')
                (self.root/'mockup'/name).write_text(text)
                p.unlink()
        for p in self.root.rglob('*'):
            if p.is_file() and p.suffix in {'.md','.html'}:
                p.write_text(p.read_text().replace('mockups/','mockup/').replace('href="../tokens.css"','href="tokens.css"'))
        def paths(value):
            if isinstance(value,str):return value.replace('mockups/','mockup/')
            if isinstance(value,list):return [paths(v) for v in value]
            if isinstance(value,dict):return {k:paths(v) for k,v in value.items()}
            return value
        self.coverage=paths(self.coverage)
        self.prd.write_text(self.prd.read_text()+'| NFR-001 | Keyboard navigation |\n')
        self.coverage['source']['sha256']=hashlib.sha256(self.prd.read_bytes()).hexdigest()
        self.coverage['quality_requirements']=[{'id':'NFR-001','disposition':'cross-cutting','screens':['catalog']}]
        self.coverage['acceptance_criteria']=[{'id':'AC-001','disposition':'visual','locations':['mockup/catalog-notes.md#ready' if native else 'mockup/catalog.html#ready']}]
        (self.root/'verification.md').unlink()
        (self.root/'design-system.md').write_text('# Fixture design system\n\n## Validation and handoff\nStatic fixture checks recorded; rendered behavior is not verified.\n')
        self.save_coverage()

    def test_standard_web_auto_and_explicit(self):
        self.standard()
        self.assertEqual(self.errors(),[])
        self.assertEqual(module.check(self.root,self.prd,'standard'),[])

    def test_standard_native_without_html_or_css(self):
        self.standard(native=True)
        self.assertEqual(self.errors(),[])

    def test_missing_and_empty_spec(self):
        self.standard()
        p=self.root/'design-system.md'
        for action in [lambda:p.write_text(''),lambda:p.unlink()]:
            action()
            self.assertTrue(any('design-system.md' in e for e in self.errors()))

    def test_consolidated_validation_required(self):
        self.standard()
        for text in ['# Specification\n', '# Specification\n## Validation and handoff\n\n## Next\nBody\n']:
            (self.root/'design-system.md').write_text(text)
            self.assertTrue(any('consolidated' in e for e in self.errors()))

    def test_root_mockup_resources_rejected(self):
        self.standard()
        for name in ['old.html','old.js','old.css','old.png']:
            p=self.root/name;p.write_text('obsolete resource')
            self.assertTrue(any('under mockup/' in e for e in self.errors()))
            p.unlink()

    def test_standard_game_images(self):
        self.standard(native=True)
        self.coverage['targets'][0].update(platform='console', product_type='game');self.save_coverage()
        self.assertEqual(self.errors(),[])

    def test_standard_two_themes_one_token_authority(self):
        self.standard()
        self.coverage['targets']=[{'id':t,'platform':'web','product_type':'application'} for t in ['dark','light']]
        self.coverage['screens'][0]['targets']=['dark','light'];self.save_coverage()
        p=self.root/'tokens.json';tokens=json.loads(p.read_text());tokens['overrides']={'light':{'primitive':{'ink':'#eeeeee'}}};p.write_text(json.dumps(tokens))
        p=self.root/'mockup/tokens.css';p.write_text(p.read_text()+'\n[data-design-target="light"] { --primitive-ink: #eeeeee; }')
        self.assertEqual(self.errors(),[])
        p.write_text(p.read_text().replace('#eeeeee','#ffffff'))
        self.assertTrue(any('CSS value' in e for e in self.errors()))

    def test_standard_broken_link(self):
        self.standard()
        p=self.root/'index.md';p.write_text(p.read_text()+'[Missing](mockup/absent.html)')
        self.assertTrue(any('Broken' in e for e in self.errors()))

    def test_standard_token_drift(self):
        self.standard()
        p=self.root/'mockup/tokens.css';p.write_text(p.read_text().replace('#111111','#222222'))
        self.assertTrue(any('CSS value' in e for e in self.errors()))

    def test_missing_nfr_and_ac_dispositions(self):
        for key in ['quality_requirements','acceptance_criteria']:
            with self.subTest(key=key):
                # One setup per subtest would obscure the actual coverage edit.
                if key=='quality_requirements':self.standard()
                previous=self.coverage.pop(key);self.save_coverage()
                self.assertTrue(any(key in e for e in self.errors()))
                self.coverage[key]=previous

    def test_duplicate_nfr_disposition(self):
        self.standard()
        self.coverage['quality_requirements']*=2;self.save_coverage()
        self.assertTrue(any('Duplicate quality' in e for e in self.errors()))

    def test_unknown_ac_disposition(self):
        self.standard()
        self.coverage['acceptance_criteria'][0]['id']='AC-999';self.save_coverage()
        self.assertTrue(any('dispositions differ' in e for e in self.errors()))

    def test_nonvisual_requires_rationale(self):
        self.standard()
        self.coverage['acceptance_criteria']=[{'id':'AC-001','disposition':'technical'}];self.save_coverage()
        self.assertTrue(any('nonvisual rationale' in e for e in self.errors()))

    def test_visual_requires_mapping(self):
        self.standard()
        self.coverage['quality_requirements'][0]['screens']=[];self.save_coverage()
        self.assertTrue(any('visual mappings' in e for e in self.errors()))

    def test_location_must_be_declared_state(self):
        self.standard()
        p=self.root/'mockup/catalog.html';p.write_text(p.read_text()+'<span id="incidental">Text</span>')
        self.coverage['acceptance_criteria'][0]['locations']=['mockup/catalog.html#incidental'];self.save_coverage()
        self.assertTrue(any('declared state' in e for e in self.errors()))

    def test_duplicate_state_ids(self):
        self.standard()
        p=self.root/'mockup/catalog.html';p.write_text(p.read_text()+'<section id="ready">Duplicate</section>')
        self.assertTrue(any('Duplicate HTML IDs' in e for e in self.errors()))

    def test_nested_independent_states(self):
        self.standard()
        p=self.root/'mockup/catalog.html'
        p.write_text('<link rel="stylesheet" href="tokens.css"><main id="ready" hidden><div>Catalog</div><section id="loading">Loading</section></main>')
        self.assertTrue(any('Nested independent state loading' in e for e in self.errors()))
        p.write_text('<link rel="stylesheet" href="tokens.css"><main id="ready"><div>Catalog</div></main><section id="loading">Loading</section>')
        self.assertEqual(self.errors(),[])

    def test_nested_across_screen_entries(self):
        self.standard()
        original=self.coverage['screens'][0]
        original['states']=['ready'];original['state_locations']={'ready':'#ready'}
        other=dict(original,id='loading-flow',states=['loading'],state_locations={'loading':'#loading'})
        self.coverage['screens'].append(other)
        self.coverage['requirements'][0]['screens'].append('loading-flow');self.save_coverage()
        p=self.root/'mockup/catalog.html';p.write_text('<link rel="stylesheet" href="tokens.css"><section id="ready"><section id="loading">Loading</section></section>')
        self.assertTrue(any('Nested independent state' in e for e in self.errors()))

    def test_ordinary_nested_content_is_valid(self):
        self.standard()
        p=self.root/'mockup/catalog.html';p.write_text(p.read_text().replace('Catalog</main>','<section id="credits">Credits</section></main>'))
        self.assertEqual(self.errors(),[])

    def test_first_document_link_is_spec(self):
        self.standard()
        for name,link in [('index.md','[Components](components.md)\n'),('mockup/index.html','<a href="components.html">Components</a>')]:
            p=self.root/name;old=p.read_text();p.write_text(link+old)
            self.assertTrue(any('First document link' in e for e in self.errors()))
            p.write_text(old)

    def test_skip_and_self_links_may_precede_spec(self):
        self.standard()
        p=self.root/'mockup/index.html';p.write_text('<a href="#main">Skip</a><a href="index.html">Home</a><main id="main"></main>'+p.read_text())
        self.assertEqual(self.errors(),[])

    def test_cli_layout_modes(self):
        import subprocess
        self.standard()
        for mode in ['auto','standard','legacy']:
            result=subprocess.run([sys.executable,str(Path(module.__file__)),str(self.root),'--source',str(self.prd),'--layout',mode],capture_output=True,text=True)
            self.assertEqual(result.returncode,1 if mode=='legacy' else 0,result.stdout+result.stderr)

    def test_invalid_api_layout(self):
        self.assertEqual(module.check(self.root,self.prd,'invalid'),['Unsupported layout: invalid'])

    def test_legacy_explicit_still_passes(self):
        self.assertEqual(module.check(self.root,self.prd,'legacy'),[])

    def test_valid_legacy_supplied_dispositions_are_checked(self):
        self.coverage['acceptance_criteria']=[{'id':'AC-001','disposition':'technical','notes':'Fixture rationale.'}];self.save_coverage()
        self.assertEqual(self.errors(),[])
        self.coverage['acceptance_criteria']=[];self.save_coverage()
        self.assertTrue(any('dispositions differ' in e for e in self.errors()))




class OutputWordingTests(PackageFixture, unittest.TestCase):
    def test_caption_is_checked(self):
        path = self.root/'mockups/catalog.html'
        path.write_text(path.read_text()+'<p>Canonical design</p>')
        self.assertTrue(any('Output wording:' in error for error in self.errors()))

    def test_code_and_identifiers_are_checked(self):
        (self.root/'example.js').write_text('const emailCanonical = "example";')
        self.assertTrue(any('Output wording:' in error for error in self.errors()))


if __name__ == '__main__':
    unittest.main()
