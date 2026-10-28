import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {launchBlock, removeOwnedTabs} from '../study-extension/launch.mjs';

const manifest = JSON.parse(readFileSync(new URL('../materials/manifest.json', import.meta.url)));

import {fakeChrome} from './chrome_test_fixture.mjs';

for (const set of manifest.sets) {
  for (const load of ['low_load', 'high_load']) {
    test(`${set.topic}: ${load} creates the manifest order and selects neutral last`, async () => {
      const {api, windows} = fakeChrome();
      const urls = set.launch_order[load].map(path => new URL(path, 'http://127.0.0.1:5501/').href);
      const result = await launchBlock(api, urls);
      const tabs = windows.get(result.windowId);
      assert.deepEqual(tabs.map(tab => tab.url), urls);
      assert.equal(tabs.length, load === 'low_load' ? 6 : 16);
      assert.equal(tabs.at(-1).active, true);
      assert.equal(tabs.filter(tab => tab.active).length, 1);
      for (const page of set.pages.filter(page => page.target_id)) {
        const expected = page[load === 'low_load' ? 'low_load_position' : 'high_load_position'];
        assert.equal(tabs[expected - 1].url, new URL(page.path, 'http://127.0.0.1:5501/').href);
      }
      // A tab the researcher adds later must survive the launcher's reset.
      tabs.push({id: 9999, url: 'https://example.net/', index: tabs.length});
      await removeOwnedTabs(api, result.tabIds);
      assert.deepEqual(tabs.map(tab => tab.id), [9999]);
      assert.equal(windows.get(1)[0].url, 'https://example.org/');
    });
  }
}

test('partial creation failure cleans up only launcher-owned tabs', async () => {
  const {api, windows} = fakeChrome({failAt: 2});
  await assert.rejects(launchBlock(api, ['a', 'b', 'c', 'd']), /creation failure/);
  assert.equal([...windows.values()].flat().length, 1);
  assert.equal(windows.get(1)[0].id, 1);
});

test('incorrect native insertion is rejected and rolled back', async () => {
  const {api, windows} = fakeChrome({ignoreIndex: true});
  await assert.rejects(launchBlock(api, ['a', 'b', 'c']), /could not be verified/);
  assert.equal([...windows.values()].flat().length, 1);
});
