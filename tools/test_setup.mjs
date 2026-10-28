import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';

const read = path => readFileSync(new URL('../' + path, import.meta.url), 'utf8');
const manifest = JSON.parse(read('materials/manifest.json'));

class Element {
  constructor(tag = 'div') { this.tag = tag; this.value = ''; this.children = []; this.events = {}; this.dataset = {}; }
  appendChild(child) {
    this.children.push(child);
    if (this.tag === 'select' && !this.value) this.value = child.value;
  }
  replaceChildren(...children) { this.children = children; }
  addEventListener(name, fn) { (this.events[name] ||= []).push(fn); }
  fire(name) { for (const fn of this.events[name] || []) fn({preventDefault() {}}); }
}

function fixture({url = 'http://127.0.0.1:5501/study%20folder/index.html'} = {}) {
  const elements = {};
  for (const id of ['set', 'load', 'page-links', 'status', 'launch-progress', 'open-tabs',
    'open-next', 'reset', 'open-all-hint', 'popup-help', 'setup-form']) {
    elements[id] = new Element(['set', 'load'].includes(id) ? 'select' : 'div');
  }
  elements.load.value = 'low_load';
  const events = {}, handles = [], calls = [];
  const state = {allow: Infinity};
  const unrelated = {closed: false};
  const window = {STUDY_MATERIALS: manifest, location: new URL(url),
    addEventListener(name, fn) { (events[name] ||= []).push(fn); },
    open(url, target) {
      assert.equal(target, '_blank');
      calls.push(url);
      if (handles.filter(handle => !handle.closed).length >= state.allow) return null;
      const handle = {url, closed: false, focused: false, focus() { this.focused = true; },
        close() { this.closed = true; }};
      handles.push(handle);
      return handle;
    }
  };
  vm.runInContext(read('assets/setup.js'), vm.createContext({
    window, document: {getElementById: id => elements[id], createElement: tag => new Element(tag)}, URL, console
  }));
  return {elements, handles, calls, state, unrelated, url, focus() { for (const fn of events.focus || []) fn(); }};
}

for (const set of manifest.sets) {
  for (const load of ['low_load', 'high_load']) {
    test(set.topic + '/' + load + ': popup requests follow the manifest, neutral last, without an extension', () => {
      const f = fixture(), e = f.elements;
      e.set.value = String(set.number); e.load.value = load; e.load.fire('change');
      const expected = set.launch_order[load].map(path => new URL(path, f.url).href);
      assert.equal(e['open-tabs'].disabled, false);
      assert.equal(e['page-links'].children.length, expected.length);
      assert.match(e['page-links'].children.at(-1).children[0].textContent, /Study Start/);
      e['setup-form'].fire('submit');
      assert.deepEqual(f.calls, expected);
      assert.equal(f.handles.length, load === 'low_load' ? 6 : 16);
      assert.match(f.handles.at(-1).url, /\/start.html$/);
      assert.equal(e['open-tabs'].disabled, true);
      assert.equal(e.set.disabled, true);
      assert.match(e.status.textContent, /cannot verify native tab positions/);
      e['setup-form'].fire('submit');
      assert.deepEqual(f.calls, expected);
    });
  }
}

test('blocked popup recovery resumes remaining pages without duplicates', () => {
  const f = fixture(), e = f.elements;
  e.load.value = 'high_load'; e.load.fire('change'); f.state.allow = 3;
  e['setup-form'].fire('submit');
  assert.equal(f.handles.length, 3);
  assert.equal(e['popup-help'].open, true);
  assert.equal(e['launch-progress'].textContent, '3 / 16 study tabs opened');
  assert.equal(e.set.disabled, true);
  f.state.allow = Infinity;
  e['setup-form'].fire('submit');
  assert.equal(f.handles.length, 16);
  assert.equal(new Set(f.handles.map(h => h.url)).size, 16);
  assert.match(f.handles.at(-1).url, /\/start.html$/);
});

test('Open next tab supports one-click-at-a-time preparation and focuses existing links', () => {
  const f = fixture(), e = f.elements;
  for (let i = 0; i < 6; i++) e['open-next'].fire('click');
  assert.equal(f.handles.length, 6);
  assert.equal(e['open-next'].disabled, true);
  e['page-links'].children[0].children[0].fire('click');
  assert.equal(f.handles.length, 6);
  assert.equal(f.handles[0].focused, true);
});

test('a direct link cannot skip ahead in the opening sequence', () => {
  const f = fixture(), e = f.elements;
  e['page-links'].children.at(-1).children[0].fire('click');
  assert.equal(f.handles.length, 0);
  assert.match(e.status.textContent, /listed order/);
  e['page-links'].children[0].children[0].fire('click');
  assert.equal(f.handles.length, 1);
});

test('reset closes owned popups only and closed windows are pruned on focus', () => {
  const f = fixture(), e = f.elements;
  e['setup-form'].fire('submit');
  f.handles[0].close(); f.focus();
  assert.equal(e['launch-progress'].textContent, '5 / 6 study tabs opened');
  e.reset.fire('click');
  assert.ok(f.handles.every(h => h.closed));
  assert.equal(f.unrelated.closed, false);
  assert.equal(e.set.disabled, false);
  assert.equal(e['launch-progress'].textContent, '0 / 6 study tabs opened');
});

test('direct-file setup creates valid encoded URLs and requests Study Start last', () => {
  const f = fixture({url: 'file:///Users/researcher/study%20folder/index.html'}), e = f.elements;
  e.load.value = 'high_load'; e.load.fire('change');
  e['setup-form'].fire('submit');
  assert.equal(f.handles.length, 16);
  assert.ok(f.calls.every(url => url.startsWith('file:///Users/researcher/study%20folder/')));
  assert.match(f.calls.at(-1), /\/start.html$/);
});
