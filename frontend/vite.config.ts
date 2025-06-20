import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
	plugins: [
		tailwindcss(),
		sveltekit(),
	],
	server: {
		host: true,      // equivalente a "0.0.0.0"
		port: 5173       // cámbialo si ya tienes algo ocupando ese puerto
	},
	preview: {
		host: true,
		port: 4173
  }
});
