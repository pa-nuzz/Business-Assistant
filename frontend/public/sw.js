// Service Worker for AEIOU AI PWA
// Handles offline support, background sync, and push notifications

const CACHE_NAME = 'aeiou-v1';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/dashboard',
  '/tasks',
  '/documents',
  '/chat',
];

const API_CACHE = 'aeiou-api-v1';
const API_ROUTES = [
  /\/api\/v1\/(tasks|documents|conversations)/,
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    }).then(() => {
      return self.skipWaiting();
    })
  );
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME && name !== API_CACHE)
          .map((name) => caches.delete(name))
      );
    }).then(() => {
      return self.clients.claim();
    })
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests and non-HTTP(S) URLs
  if (request.method !== 'GET') return;
  if (!url.protocol.startsWith('http')) return;

  // Handle API requests with stale-while-revalidate strategy
  if (API_ROUTES.some((route) => route.test(url.pathname))) {
    event.respondWith(apiStrategy(request));
    return;
  }

  // Handle static assets with cache-first strategy
  if (isStaticAsset(url.pathname)) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // Default: network-first with cache fallback
  event.respondWith(networkFirst(request));
});

// Background Sync - queue failed requests
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-tasks') {
    event.waitUntil(syncTasks());
  } else if (event.tag === 'sync-documents') {
    event.waitUntil(syncDocuments());
  }
});

// Push Notifications
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : {};
  
  const options = {
    body: data.body || 'You have a new notification',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png',
    tag: data.tag || 'default',
    data: data.data || {},
    actions: data.actions || [
      { action: 'open', title: 'Open' },
      { action: 'dismiss', title: 'Dismiss' }
    ],
    requireInteraction: data.requireInteraction || false,
  };

  event.waitUntil(
    self.registration.showNotification(
      data.title || 'AEIOU AI',
      options
    )
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const { action, notification } = event;
  const data = notification.data || {};

  if (action === 'dismiss') return;

  event.waitUntil(
    self.clients.matchAll({ type: 'window' }).then((clientList) => {
      const url = data.url || '/';
      
      // Focus existing client if open
      for (const client of clientList) {
        if (client.url === url && 'focus' in client) {
          return client.focus();
        }
      }
      
      // Open new window
      if (self.clients.openWindow) {
        return self.clients.openWindow(url);
      }
    })
  );
});

// Cache strategies
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    return cached || offlineResponse();
  }
}

async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    const cached = await caches.match(request);
    return cached || offlineResponse();
  }
}

async function apiStrategy(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(API_CACHE);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    const cached = await caches.match(request);
    if (cached) {
      // Return cached data with stale header
      const headers = new Headers(cached.headers);
      headers.set('X-Cache', 'stale');
      
      return new Response(cached.body, {
        status: 200,
        statusText: 'OK',
        headers,
      });
    }
    return offlineResponse();
  }
}

function offlineResponse() {
  return new Response(
    JSON.stringify({
      error: 'You are offline',
      offline: true,
      message: 'Some features may be unavailable. Please check your connection.',
    }),
    {
      status: 503,
      headers: {
        'Content-Type': 'application/json',
        'X-Offline': 'true',
      },
    }
  );
}

function isStaticAsset(pathname) {
  return (
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/static/') ||
    pathname.startsWith('/icons/') ||
    pathname.endsWith('.js') ||
    pathname.endsWith('.css') ||
    pathname.endsWith('.png') ||
    pathname.endsWith('.jpg') ||
    pathname.endsWith('.svg')
  );
}

// Background sync functions
async function syncTasks() {
  const db = await openIndexedDB();
  const tx = db.transaction('pending_tasks', 'readonly');
  const store = tx.objectStore('pending_tasks');
  const requests = await store.getAll();

  for (const req of requests) {
    try {
      await fetch(req.url, {
        method: req.method,
        headers: req.headers,
        body: req.body,
      });
      
      // Remove from pending
      const deleteTx = db.transaction('pending_tasks', 'readwrite');
      deleteTx.objectStore('pending_tasks').delete(req.id);
      await deleteTx.complete;
    } catch (error) {
      console.error('Sync failed for task:', req.id, error);
    }
  }
}

async function syncDocuments() {
  // Similar to syncTasks but for documents
  console.log('Document sync triggered');
}

function openIndexedDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('aeiou-offline', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      
      if (!db.objectStoreNames.contains('pending_tasks')) {
        db.createObjectStore('pending_tasks', { keyPath: 'id', autoIncrement: true });
      }
      
      if (!db.objectStoreNames.contains('pending_documents')) {
        db.createObjectStore('pending_documents', { keyPath: 'id', autoIncrement: true });
      }
      
      if (!db.objectStoreNames.contains('cache_data')) {
        db.createObjectStore('cache_data', { keyPath: 'key' });
      }
    };
  });
}
