<script lang="ts">
	import themeStore, { type Theme } from '$lib/store/theme.store';
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import '../app.css';

	onMount(() => {
		const storedTheme = localStorage.getItem('app-theme') as Theme;

		if (storedTheme) {
			themeStore.set(storedTheme);
		} else {
			const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

			themeStore.set(prefersDark ? 'dark' : 'light');
		}
	});

	$: {
		if ($themeStore) {
			if (browser) {
				document.documentElement.setAttribute('data-theme', $themeStore);
				localStorage.setItem('app-theme', $themeStore);
			}
		}
	}
</script>

<slot />
