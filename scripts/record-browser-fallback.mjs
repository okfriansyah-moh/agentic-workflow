import path from 'node:path';
import { pathToFileURL } from 'node:url';
const options=Object.fromEntries(process.argv.slice(2).reduce((pairs,item,index,all)=>index%2?pairs:[...pairs,[item,all[index+1]]],[]));
if(!options['--runtime']||!options['--output']||!options['--url']) throw new Error('Use --runtime PATH --output PATH --url URL');
process.env.PLAYWRIGHT_BROWSERS_PATH=path.join(path.resolve(options['--runtime']),'browsers');
const {chromium}=await import(pathToFileURL(path.join(options['--runtime'],'node_modules/playwright/index.mjs')).href);
import fs from 'node:fs/promises';
const output=path.resolve(options['--output']);
await fs.mkdir(output,{recursive:true});
const browser=await chromium.launch({headless:true});
const groups=[];
for (const [width,height] of [[1280,900],[375,812]]) {
 const context=await browser.newContext({viewport:{width,height},deviceScaleFactor:1,recordVideo:{dir:output,size:{width,height}}});
 const page=await context.newPage();const video=page.video();const started=Date.now();const cases=[];
 await context.tracing.start({screenshots:true,snapshots:true,sources:true});
 for (const variant of ['clean','bad']) {
  await page.goto(options['--url'].replace(/\/$/,'')+'/?variant='+variant);
  const caseId=variant==='clean'?'AW11-UI-01':'AW11-UI-02';
  await page.evaluate(({caseId,variant})=>{const label=document.createElement('div');label.textContent=caseId+' · '+variant;Object.assign(label.style,{position:'fixed',bottom:'10px',left:'10px',padding:'8px',background:'#122932',color:'#fff',font:'14px system-ui',zIndex:999});document.body.append(label)},{caseId,variant});
  await page.waitForTimeout(900);
  const timestamp=(Date.now()-started)/1000;
  await page.locator('button').click();
  await page.waitForTimeout(1200);
  cases.push({case_id:caseId,variant,wall_elapsed_seconds:timestamp,result:await page.locator('output').textContent()});
 }
 await context.tracing.stop({path:output+'/fallback-'+width+'.zip'});
 await context.close();await video.saveAs(output+'/fallback-'+width+'.webm');
 groups.push({viewport:{width,height},cases,video:'fallback-'+width+'.webm'});
}
await browser.close();await fs.writeFile(output+'/fallback.json',JSON.stringify({capture:'Playwright recordVideo fallback after CLI frame readability review',timestamp_basis:'Wall elapsed values require separate frame inspection to map video presentation timestamps',groups},null,2));
console.log(JSON.stringify(groups));
