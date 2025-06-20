<script lang="ts">
	// Importaciones necesarias de Svelte y otras librerías
	import { onMount, tick } from 'svelte'; // Para ejecutar código cuando el componente se monta en el DOM
	import { page } from '$app/stores'; // Store de SvelteKit para acceder a información de la página actual (ej. parámetros de URL)
	import { bookStore, type Book } from '$lib/store/book.store'; // Nuestro store de libros y la interfaz Book
	import ePub, { type Rendition, type Book as EpubBookInstance } from 'epubjs'; // Librería para manejar y renderizar EPUBs
	import { ArrowLeft, ChevronLeft, ChevronRight } from '@lucide/svelte'; // Iconos para la UI
	import { goto } from '$app/navigation'; // Para navegar programáticamente a otras rutas
	import { _ } from 'svelte-i18n'; // Store para las traducciones

	// --- Variables de estado del componente ---
	let currentBook: Book | undefined; // Almacenará el objeto del libro que se está leyendo
	let epubInstance: EpubBookInstance | undefined; // Instancia del libro EPUB creada por epubjs
	let rendition: Rendition | undefined; // Objeto de epubjs que maneja el renderizado del libro en la página
	let viewerElement: HTMLDivElement; // Referencia al elemento DIV donde se mostrará el contenido del EPUB (vinculado con bind:this)
	let isLoading = true; // Booleano para controlar el estado de carga
	let errorMessage: string | undefined; // Para almacenar mensajes de error si algo falla
	let currentChapterTitle = ''; // Título del capítulo actual que se está mostrando

	onMount(() => {
		// Ensure epubInstance and rendition are reset if the component re-initializes
		// This is important if onMount could be called multiple times for the same component instance,
		// though less common for a page component unless specific navigation patterns are used.
		const cleanupPreviousInstance = () => {
			if (epubInstance) {
				// Si hay una instancia de epubjs activa, la destruimos para liberar recursos
				epubInstance.destroy();
				epubInstance = undefined;
			}
			rendition = undefined;
		};

		const initEpubViewer = async () => {
			cleanupPreviousInstance(); // Primero, limpiar cualquier instancia previa del visor EPUB

			// Reiniciar los estados del componente al inicio de la carga
			isLoading = true; errorMessage = undefined; currentBook = undefined; currentChapterTitle = '';

			const bookId = $page.params.bookId;
			if (!bookId) { // Verificar si el bookId (de la URL) está presente
				errorMessage = $_('reader.error.noBookId', { default: 'Book ID not provided.' });
				isLoading = false;
				return;
			}

			const books = $bookStore;
			const foundBook = books.find((b) => b.id === bookId);
			if (!foundBook) {
				// Si no se encuentra el libro en el store, mostrar error
				errorMessage = $_('reader.error.bookNotFound', { default: 'Book not found in your library.' });
				isLoading = false;
				return;
			}
			currentBook = foundBook;

			if (!currentBook.data) {
				// Verificar si el libro tiene los datos (ArrayBuffer) necesarios para renderizar
				console.error("Book data (ArrayBuffer) is missing for book:", currentBook.id);
				errorMessage = $_('reader.error.epubLoadFailed', { default: 'Book data is missing or corrupted.' });
				isLoading = false;
				return;
			}

			// Now we have a book and its data.
			// Establecer isLoading a false para que Svelte pueda renderizar el div#viewer.
			isLoading = false;

			// Wait for Svelte to update the DOM and bind viewerElement.
			// Using await new Promise ensures we wait for the next microtask queue,
			// allowing Svelte to process pending updates.
			// Esperar un "tick" del ciclo de Svelte para que el DOM se actualice y viewerElement se vincule.
			// Esto es crucial porque el div#viewer se renderiza condicionalmente basado en isLoading.
			if (!viewerElement) {
				await tick();
			}

			// After the tick, viewerElement should be bound if the conditions for its rendering were met.
			// Después del tick, verificar si viewerElement está realmente disponible.
			if (!viewerElement) {
				console.error("EPUB viewer element (#viewer) still not found in DOM after isLoading=false and tick.");
				errorMessage = $_('reader.error.epubLoadFailed', { default: 'Viewer element failed to render.' });
				// isLoading ya es false, así que no es necesario cambiarlo aquí.
				return;
			}

			// Variable temporal para la instancia de epubjs, para poder destruirla en el catch si falla la inicialización.
			let tempEpubInstance: EpubBookInstance | undefined;
			try {
				// Crear una nueva instancia de ePub con los datos (ArrayBuffer) del libro actual.
				tempEpubInstance = ePub(currentBook.data);
				
				// Renderizar el libro en el elemento viewerElement.
				const tempRendition = tempEpubInstance.renderTo(viewerElement, {
					width: '100%', // Ocupar todo el ancho disponible
					height: '100%', // Ocupar toda la altura disponible
					flow: 'paginated', // Flujo paginado, como un libro físico
					spread: 'auto' // Intentar mostrar dos páginas si el espacio lo permite (ej. en pantallas anchas)
				});

				// Mostrar el contenido del libro. Esto puede tomar un momento.
				await tempRendition.display();

				// Escuchar el evento 'displayed' de la rendition para actualizar el título del capítulo.
				// Este evento se dispara cada vez que una nueva sección/capítulo se muestra.
				tempRendition.on('displayed', (section: any) => {
					// Obtener información de navegación para la sección actual
					const navItem = tempEpubInstance?.navigation.get(section.href);
					// Actualizar el título del capítulo si está disponible
					currentChapterTitle = navItem?.label?.trim() || '';
				});
				
				// Si todo fue exitoso, asignar las instancias temporales a las variables del componente.
				epubInstance = tempEpubInstance;
				rendition = tempRendition;
				// isLoading ya se estableció a false antes para permitir el renderizado del viewerElement.

			} catch (error) {
				// Manejar errores durante la carga o renderizado del EPUB.
				console.error('Error loading EPUB in reader:', error);
				errorMessage = $_('reader.error.epubLoadFailed', { default: 'Failed to load the EPUB file.' }); // isLoading is already false
				if (tempEpubInstance) {
					// Si la instancia de epubjs se creó pero falló después, destruirla.
					tempEpubInstance.destroy();
				}
				// Asegurarse de que las variables del componente queden limpias.
				epubInstance = undefined;
				rendition = undefined;
			}
		};

		initEpubViewer(); // Llamar a la función asíncrona para inicializar el visor.

		return () => {
			cleanupPreviousInstance(); // Use the centralized cleanup
			// Reset states for a clean slate if the component is somehow re-used or for clarity
			isLoading = true;
			errorMessage = undefined;
			currentBook = undefined;
			currentChapterTitle = '';
		};
	});

	// Función para navegar a la página siguiente del libro.
	function nextPage() {
		if (rendition) {
			// Solo intentar avanzar si la rendition (el objeto de renderizado) existe.
			rendition.next();
		}
	}

	// Función para navegar a la página anterior del libro.
	function prevPage() {
		if (rendition) {
			// Solo intentar retroceder si la rendition existe.
			rendition.prev();
		}
	}
