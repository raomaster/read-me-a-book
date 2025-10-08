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
			registerType: 'autoUpdate'
		  })
	],
	server: {
		host: true,      // equivalente a "0.0.0.0"
		port: 80,       // cámbialo si ya tienes algo ocupando ese puerto
		allowedHosts: ['leeme.mooo.com', 'frontend-1061461444755.us-central1.run.app']
	},
	preview: {
		host: true,
		port: 80,
		allowedHosts: ['leeme.mooo.com', 'frontend-1061461444755.us-central1.run.app']
  	},
	build: {
		outDir: 'build'
	}
});
