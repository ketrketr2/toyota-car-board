const assert = require('node:assert/strict');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require('playwright');
(async()=>{
 const browser=await chromium.launch();
 const errors=[];
 try {
  for(const width of [1440,390]) {
   const page=await browser.newPage({viewport:{width,height:900}});
   page.on('pageerror',e=>errors.push(e.message));
   page.on('console',m=>{if(m.type()==='error'&&!/net::ERR_|Failed to load resource/.test(m.text()))errors.push(m.text());});
   for(const file of ['plain.html','signal_plain.html']) {
    await page.goto(pathToFileURL(path.join(process.argv[2],file)).href,{waitUntil:'domcontentloaded'});
    if(file==='plain.html') {
     for(const view of ['hq','car:roomy','car:sienta','car:alphard','car:voxy','car:noah','car:aqua','car:raize','car:lc250','queries','guide']) {
      await page.evaluate(v=>go(v),view);
      const text=await page.locator('#main').innerText();
      assert(!/NaN|Infinity|undefined/.test(text),view+': 無効な表示値');
     }
    } else {
     for(const view of ['hq','car','seg','cite','ga']) {
      await page.click(`[data-v=${view}]`);
      const text=await page.locator('#v-'+view).innerText();
      assert(!/NaN|Infinity|undefined/.test(text.replace(/横スクロール・NaN/g,'')),view+': 無効な表示値');
     }
     await page.click('[data-v=hq]');
     await page.click('.hp[data-st=geo]');
     assert(await page.locator('#mshade').evaluate(e=>e.classList.contains('on')),'スコア説明が開かない');
    }
   }
   await page.close();
  }
  assert.deepEqual(errors,[]);
  console.log('欠測時のブラウザ検証: OK（PC・スマホ）');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
