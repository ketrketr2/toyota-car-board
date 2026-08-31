const fs = require('fs');
const { chromium } = require('playwright');
const PW_EXE = process.env.PW_CHROME || '/opt/pw-browsers/chromium';
const LAUNCH = fs.existsSync(PW_EXE) ? { executablePath: PW_EXE } : {};
(async () => {
  const b = await chromium.launch(LAUNCH);
  const errs = [];
  for (const w of [[1440, 900], [390, 844]]) {
    const p = await b.newPage({ viewport: { width: w[0], height: w[1] } });
    p.on('pageerror', e => errs.push(`[${w[0]}] pageerror: ${e.message}`));
    p.on('console', m => {
      const t = m.text();
      if (m.type() === 'error' && !/net::ERR_|Failed to load resource/.test(t)) errs.push(`[${w[0]}] console: ${t}`);
    });
    await p.goto('file://' + process.cwd() + '/signal_plain.html', { waitUntil: 'load' });
    await p.waitForTimeout(700);
    for (const v of ['hq', 'car', 'seg', 'cite', 'ga']) {
      await p.click(`[data-v=${v}]`);
      await p.waitForTimeout(280);
      const info = await p.evaluate(vv => {
        const el = document.querySelector('#v-' + vv);
        return { len: el ? el.innerHTML.length : 0,
                 ow: document.documentElement.scrollWidth > window.innerWidth + 2,
                 txt: el ? el.innerText.slice(0, 40) : '' };
      }, v);
      if (info.len < 500) errs.push(`[${w[0]}] ${v}: view too small (${info.len})`);
      if (info.ow) errs.push(`[${w[0]}] ${v}: H-OVERFLOW`);
      console.log(`[${w[0]}] ${v.padEnd(5)} len=${String(info.len).padStart(7)} ${info.txt.replace(/\n/g, ' ')}`);
    }
    if (w[0] === 1440) {
      const nan = await p.evaluate(() => {
        const t = document.body.innerText;
        return { nan: /(?<![A-Za-z])NaN(?![A-Za-z])/.test(t.replace(/横スクロール・NaN/g, '')), und: t.includes('undefined') };
      });
      if (nan.nan) errs.push('NaN in text');
      if (nan.und) errs.push('undefined in text');
      await p.click('[data-v=hq]'); await p.waitForTimeout(250);
      await p.click('.hp[data-st=geo]'); await p.waitForTimeout(350);
      const modal = await p.evaluate(() => document.querySelector('#mshade') && document.querySelector('#mshade').classList.contains('on'));
      if (!modal) errs.push('geo modal did not open');
      await p.keyboard.press('Escape');
      await p.click('[data-v=car]'); await p.waitForTimeout(300);
      await p.click('#qtable tbody tr'); await p.waitForTimeout(400);
      const qd = await p.evaluate(() => document.querySelector('#mshade').classList.contains('on'));
      if (!qd) errs.push('query detail modal did not open');
      await p.keyboard.press('Escape');
    }
    await p.close();
  }
  await b.close();
  console.log(errs.length ? 'SIGNAL ERRORS:\n' + errs.join('\n') : 'SIGNAL ERRORS: none');
  process.exit(errs.length ? 1 : 0);
})();
