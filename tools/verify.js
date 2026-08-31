const fs = require('fs');
const { chromium } = require('playwright');
const PW_EXE = process.env.PW_CHROME || '/opt/pw-browsers/chromium';
const LAUNCH = fs.existsSync(PW_EXE) ? { executablePath: PW_EXE } : {};
(async () => {
  const b = await chromium.launch(LAUNCH);
  const errs = [];
  const views = ['hq', 'car:roomy', 'car:sienta', 'car:alphard', 'car:voxy', 'car:noah',
                 'car:aqua', 'car:raize', 'car:lc250', 'queries', 'guide'];
  for (const w of [[1440, 900], [390, 844]]) {
    const p = await b.newPage({ viewport: { width: w[0], height: w[1] } });
    p.on('pageerror', e => errs.push(`[${w[0]}] pageerror: ${e.message}`));
    p.on('console', m => {
      const t = m.text();
      // フォントCDNなど外部リソースの取得失敗は描画の正否と無関係なので除外する
      if (m.type() === 'error' && !/net::ERR_|Failed to load resource/.test(t)) errs.push(`[${w[0]}] console: ${t}`);
    });
    for (const v of views) {
      await p.goto('file://'+process.cwd()+'/plain.html#' + v, { waitUntil: 'load' });
      await p.waitForTimeout(230);
      const info = await p.evaluate(() => {
        const m = document.querySelector('#main');
        return { len: m ? m.innerHTML.length : 0,
                 txt: (m ? m.innerText : '').slice(0, 60),
                 ow: document.documentElement.scrollWidth > window.innerWidth + 2,
                 sw: document.documentElement.scrollWidth, iw: window.innerWidth,
                 nan: (m ? m.innerText : '').includes('NaN') || (m ? m.innerText : '').includes('undefined'),
                 svg: document.querySelectorAll('#main svg').length };
      });
      if (info.len < 600) errs.push(`[${w[0]}] ${v}: main too small (${info.len})`);
      if (info.ow) errs.push(`[${w[0]}] ${v}: H-OVERFLOW ${info.sw}>${info.iw}`);
      if (info.nan) errs.push(`[${w[0]}] ${v}: NaN/undefined in text`);
      console.log(`[${w[0]}] ${v.padEnd(12)} len=${String(info.len).padStart(6)} svg=${info.svg} ${info.txt.replace(/\n/g, ' ')}`);
    }
    // modal + sort interactions on desktop only
    if (w[0] === 1440) {
      await p.goto('file://'+process.cwd()+'/plain.html#car:roomy', { waitUntil: 'load' });
      await p.waitForTimeout(200);
      await p.evaluate(() => help('funnel'));
      await p.waitForTimeout(150);
      const mo = await p.evaluate(() => document.querySelector('#mback').classList.contains('on'));
      if (!mo) errs.push('modal did not open');
      await p.evaluate(() => closeModal());
      await p.evaluate(() => sortQ('roomy', 1));
      await p.waitForTimeout(120);
      const rows = await p.evaluate(() => document.querySelectorAll('#qt_roomy tbody tr').length);
      if (rows < 50) errs.push(`sortQ rows=${rows}`);
      console.log('modal OK, sort rows=', rows);
      await p.screenshot({ path: process.cwd()+'/s_hq.png', fullPage: false });
      await p.goto('file://'+process.cwd()+'/plain.html#hq', { waitUntil: 'load' });
      await p.waitForTimeout(300);
      await p.screenshot({ path: process.cwd()+'/s_hq_full.png', fullPage: true });
      await p.goto('file://'+process.cwd()+'/plain.html#car:raize', { waitUntil: 'load' });
      await p.waitForTimeout(300);
      await p.screenshot({ path: process.cwd()+'/s_car.png', fullPage: true });
    } else {
      await p.goto('file://'+process.cwd()+'/plain.html#car:roomy', { waitUntil: 'load' });
      await p.waitForTimeout(250);
      await p.screenshot({ path: process.cwd()+'/s_mobile.png', fullPage: false });
    }
    await p.close();
  }
  await b.close();
  console.log(errs.length ? 'ERRORS:\n' + errs.join('\n') : 'ERRORS: none');
  process.exit(errs.length ? 1 : 0);
})();
