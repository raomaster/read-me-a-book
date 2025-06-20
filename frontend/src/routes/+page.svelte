<script lang="ts">
	import ThemeSwitcher from "$lib/components/ThemeSwitcher.svelte";
	import { bookStore } from "$lib/store/book.store";
	import { clickOutside } from "$lib/actions/clickOutside.action";
	import LanguageSwitcher from "$lib/components/LanguageSwitcher.svelte";
	import { _ } from "svelte-i18n";
 

	let fileInput: HTMLInputElement;
	let isMenuOpen = false;

	function closeMenu() {
		isMenuOpen = false;
	}



	async function handleFileSelect(event: Event) {
		const target = event.target as HTMLInputElement;
		if (target.files && target.files[0]){
			const file = target.files[0]
			await bookStore.addBook(file);
		}
	}
	// Look for every change in bookstorage
	$: {
		if($bookStore) {
			console.log($bookStore);
		}
	}
</script>

<svelte:head>
	<title>{$_("pageTitle")}</title>
	<meta name="description" content={$_('metaDescription')} />
</svelte:head>
<div class="min-h-screen bg-background p-4 sm:p-6 lg:p-8">
	<section class="w-full max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
		<!-- Contenedor principal de contenido, consistente con el diseño aprobado -->
		<div class="bg-surface rounded-2xl shadow-lg p-6">
			<header class="flex justify-between items-center gap-4 border-b border-border pb-5">
				<h1 class="text-4xl font-bold text-text-base">{$_("pageTitle")}  ({$bookStore.length})</h1>
				<div class="flex items-center gap-3">
					<!-- Botón Principal "Import" (Sin cambios, ya era correcto) -->
					<label for="file-upload" class="filled-button whitespace-nowrap cursor-pointer">
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
						</svg>
						{$_("importButton")}  
						<!-- Icono de libro con símbolo de carga -->
						<svg fill="currentColor" version="1.1" id="Capa_1" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 ml-2" xmlns:xlink="http://www.w3.org/1999/xlink" 
							viewBox="0 0 87.261 87.261"
							xml:space="preserve">
							<g>
								<path d="M80.521,53.865L67.19,37.018V23.541c0,0,0.008-6.385,0-6.465l-3.746-7.59l3.324-6.32c0.354-0.67,0.33-1.475-0.061-2.121
									C66.314,0.397,65.613,0,64.857,0H7.442C6.251,0,5.284,0.967,5.284,2.16l0.051,80.307h10.369V16.842H9.603V4.32h51.68l-2.186,4.15
									c-0.328,0.625-0.332,1.369-0.006,1.998l3.295,6.373h-42.43v65.625h7.914h6.818h12.997c0.347,2.703,2.652,4.795,5.449,4.795h11.259
									c3.038,0,5.5-2.463,5.5-5.5V63.094h6.563c0.006,0,0.012,0,0.021,0c3.036,0,5.5-2.463,5.5-5.5
									C81.978,56.156,81.425,54.846,80.521,53.865z M64.044,57.393v24.168H52.785V57.393H40.722l17.693-22.362l17.691,22.361
									L64.044,57.393L64.044,57.393z"/>
							</g>
						</svg>
					</label>
					<input id="file-upload" type="file" on:change={handleFileSelect} accept=".epub" class="hidden" />

					<!-- Menú Secundario (Sin cambios, ya era correcto) -->
					<div class="relative">
						<button
							on:click={() => (isMenuOpen = !isMenuOpen)}
							aria-haspopup="true"
							aria-expanded={isMenuOpen}
							class="py-2 px-2.5 rounded-md text-text-muted bg-background border border-border hover:bg-surface hover:text-text-base transition-colors"
						>
							<span class="sr-only">{$_('openOptionsMenu')}</span>
							<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01" />
							</svg>
						</button>

						{#if isMenuOpen}
							<div
								class="absolute top-full right-0 mt-2 w-56 bg-surface border border-border rounded-lg shadow-xl z-10 p-2"
								role="menu"
								use:clickOutside
								on:click_outside={closeMenu}
							>
								<div class="px-2 py-1">
									<ThemeSwitcher />
								</div>
								<div class="px-2 py-1">
									<LanguageSwitcher />
								</div>
							</div>
						{/if}
					</div>
				</div>
			</header>
			<div class="mt-8">
				{#if $bookStore.length === 0}
					<!-- Estado Vacío Mejorado: Más visual y centrado -->
					<div class="text-center py-12">
						<label for="file-upload">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="mx-auto h-12 w-12 text-text-muted"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
								stroke-width="1.5"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="M12 9v6m3-3H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z"
								/>
							</svg>
						</label>
						<h3 class="mt-2 text-lg font-medium text-text-base">{$_('noBooksYet')}</h3>
						<p class="mt-1 text-base text-text-muted">{$_('importFirstBook')}</p>
					</div>
				{:else}
					<!-- La rejilla de libros responsiva -->
					<div
						class="grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3 sm:gap-x-6 lg:grid-cols-4 xl:grid-cols-6 xl:gap-x-8"
					>
						{#each $bookStore as book (book.id)}
							<a href={`/reader/${encodeURIComponent(book.id)}`} class="group block text-center">
								<div
									class="relative mx-auto h-64 w-44 overflow-hidden rounded-md bg-background shadow-md transition-all duration-300 group-hover:shadow-xl group-hover:-translate-y-1"
								>
									<img
										src={book.coverUrl}
										alt={`Cover of ${book.title}`}
										class="h-full w-full object-cover"
									/>
								</div>
								<h3 class="mt-4 block truncate text-sm font-semibold text-text-base group-hover:text-primary">
									{book.title}
								</h3>
							</a>
						{/each}
					</div>
				{/if}
			</div>
		</div>
	</section>

</div>
