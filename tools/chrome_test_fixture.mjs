import assert from 'node:assert/strict';

export function fakeChrome({failAt = -1, ignoreIndex = false} = {}) {
  let nextId = 100, created = 0;
  const windows = new Map([[1, [{id: 1, index: 0, url: 'https://example.org/', pinned: false}]]]);
  const reindex = tabs => tabs.forEach((tab, index) => tab.index = index);
  const api = {
    windows: {
      async create({url}) {
        const id = nextId++, tab = {id: nextId++, index: 0, url, pinned: false, active: true};
        windows.set(id, [tab]); return {id, tabs: [tab]};
      },
      async update(id, properties) { assert.ok(windows.has(id)); return {id, ...properties}; }
    },
    tabs: {
      async get(id) {
        for (const tabs of windows.values()) {
          const found = tabs.find(tab => tab.id === id);
          if (found) return {...found};
        }
        throw new Error('Unknown tab');
      },
      async create({windowId, index, url, active}) {
        if (created++ === failAt) throw new Error('Simulated tab creation failure');
        const tab = {id: nextId++, url, pinned: false, active};
        const tabs = windows.get(windowId);
        tabs.splice(ignoreIndex ? 0 : index, 0, tab); reindex(tabs); return tab;
      },
      async query({windowId}) { return windows.get(windowId).map(tab => ({...tab})); },
      async update(id, properties) {
        for (const tabs of windows.values()) {
          const tab = tabs.find(t => t.id === id);
          if (!tab) continue;
          if (properties.active) tabs.forEach(t => t.active = false);
          Object.assign(tab, properties); return tab;
        }
        throw new Error('Unknown tab');
      },
      async remove(id) {
        for (const tabs of windows.values()) {
          const index = tabs.findIndex(tab => tab.id === id);
          if (index >= 0) { tabs.splice(index, 1); reindex(tabs); return; }
        }
        throw new Error('Already closed');
      }
    }
  };
  return {api, windows};
}
