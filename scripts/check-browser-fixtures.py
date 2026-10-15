import argparse,hashlib,json,pathlib,subprocess,time,shutil
parser=argparse.ArgumentParser(description='Capture clean/broken workflow fixtures using a pinned installed CLI.')
parser.add_argument('--url',default='http://127.0.0.1:45021')
parser.add_argument('--output',type=pathlib.Path,required=True)
parser.add_argument('--cli',default='playwright-cli')
parser.add_argument('--session',default='aw-fixture-review')
args=parser.parse_args()
ROOT=pathlib.Path(__file__).resolve().parents[1]/'tests/fixtures/browser'
OUT=args.output.resolve();OUT.mkdir(parents=True,exist_ok=True)
design=json.loads((ROOT/'design.json').read_text());expected=design['expected']
CLI=[shutil.which(args.cli) or args.cli,'-s='+args.session]
config=OUT/'cli.config.json'
config.write_text(json.dumps({'outputDir':str(OUT/'native-artifacts'),'browser':{'browserName':'chromium','launchOptions':{'headless':True},'contextOptions':{'deviceScaleFactor':1,'viewport':{'width':1280,'height':900}}}}))
records=[]
def run(*args):
 result=subprocess.run(CLI+list(args)+['--json'],cwd=OUT,capture_output=True,text=True,timeout=60)
 record={'argv':list(args),'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'at':time.time()}
 records.append(record)
 (OUT/'commands.json').write_text(json.dumps(records,indent=2))
 if result.returncode: raise RuntimeError(record)
 return json.loads(result.stdout)
run('open',args.url,'--browser=chromium','--config='+str(config))
run('tracing-start')
run('video-start',str(OUT/'review.webm'),'--size=1280x900','--fps=25','--cursor')
run('video-show-actions')
started=time.time(); cases=[]
for variant in ['clean','bad']:
 for viewport in design['viewports']:
  width,height=viewport['width'],viewport['height']
  case=f'{variant}-{width}'
  run('video-chapter',f'AW11-UI-{1 if variant=="clean" else 2:02d}: {case}','--duration=700')
  run('resize',str(width),str(height))
  run('goto',args.url.rstrip('/')+'/?variant='+variant)
  result=run('run-code',"""async page => {
    const before = await page.evaluate(() => {
      const card = document.querySelector('main');
      const p = document.querySelector('p');
      const b = document.querySelector('button');
      const ps = getComputedStyle(p);
      return { viewport: innerWidth, device_scale: devicePixelRatio, document_width: document.documentElement.scrollWidth,
        card_width: card.getBoundingClientRect().width, paragraph_font: parseFloat(ps.fontSize),
        paragraph_color: ps.color, background: getComputedStyle(card).backgroundColor,
        accessible_name: b.getAttribute('aria-label') || [...b.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join('').trim() };
    });
    await page.locator('button').click();
    return {...before, result: await page.locator('output').textContent(),
      accessible_button_count: await page.getByRole('button', {name:__EXPECTED_BUTTON__, exact:true}).count()};
  }""".replace('__EXPECTED_BUTTON__',json.dumps(expected['button_accessible_name'])))
  data=json.loads(result['result']); data.update(case=case,timestamp=time.time()-started)
  data['findings']=[]
  if not expected['mobile_horizontal_overflow'] and data['document_width']>data['viewport']: data['findings'].append('horizontal-overflow')
  if data['card_width']>expected['max_width']: data['findings'].append('excessive-card-width')
  def luminance(rgb):
   import re
   values=[int(x)/255 for x in re.findall(r'\d+',rgb)[:3]]
   return sum(w*(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4) for w,v in zip([.2126,.7152,.0722],values))
  a,b=sorted([luminance(data['paragraph_color']),luminance(data['background'])]);data['contrast']=(b+.05)/(a+.05)
  if data['contrast']<expected['paragraph_contrast_minimum']: data['findings'].append('insufficient-contrast')
  if data['paragraph_font']<expected['minimum_body_font_px']: data['findings'].append('unreadable-body-size')
  if data['accessible_button_count']!=1: data['findings'].append('missing-accessible-name')
  if data['result']!=expected['button_result']: data['findings'].append('failing-interaction')
  run('screenshot','--filename='+str(OUT/(case+'.png')))
  cases.append(data)
run('video-stop')
trace=run('tracing-stop')
run('console');run('requests')
run('close')
(OUT/'results.json').write_text(json.dumps({'cases':cases,'trace':trace,'started':started,'design_sha256':hashlib.sha256((ROOT/'design.json').read_bytes()).hexdigest()},indent=2))
if any(c['findings'] for c in cases if c['case'].startswith('clean')): raise SystemExit('Clean fixture failed required design checks')
required={'insufficient-contrast','unreadable-body-size','missing-accessible-name','failing-interaction'}
if any(not required<=set(c['findings']) for c in cases if c['case'].startswith('bad')): raise SystemExit('Broken fixture defects were not detected')
narrowest=min(v['width'] for v in design['viewports'])
if not any(c['case']==f'bad-{narrowest}' and 'horizontal-overflow' in c['findings'] for c in cases): raise SystemExit('Broken mobile overflow was not detected')
print(json.dumps(cases,indent=2))
