class OfflineSyncManager {
  private db: IDBDatabase | null = null;
  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('aeiou-offline', 1);
      request.onerror = () => reject(request.error);
      request.onsuccess = () => { this.db = request.result; resolve(); };
      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains('pending')) {
          db.createObjectStore('pending', { keyPath: 'id', autoIncrement: true });
        }
        if (!db.objectStoreNames.contains('cache')) {
          db.createObjectStore('cache', { keyPath: 'key' });
        }
      };
    });
  }
  async queueRequest(req: { url: string; method: string; headers: Record<string,string>; body: string; type: string }): Promise<number> {
    if (!this.db) await this.init();
    return new Promise((resolve, reject) => {
      const tx = this.db!.transaction('pending', 'readwrite');
      const store = tx.objectStore('pending');
      const data = { ...req, timestamp: Date.now(), attempts: 0 };
      const r = store.add(data);
      r.onsuccess = () => { this.registerSync(`sync-${req.type}s`); resolve(r.result as number); };
      r.onerror = () => reject(r.error);
    });
  }
  async cacheResponse(key: string, data: unknown, ttl = 5): Promise<void> {
    if (!this.db) await this.init();
    return new Promise((resolve, reject) => {
      const tx = this.db!.transaction('cache', 'readwrite');
      const store = tx.objectStore('cache');
      const r = store.put({ key, data, timestamp: Date.now(), expiresAt: Date.now() + ttl * 60000 });
      r.onsuccess = () => resolve();
      r.onerror = () => reject(r.error);
    });
  }
  async getCached<T>(key: string): Promise<T | null> {
    if (!this.db) await this.init();
    return new Promise((resolve, reject) => {
      const tx = this.db!.transaction('cache', 'readonly');
      const r = tx.objectStore('cache').get(key);
      r.onsuccess = () => { const d = r.result; resolve(d && d.expiresAt > Date.now() ? d.data : null); };
      r.onerror = () => reject(r.error);
    });
  }
  private async registerSync(tag: string): Promise<void> {
    if ('serviceWorker' in navigator && 'SyncManager' in window) {
      try { const reg = await navigator.serviceWorker.ready; await (reg as any).sync.register(tag); } catch (e) { console.warn('Sync failed', e); }
    }
  }
}
export const offlineSync = new OfflineSyncManager();
