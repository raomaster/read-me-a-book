import adapter from '@sveltejs/adapter-auto';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://svelte.dev/docs/kit/integrations
	// for more information about preprocessors
	preprocess: vitePreprocess(),
	vitePlugin: {
		inspector: {
			toggleKeyCombo: 'alt-shift',
			holdMode: true,
			showToggleButton: 'hover'
		},         // DevTools
		onwarn: (warning, handler) => {
		if (warning.code === 'css-unused-selector') return;
		handler(warning);
    }
  },
	kit: {
		// adapter-auto only supports some environments, see https://svelte.dev/docs/kit/adapter-auto for a list.
		// If your environment is not supported, or you settled on a specific environment, switch out the adapter.
		// See https://svelte.dev/docs/kit/adapters for more information about adapters.
		adapter: adapter({
			// dónde volcará los archivos estáticos generados:
			pages: 'build',
			assets: 'build',
			// sin fallback si quieres SPA:
			fallback: null
			}
		),
	}
};

export default config;