</script>

<svelte:head>
	<title>
		{currentBook ? currentBook.title : $_('reader.pageTitle', { default: 'Reader' })} - {$_('pageTitle', { default: 'Read Me a Book' })}
	</title>
	<meta
		name="description"
		content={$_('reader.metaDescription', {
			values: { bookTitle: currentBook?.title || 'book' },
			default: `Reading ${currentBook?.title || 'book'}`
		})}
	/>
</svelte:head>

<div class="flex flex-col h-screen bg-background text-text-base">
	{#if currentBook && !isLoading && !errorMessage }
		<header class="flex items-center justify-between p-3 border-b border-border shadow-sm bg-surface flex-shrink-0">
			<button
				on:click={() => goto('/')}
				class="p-2 rounded-md hover:bg-surface-hover text-text-muted hover:text-text-base"
				aria-label={$_('reader.backToLibrary', { default: 'Back to library' })}
			>
				<ArrowLeft size={24} />
			</button>
			<div class="text-center overflow-hidden mx-2">
				<h1 class="text-lg font-semibold truncate" title={currentBook.title}>{currentBook.title}</h1>
				{#if currentChapterTitle}
					<p class="text-xs text-text-muted truncate" title={currentChapterTitle}>{currentChapterTitle}</p>
				{/if}
			</div>
			<div class="w-10 flex-shrink-0" />
		</header>
	{:else if !isLoading && !errorMessage}
		<header class="flex items-center justify-start p-3 border-b border-border shadow-sm bg-surface flex-shrink-0">
			<button
				on:click={() => goto('/')}
				class="p-2 rounded-md hover:bg-surface-hover text-text-muted hover:text-text-base"
				aria-label={$_('reader.backToLibrary', { default: 'Back to library' })}
			>
				<ArrowLeft size={24} />
			</button>
			<div class="text-center overflow-hidden mx-2">
				<h1 class="text-lg font-semibold truncate">{$_('reader.pageTitle', { default: 'Reader' })}</h1>
			</div>
		</header>
	{/if}

	<main class="flex-grow relative overflow-hidden">
		{#if isLoading}
			<div class="absolute inset-0 flex items-center justify-center"><p>{$_('reader.loadingBook', { default: 'Loading book...' })}</p></div>
		{:else if errorMessage}
			<div class="absolute inset-0 flex flex-col items-center justify-center p-4 text-center">
				<p class="text-lg text-red-500">{errorMessage}</p>
				<button on:click={() => goto('/')} class="mt-4 filled-button">{$_('reader.backToLibrary', { default: 'Back to Library' })}</button>
			</div>
		{:else}
			<div bind:this={viewerElement} id="viewer" class="w-full h-full epub-viewer-container" />
			
			{#if rendition}
			<div class="fixed bottom-0 left-0 right-0 flex justify-between p-2 bg-surface/80 backdrop-blur-sm border-t border-border shadow-up">
				<button on:click={prevPage} class="p-2 rounded-md hover:bg-surface-hover text-text-muted hover:text-text-base" aria-label={$_('reader.previousPage', { default: 'Previous Page' })}><ChevronLeft size={28} /></button>
				<button on:click={nextPage} class="p-2 rounded-md hover:bg-surface-hover text-text-muted hover:text-text-base" aria-label={$_('reader.nextPage', { default: 'Next Page' })}><ChevronRight size={28} /></button>
			</div>
			{:else if !isLoading && !errorMessage} 
				<div class="absolute inset-0 flex flex-col items-center justify-center p-4 text-center">
					<p>{$_('reader.error.unexpected', { default: 'Could not display the book.' })}</p>
					<button on:click={() => goto('/')} class="mt-4 filled-button">{$_('reader.backToLibrary', { default: 'Back to Library' })}</button>
				</div>
			{/if}
		{/if}
	</main>
</div>

<style>
	.epub-viewer-container :global(.epub-view) {
		user-select: text !important;
		-webkit-user-select: text !important;
		-moz-user-select: text !important;
		-ms-user-select: text !important;
	}
	#viewer {
		height: 100%; 
	}
	.shadow-up {
		box-shadow: 0 -4px 6px -1px rgb(0 0 0 / 0.1), 0 -2px 4px -2px rgb(0 0 0 / 0.1);
	}
</style>
