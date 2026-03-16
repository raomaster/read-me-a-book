import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { SvelteKitPWA } from '@vite-pwa/sveltekit';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [
		tailwindcss(),
		sveltekit(),
		SvelteKitPWA({
			srcDir: 'src',
			strategies: 'generateSW',
			registerType: 'autoUpdate',
			manifest: false,
			useCredentials: true,
			includeAssets: ['icon-180.png', 'icon-192.png', 'icon-512.png', 'favicon.png'],
			workbox: {
				globPatterns: ['**/*.{js,css,html,ico,png,svg,webp,woff,woff2}'],
				navigateFallback: '/',
				navigateFallbackDenylist: [/^\/api\//],
				runtimeCaching: [
					{
						urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
						handler: 'CacheFirst',
						options: { cacheName: 'google-fonts-cache', expiration: { maxEntries: 10, maxAgeSeconds: 60 * 60 * 24 * 365 } }
					},
					{
						urlPattern: /^https:\/\/.*\/api\/.*/i,
						handler: 'NetworkFirst',
						options: { cacheName: 'api-cache', expiration: { maxEntries: 50, maxAgeSeconds: 60 * 5 } }
					}
				]
			},
			devOptions: {
				enabled: false
			}
		  })
	],
	server: {
		host: true,      // equivalente a "0.0.0.0"
		port: 80,       // cámbialo si ya tienes algo ocupando ese puerto
		allowedHosts: ['leeme.mooo.com', 'frontend-1061461444755.us-central1.run.app', 'voxenfy.com']
	},
	preview: {
		host: true,
		port: 80,
		allowedHosts: ['leeme.mooo.com', 'frontend-1061461444755.us-central1.run.app', 'voxenfy.com']
  	},
	build: {
		outDir: 'build'
	}
});
