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
		allowedHosts: ['leeme.mooo.com']
	},
	preview: {
		host: true,
		port: 80
  	},
	build: {
		outDir: 'build'
	}
});
