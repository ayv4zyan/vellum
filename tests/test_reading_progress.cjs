// Run: npm install --no-save linkedom && node tests/test_reading_progress.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {parseHTML} = require('linkedom');
const root = path.resolve(process.argv[2] || path.join(__dirname, '..'));
const source = fs.readFileSync(path.join(root, 'reader.js'), 'utf8');

async function run({mobile = false, article = true} = {}) {
  const {document} = parseHTML(`<html><body><header class="book-top-bar"></header>${article ? '<article class="chapter-content"></article>' : ''}</body></html>`);
  const callbacks = {};
  const frames = [];
  const window = {location:{pathname:'/chapter.html', hash:''}, scrollY:0, innerHeight:640,
    matchMedia:() => ({matches:!mobile}),
    addEventListener:(name, callback) => (callbacks[name] ||= []).push(callback)};
  const topBar = document.querySelector('.book-top-bar');
  topBar.offsetHeight = 48;
  let height = 2400;
  if (article) document.querySelector('.chapter-content').getBoundingClientRect = () => ({top:100-window.scrollY, height});
  const storage = {getItem:() => null, setItem:() => {}};
  vm.runInNewContext(source, {document, window, localStorage:storage, sessionStorage:storage,
    requestAnimationFrame:callback => {frames.push(callback); return frames.length;}, setTimeout, clearTimeout});
  const fire = name => {for (const callback of callbacks[name] || []) callback(); while (frames.length) frames.shift()();};
  const track = document.querySelector('.reading-progress');
  if (!article) { assert.equal(track, null, 'catalog must not show reading progress'); return; }
  assert.ok(track, 'missing top reading progress bar');
  assert.equal(track.getAttribute('role'), 'progressbar');
  const fill = track.querySelector('.reading-progress-fill');
  assert.ok(fill, 'missing progress fill');
  const initial = Number(track.getAttribute('aria-valuenow'));
  assert.ok(initial > 0 && initial < 100);
  window.scrollY = 500; fire('scroll');
  assert.ok(Number(track.getAttribute('aria-valuenow')) > initial, 'progress advances on scroll');
  if (mobile) assert.ok(topBar.classList.contains('is-hidden'));
  assert.equal(track.parentElement, document.body, 'progress must be outside auto-hidden navigation');
  window.scrollY = 2000; fire('scroll');
  assert.equal(track.getAttribute('aria-valuenow'), '100');
  window.scrollY = 0; fire('scroll');
  assert.equal(Number(track.getAttribute('aria-valuenow')), initial);
  window.innerHeight = 800; fire('resize');
  assert.ok(Number(track.getAttribute('aria-valuenow')) > initial, 'progress updates on resize');
  height = 3000; fire('load');
  assert.equal(track.getAttribute('aria-valuenow'), '23', 'progress recalculates after images load');
  assert.ok(parseFloat(fill.style.width) > 0);
}

(async () => {
  await run(); await run({mobile:true}); await run({article:false});
  console.log('PASS: reading progress exists and updates on scroll, resize and load; stays outside hidden mobile navigation; absent from catalog');
})().catch(error => {console.error('FAIL:', error.message); process.exitCode = 1;});
