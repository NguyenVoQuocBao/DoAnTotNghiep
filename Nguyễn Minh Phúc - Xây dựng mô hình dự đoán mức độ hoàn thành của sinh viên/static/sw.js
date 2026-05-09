// Service Worker for Learning Analytics PWA
const CACHE_NAME = 'learning-analytics-v1.0.0';
const STATIC_CACHE = 'static-v1.0.0';
const DYNAMIC_CACHE = 'dynamic-v1.0.0';

// Files to cache immediately
const STATIC_FILES = [
  '/',
  '/static/css/style.css',
  '/static/manifest.json',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
  'https://cdn.jsdelivr.net/npm/chart.js',
  'https://cdn.socket.io/4.5.0/socket.io.min.js',
  'https://cdn.plot.ly/plotly-latest.min.js'
];

// Files to cache dynamically
const DYNAMIC_FILES = [
  '/student/dashboard',
  '/student/analyze',
  '/student/history',
  '/teacher/dashboard',
  '/teacher/statistics'
];

// Install event - cache static files
self.addEventListener('install', event => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('Service Worker: Caching static files');
        return cache.addAll(STATIC_FILES);
      })
      .catch(err => {
        console.error('Service Worker: Error caching static files', err);
      })
  );
  
  // Force activation
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
            console.log('Service Worker: Deleting old cache', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  
  // Take control of all pages
  self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip chrome-extension and other non-http requests
  if (!url.protocol.startsWith('http')) {
    return;
  }
  
  event.respondWith(
    caches.match(request)
      .then(cachedResponse => {
        if (cachedResponse) {
          console.log('Service Worker: Serving from cache', request.url);
          return cachedResponse;
        }
        
        // Not in cache, fetch from network
        return fetch(request)
          .then(networkResponse => {
            // Check if valid response
            if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
              return networkResponse;
            }
            
            // Clone response for caching
            const responseToCache = networkResponse.clone();
            
            // Cache dynamic content
            if (shouldCacheDynamically(request.url)) {
              caches.open(DYNAMIC_CACHE)
                .then(cache => {
                  console.log('Service Worker: Caching dynamic content', request.url);
                  cache.put(request, responseToCache);
                });
            }
            
            return networkResponse;
          })
          .catch(err => {
            console.error('Service Worker: Fetch failed', err);
            
            // Return offline page for navigation requests
            if (request.destination === 'document') {
              return caches.match('/offline.html');
            }
            
            // Return cached version or error
            return caches.match(request);
          });
      })
  );
});

// Background sync for offline actions
self.addEventListener('sync', event => {
  console.log('Service Worker: Background sync', event.tag);
  
  if (event.tag === 'analytics-sync') {
    event.waitUntil(syncAnalyticsData());
  }
});

// Push notifications
self.addEventListener('push', event => {
  console.log('Service Worker: Push received');
  
  const options = {
    body: event.data ? event.data.text() : 'New learning insights available!',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'View Dashboard',
        icon: '/static/icons/dashboard-icon.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/static/icons/close-icon.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('Learning Analytics', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
  console.log('Service Worker: Notification clicked', event.action);
  
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/student/dashboard')
    );
  } else if (event.action === 'close') {
    // Just close the notification
    return;
  } else {
    // Default action - open app
    event.waitUntil(
      clients.matchAll().then(clientList => {
        if (clientList.length > 0) {
          return clientList[0].focus();
        }
        return clients.openWindow('/');
      })
    );
  }
});

// Message handling from main thread
self.addEventListener('message', event => {
  console.log('Service Worker: Message received', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CACHE_ANALYTICS') {
    cacheAnalyticsData(event.data.payload);
  }
});

// Helper functions
function shouldCacheDynamically(url) {
  // Cache API responses and important pages
  return DYNAMIC_FILES.some(pattern => url.includes(pattern)) ||
         url.includes('/api/') ||
         url.includes('/student/') ||
         url.includes('/teacher/');
}

async function syncAnalyticsData() {
  try {
    // Get stored offline actions
    const cache = await caches.open(DYNAMIC_CACHE);
    const offlineActions = await cache.match('/offline-actions');
    
    if (offlineActions) {
      const actions = await offlineActions.json();
      
      // Process each offline action
      for (const action of actions) {
        try {
          await fetch(action.url, {
            method: action.method,
            headers: action.headers,
            body: action.body
          });
          console.log('Service Worker: Synced offline action', action);
        } catch (err) {
          console.error('Service Worker: Failed to sync action', action, err);
        }
      }
      
      // Clear processed actions
      await cache.delete('/offline-actions');
    }
  } catch (err) {
    console.error('Service Worker: Sync failed', err);
  }
}

async function cacheAnalyticsData(data) {
  try {
    const cache = await caches.open(DYNAMIC_CACHE);
    const response = new Response(JSON.stringify(data), {
      headers: { 'Content-Type': 'application/json' }
    });
    await cache.put('/cached-analytics', response);
    console.log('Service Worker: Analytics data cached');
  } catch (err) {
    console.error('Service Worker: Failed to cache analytics', err);
  }
}

// Periodic background sync (if supported)
if ('periodicSync' in self.registration) {
  self.addEventListener('periodicsync', event => {
    if (event.tag === 'analytics-update') {
      event.waitUntil(updateAnalyticsCache());
    }
  });
}

async function updateAnalyticsCache() {
  try {
    const response = await fetch('/api/analytics-summary');
    if (response.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      await cache.put('/api/analytics-summary', response.clone());
      console.log('Service Worker: Analytics cache updated');
    }
  } catch (err) {
    console.error('Service Worker: Failed to update analytics cache', err);
  }
}

// Error handling
self.addEventListener('error', event => {
  console.error('Service Worker: Error', event.error);
});

self.addEventListener('unhandledrejection', event => {
  console.error('Service Worker: Unhandled rejection', event.reason);
});

console.log('Service Worker: Loaded successfully');