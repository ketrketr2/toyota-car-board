// ブラウザに依存せず、集計結果で実際のテンプレート関数を実行する。
// レイアウト検証は既存のPlaywright検証が担当する。
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const board = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const signal = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
function surface() {
  const elements = new Map();
  function element(id) {
    if (!elements.has(id)) elements.set(id, {
      innerHTML: '', style: {}, dataset: {}, value: '',
      classList: {add(){}, remove(){}, toggle(){}, contains(){return false;}},
      addEventListener(){}, querySelectorAll(){return [];},
      querySelector(s){return element(id+s);}, getAttribute(){return '';}
    });
    return elements.get(id);
  }
  const document = {querySelector:element, getElementById:element,
    querySelectorAll(){return [];}, addEventListener(){}, body:element('body'),
    createElement:element};
  const context = vm.createContext({document, window:{DATA:board,addEventListener(){},scrollTo(){}},
    addEventListener(){}, requestAnimationFrame(){}, location:{hash:''},
    localStorage:{getItem(){return null;}}, console, innerWidth:1440, innerHeight:900});
  return {context, elements};
}
function valid(html) {
  assert(!/NaN|Infinity|undefined/.test(html.replace(/横スクロール・NaN/g,'')),
    '未定義の数値または文字列を描画した: '+html.slice(Math.max(0,html.search(/NaN|Infinity|undefined/)-80),html.search(/NaN|Infinity|undefined/)+80));
}
const b = surface();
const helpers = fs.readFileSync(path.join(root,'tools/part_js1.js'),'utf8');
vm.runInContext(helpers, b.context);
valid(vm.runInContext('rHQ()',b.context));
for (const pts of ['[]','[{x:0,y:0,label:"ゼロ",col:"red",id:"roomy"}]','[{x:null,y:null}]']) {
  valid(vm.runInContext(`scatter(${pts},560,420)`,b.context));
}
const s = surface();
let source = fs.readFileSync(path.join(root,'tools/signal_template.html'),'utf8');
source = source.slice(source.indexOf('<script>')+8,source.lastIndexOf('</script>'))
  .replace('__DATA__',JSON.stringify(signal)).replace('__IMG__','{}');
vm.runInContext(source,s.context);
vm.runInContext("showStat('geo')",s.context);
for (const el of s.elements.values()) valid(el.innerHTML);
console.log('欠測時の描画ロジック: OK');
