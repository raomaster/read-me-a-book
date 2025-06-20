<script lang="ts">
	import themeStore, { type Theme } from '$lib/store/theme.store';
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import '../app.css';
	import '$lib/i18n';
	import { waitLocale, locale as currentLocale } from 'svelte-i18n';

	onMount(async () => {
		const storedTheme = localStorage.getItem('app-theme') as Theme;

		if (storedTheme) {
			themeStore.set(storedTheme);
		} else {
			const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

			themeStore.set(prefersDark ? 'dark' : 'light');
		}


		await waitLocale()
	});

	$: {
		if ($themeStore) {
			if (browser) {
				document.documentElement.setAttribute('data-theme', $themeStore);
				localStorage.setItem('app-theme', $themeStore);
			}
		}
	}

	$: {
		if ($currentLocale && browser) {
			document.documentElement.setAttribute('lang', $currentLocale);
		}
	}
</script>

<slot />
