<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { browser } from '$app/environment';
	import { onMount } from 'svelte';
	import type { Rendition } from 'epubjs';

	// Props
	export let currentRendition: Rendition | undefined;

	const fontSizes = [
		{ value: '80%', labelKey: 'reader.fontSizes.small', defaultLabel: 'Small' },
		{ value: '100%', labelKey: 'reader.fontSizes.normal', defaultLabel: 'Normal' },
		{ value: '125%', labelKey: 'reader.fontSizes.large', defaultLabel: 'Large' },
		{ value: '150%', labelKey: 'reader.fontSizes.extraLarge', defaultLabel: 'Extra Large' }
	];
	let selectedFontSize: string = '100%'; // Default font size

	function applyFontSize(size: string) {
		if (currentRendition) {
			currentRendition.themes.fontSize(size);
		}
	}

	onMount(() => {
		if (browser) {
			const storedFontSize = localStorage.getItem('epub-font-size');
			if (storedFontSize && fontSizes.some((fs) => fs.value === storedFontSize)) {
				selectedFontSize = storedFontSize;
			}
			// Initial application will be handled by the reactive statement below once rendition is available
		}
	});

	// Reactive statement to apply and store font size when it changes or rendition becomes available
	$: if (browser && currentRendition && selectedFontSize) {
		applyFontSize(selectedFontSize);
		localStorage.setItem('epub-font-size', selectedFontSize);
	}
</script>

<div class="relative w-full">
	<label for="font-size-select" class="block text-sm font-medium text-text-muted mb-1">
		{$_('reader.fontSizeLabel', { default: 'Font Size' })}
	</label>
	<select
		id="font-size-select"
		bind:value={selectedFontSize}
		class="w-full appearance-none bg-background hover:bg-surface border border-border rounded-md py-2 pl-3 pr-8 text-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary transition-colors duration-200 cursor-pointer"
	>
		{#each fontSizes as size}
			<option value={size.value}>{$_(size.labelKey, { default: size.defaultLabel })}</option>
		{/each}
	</select>
</div>