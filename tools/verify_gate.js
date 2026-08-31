const fs = require('fs');
const { chromium } = require('playwright');
const PW_EXE = process.env.PW_CHROME || '/opt/pw-browsers/chromium';
const LAUNCH = fs.existsSync(PW_EXE) ? { executablePath: PW_EXE } : {};
(async () => {
  const b = await chromium.launch(LAUNCH);
  const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
  const errs = [];
  p.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const GATE_FILE = process.env.GATE_FILE || 'index_new.html';
  await p.goto('file://'+process.cwd()+'/'+GATE_FILE, { waitUntil: 'load' });
  await p.waitForTimeout(300);
  // 誤PW
  await p.fill('#u', 'toyota'); await p.fill('#p', 'wrong');
  await p.click('#b'); await p.waitForTimeout(1800);
  const bad = await p.evaluate(() => document.querySelector('#e') ? document.querySelector('#e').textContent : '');
  console.log('誤PW時:', bad || '(空)');
  if (!bad.includes('正しくありません')) errs.push('wrong-pw did not show error');
  // 正PW
  await p.fill('#p', 'toyota2026');
  await p.click('#b'); await p.waitForTimeout(3200);
  const ok = await p.evaluate(() => ({
    main: (document.querySelector('#main')||document.querySelector('.wrap')||document.body).innerHTML.length,
    title: document.title,
    txt: ((document.querySelector('#main')||document.querySelector('.wrap')||document.body).innerText||'').slice(0, 70),
    svg: document.querySelectorAll('#main svg').length,
  }));
  console.log('復号後:', JSON.stringify(ok));
  if (ok.main < 5000) errs.push('decrypt failed / main empty');
  await p.screenshot({ path: process.cwd()+'/s_gate_after.png' });
  // ナビ遷移
  await p.evaluate(() => { if (typeof go === 'function') go('car:raize'); });
  await p.waitForTimeout(400);
  const nav = await p.evaluate(() => (((document.querySelector('#main')||document.querySelector('.wrap')||document.body).innerText)||'').slice(0, 40));
  console.log('遷移後:', nav.replace(/\n/g, ' '));
  await b.close();
  console.log(errs.length ? 'ERRORS:\n' + errs.join('\n') : 'ERRORS: none');
  process.exit(errs.length ? 1 : 0);
})();
