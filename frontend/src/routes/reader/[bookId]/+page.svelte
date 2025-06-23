<script lang="ts">
	// Importaciones necesarias de Svelte y otras librerías
	import { onMount, tick } from 'svelte';
	import { page } from '$app/stores'; // Store de SvelteKit para acceder a información de la página actual (ej. parámetros de URL)
	import { bookStore, type Book } from '$lib/store/book.store'; // Nuestro store de libros y la interfaz Book
	import ePub, { type Rendition, type Book as EpubBookInstance } from 'epubjs'; // Librería para manejar y renderizar EPUBs
	import { ArrowLeft, Settings } from '@lucide/svelte'; // Iconos para la UI.
	import { goto } from '$app/navigation'; // Para navegar programáticamente a otras rutas
	import { _ } from 'svelte-i18n'; // Store para las traducciones
	import { browser } from '$app/environment';

	import themeStore, { type Theme } from '$lib/store/theme.store';
	import LanguageSwitcher from '$lib/components/LanguageSwitcher.svelte';
	import ThemeSwitcher from '$lib/components/ThemeSwitcher.svelte';
	import { clickOutside } from '$lib/actions/clickOutside.action';
	import FontSizeSwitcher from '$lib/components/FontSizeSwitcher.svelte';
	import TtsConfigurator from '$lib/components/TTSConfigurator.svelte';

	// --- HACK PARA EL PROBLEMA DE SANDBOX EN EPUB.JS 0.3.93 ---
	// La versión 0.3.93 de epub.js hardcodea `sandbox="allow-same-origin"` en la creación de su iframe interno.
	// Este hack intenta modificar el atributo sandbox del iframe *antes* de que se cargue el contenido.
	// Es un parche muy específico y frágil para esta versión de la librería.
	// Se coloca aquí para asegurar que se ejecute lo antes posible, antes de cualquier instanciación de ePub.
	if (typeof window !== 'undefined' && (ePub as any).Rendition && (ePub as any).Rendition.View && (ePub as any).Rendition.View.Iframe && !(ePub as any).Rendition.View.Iframe.__patched__) {
		console.log("EPUB.js Hack: Applying sandbox patch to IframeView.prototype.load (global scope)");
		const originalIframeViewLoad = (ePub as any).Rendition.View.Iframe.prototype.load;
		(ePub as any).Rendition.View.Iframe.prototype.load = function(contents: string) {
			if (this.iframe) {
				this.iframe.setAttribute("sandbox", "allow-same-origin allow-scripts allow-popups allow-forms allow-pointer-lock allow-top-navigation-by-user-activation");
				console.log("EPUB.js Hack: Iframe sandbox attribute set during load:", this.iframe.getAttribute("sandbox"));
			} else {
				console.warn("EPUB.js Hack: Iframe not found when patching load method. This might indicate a deeper issue.");
			}
			const result = originalIframeViewLoad.apply(this, [contents]);
			(ePub as any).Rendition.View.Iframe.__patched__ = true; // Marca como parcheado
			return result;
		};
	}
	// --- FIN DEL HACK ---

	// --- Variables de estado del componente ---
	let currentBook: Book | undefined; // Almacenará el objeto del libro que se está leyendo
	let epubInstance: EpubBookInstance | undefined; // Instancia del libro EPUB creada por epubjs
	let rendition: Rendition | undefined; // Objeto de epubjs que maneja el renderizado del libro en la página
	let viewerElement: HTMLDivElement; // Referencia al elemento DIV donde se mostrará el contenido del EPUB (vinculado con bind:this)
	let isLoading = true; // Booleano para controlar el estado de carga
	let errorMessage: string | undefined; // Para almacenar mensajes de error si algo falla
	let currentChapterTitle = ''; // Título del capítulo actual que se está mostrando


	// Variables para la barra de progreso y ubicaciones
	let currentPercentage = 0; // Porcentaje actual de lectura (0 a 1)
	let locationsTotal = 0; // Número total de "páginas" según las ubicaciones de epubjs
	let currentPageInLocations = 0; // Número de página actual (basado en 1)
	let isLoadingLocations = false; // Indicador para la generación de ubicaciones

	// --------------- TTS Settings----------------
	const BACKEND_URL = 'http://localhost:8000';
	let ttsEngine: string = 'piper';
	let ttsLang: string = 'es';
	let piperVoiceKey: string = 'es_MX-claude-high';
	let currentAudio: HTMLAudioElement | null = null;


	let isSettingsOpen = false;

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
		// Resetear estados de progreso también
		currentPercentage = 0;
		locationsTotal = 0;
		currentPageInLocations = 0;
		if (browser) {
			const storedTtsEngine = localStorage.getItem('tts-engine');
			const storedTtsLang = localStorage.getItem('tts-lang');
			const storedPiperVoiceKey = localStorage.getItem('piper-voice-key');

			if (storedTtsEngine) ttsEngine = storedTtsEngine;
			if (storedTtsLang) ttsLang = storedTtsLang;
			if (storedPiperVoiceKey) piperVoiceKey = storedPiperVoiceKey;
		}


		isLoadingLocations = false;

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
			// Using await tick() ensures we wait for the next microtask queue,
			// allowing Svelte to process pending updates.
			// Esperar un "tick" del ciclo de Svelte para que el DOM se actualice y viewerElement se vincule.
			// Esto es crucial porque el div#viewer se renderiza condicionalmente basado en isLoading.
			if (!viewerElement) {
				await tick(); // Esperar a que Svelte actualice el DOM
			}

			// After the tick, viewerElement should be bound if the conditions for its rendering were met.
			// Después del tick, verificar si viewerElement está realmente disponible.
			if (!viewerElement) {
				console.error('EPUB viewer element (#viewer) still not found in DOM after isLoading=false and tick.');
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
				epubInstance = tempEpubInstance;
				rendition = tempRendition;

				// Escuchar el evento 'displayed' de la rendition para actualizar el título del capítulo.
				// Este evento se dispara cada vez que una nueva sección/capítulo se muestra.
				tempRendition.on('displayed', (section: any) => {
					// Obtener información de navegación para la sección actual
					const navItem = tempEpubInstance?.navigation.get(section.href);
					// Actualizar el título del capítulo si está disponible
					currentChapterTitle = navItem?.label?.trim() || '';
				});
				
								// Add click listener for TTS
				tempRendition.on('click', async (event: any) => {
					if (epubInstance && rendition && event.location && event.location.start && event.location.start.cfi) {
						const cfi = event.location.start.cfi;
						try {
							// Get the DOM range corresponding to the CFI
							const range = await epubInstance.getRange(cfi);
							let textToSpeak = range.toString().trim();

							// Attempt to expand the text to the containing block element (e.g., paragraph)
							if (range.startContainer) {
								let parentElement: HTMLElement | null = null;
								if (range.startContainer.nodeType === Node.ELEMENT_NODE) {
									parentElement = range.startContainer as HTMLElement;
								} else if (range.startContainer.parentNode && range.startContainer.parentNode.nodeType === Node.ELEMENT_NODE) {
									parentElement = range.startContainer.parentNode as HTMLElement;
								}

								while (parentElement && parentElement.tagName !== 'BODY' && !['P', 'DIV', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'LI'].includes(parentElement.tagName)) {
									parentElement = parentElement.parentNode as HTMLElement;
								}
								if (parentElement && parentElement.tagName !== 'BODY') {
									textToSpeak = parentElement.innerText.trim();
								}
							}
							speakText(textToSpeak);
						} catch (e) {
							console.error("Error getting range or text from CFI:", e);
						}
					}
				});

				// Manejar cambios de ubicación (evento correcto: 'relocated')
				tempRendition.on('relocated', (location: any) => {
					if (epubInstance?.locations) {
						// Forzamos el tipo a 'any' para acceder a 'start.cfi' y confiamos en las verificaciones de nulidad.
						const startLocationObject = (location as any)?.start;
						if (!startLocationObject || typeof startLocationObject.cfi !== 'string') {
							return;
						}

						const cfi = startLocationObject.cfi;
						currentPercentage = epubInstance.locations.percentageFromCfi(cfi);
						// Actualizar números de página si las ubicaciones están cargadas
						if (locationsTotal > 0 && epubInstance.locations) { // Asegurarse de que locations exista
							const loc = epubInstance.locations.load(cfi);
							// epubjs locations.load() puede devolver un objeto con page o un string CFI.
							// Necesitamos manejar ambos casos o asegurarnos del tipo.
							// Por ahora, asumimos que si es un objeto, tiene 'page'.
							currentPageInLocations = typeof loc === 'object' && loc && 'page' in loc ? (loc as any).page as number : 0;
						}
					} else {
						// Fallback si locations aún no está listo
						// Podríamos estimar el porcentaje basado en el CFI si es necesario,
						// pero por ahora, simplemente no actualizamos la página/total si locations no está listo.
					}
				});


				isLoadingLocations = true; 
				tempEpubInstance.locations.generate(1000) 
				.then(() => { 
					locationsTotal = tempEpubInstance!.locations.length(); 
					isLoadingLocations = false; 
				}) 
				.catch((err: unknown) => { 
					console.error('Error generating locations', err); 
					isLoadingLocations = false; 
				});


				// Si todo fue exitoso, asignar las instancias temporales a las variables del componente.
				// epubInstance = tempEpubInstance;
				// rendition = tempRendition;

				// Registrar temas para el contenido del EPUB
				rendition.themes.register('dark-epub', {
					body: { color: 'rgb(229 231 235)', 'background-color': 'rgb(31 41 55)' }, // text-gray-200, bg-gray-800 (ejemplo)
					'a, a:link, a:visited': { color: 'rgb(129 140 248)', 'text-decoration': 'underline' }, // indigo-400 (ejemplo)
					'p, li, h1, h2, h3, h4, h5, h6, span, div': { color: 'rgb(229 231 235) !important' }
				});
				rendition.themes.register('light-epub', {
					body: { color: 'rgb(17 24 39)', 'background-color': 'rgb(255 255 255)' }, // text-gray-900, bg-white (ejemplo)
					'a, a:link, a:visited': { color: 'rgb(79 70 229)', 'text-decoration': 'underline' }, // indigo-600 (ejemplo)
					'p, li, h1, h2, h3, h4, h5, h6, span, div': { color: 'rgb(17 24 39) !important' }
				});

				applyEpubTheme($themeStore); // Aplicar tema inicial

				// Escuchar la finalización de la generación de ubicaciones
				if (epubInstance) { // El listener va en la instancia del libro
					epubInstance.on('locationsGenerated', (locationsGenerated: any) => { // Renombrado parámetro para evitar confusión con variable global
						try {
							console.log('EPUB.js: Event "locationsGenerated" fired. Locations data:', locationsGenerated);
							if (epubInstance?.locations) { // Doble verificación por si acaso
								locationsTotal = epubInstance.locations.length();
								isLoadingLocations = false;
								console.log(`EPUB.js: isLoadingLocations set to false. Total locations: ${locationsTotal}`);
								if (rendition) { // Asegurarse que rendition exista
									// Actualizar porcentaje y página inicial después de que las ubicaciones estén listas
									// Esto es importante si el libro ya estaba abierto en una posición específica
									const currentLocationObject = rendition.currentLocation();

									// El objeto Location de epubjs tiene una propiedad 'start' que contiene el CFI.
									// Forzamos 'any' para el acceso directo y confiamos en las verificaciones.
									const startOfCurrentLocation = (currentLocationObject as any)?.start;
									if (!startOfCurrentLocation || typeof startOfCurrentLocation.cfi !== 'string') {
										console.warn('EPUB.js: Could not get CFI from current location on locationsGenerated.');
										return;
									}

									const cfi = startOfCurrentLocation.cfi;
									currentPercentage = epubInstance.locations.percentageFromCfi(cfi);
									const loc = epubInstance.locations.load(cfi);
									currentPageInLocations = typeof loc === 'object' && loc && 'page' in loc ? loc.page as number : 0;
								}
							}
						} catch (err) {
							console.error('EPUB.js: Error inside "locationsGenerated" callback:', err);
							isLoadingLocations = false; // Asegurarse de que no se quede cargando indefinidamente
						} // Fin del if (epubInstance?.locations)
					});
				}

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
			isLoadingLocations = false; // Asegurar que se resetee
		};
	});

	// Las funciones nextPage y prevPage ya no son necesarias

	function applyEpubTheme(theme: Theme | null) {
		if (rendition && theme) {
			// Asumimos que 'princess' y 'ocean' son temas oscuros o tienen un equivalente oscuro.
			if (theme === 'dark' || theme === 'princess' || theme === 'ocean') {
				rendition.themes.select('dark-epub');
			} else { // 'light' o cualquier otro tema no oscuro
				rendition.themes.select('light-epub');
			}
		}
	}

	// Reaccionar a los cambios del tema global
	$: if (browser && rendition && $themeStore) {
		applyEpubTheme($themeStore);
	}

	// Reaccionar a lo cambios en el TTS Config
	$: if (browser && ttsEngine) localStorage.setItem('tts-engine', ttsEngine);
	$: if (browser && ttsLang) localStorage.setItem('tts-lang', ttsLang);
	$: if (browser && piperVoiceKey) localStorage.setItem('piper-voice-key', piperVoiceKey);

	async function speakText(textToSpeak: string) {
		if (!textToSpeak.trim()) {
			console.warn("No text to speak.");
			return;
		}

		if (currentAudio) {
			currentAudio.pause();
			currentAudio.currentTime = 0;
		}

		try {
			const response = await fetch(`${BACKEND_URL}/text-to-audio`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ text: textToSpeak, lang: ttsLang, tts_engine: ttsEngine, piper_voice: piperVoiceKey })
			});

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(`Backend error: ${errorData.detail || response.statusText}`);
			}
			const data = await response.json();
			const audioUrl = data.audio_file_urls[0]; // Assuming one combined audio file
			if (audioUrl) { currentAudio = new Audio(audioUrl); currentAudio.play(); } else { console.warn("No audio URL received from backend."); }
		} catch (error) { console.error("Error speaking text:", error); }
	}


	function toggleSettings() {
		isSettingsOpen = !isSettingsOpen;
	}
	function closeSettings() {
		isSettingsOpen = false;
	}

	// --- Lógica de la Barra de Progreso ---
	let progressBarElement: HTMLDivElement | undefined;
	let isDraggingProgressBar = false;
	let tooltipText = ''; // Texto para el tooltip

	function handleProgressBarInteraction(event: MouseEvent) {
		if (!rendition || !epubInstance?.locations || !progressBarElement) return;

		const rect = progressBarElement.getBoundingClientRect();
		const clickX = event.clientX - rect.left;
		let percentage = clickX / rect.width;

		// Asegurar que el porcentaje esté entre [0, 1]
		percentage = Math.max(0, Math.min(1, percentage));

		const cfi = epubInstance.locations.cfiFromPercentage(percentage);
		if (cfi) {
			if (event.type === 'mousedown' || (event.type === 'mousemove' && isDraggingProgressBar)) { // Solo navega si es click o drag activo
				rendition.display(cfi);
			}
			// Actualizar texto del tooltip
			if (epubInstance.locations) {
				const loc = epubInstance.locations.load(cfi);
				// Verificar si loc es un objeto y tiene la propiedad 'page' antes de acceder a ella
				const pageNum = typeof loc === 'object' && loc && 'page' in loc ? (loc as any).page as number : 0;
				const percentageDisplay = Math.round(percentage * 100);
				tooltipText = `${percentageDisplay}% (${pageNum} / ${locationsTotal})`;
			} else if (percentage !== currentPercentage) { // Mostrar solo porcentaje si locations no está listo y el porcentaje cambia
				const percentageDisplay = Math.round(percentage * 100);
				tooltipText = `${percentageDisplay}%`; // No mostrar pageNum/locationsTotal if locations not ready
			} else {
				tooltipText = `${Math.round(percentage * 100)}%`; // Fallback si locations no está listo
			}
		}
	}

	function handleProgressBarMouseDown(event: MouseEvent) {
		event.preventDefault();   
		isDraggingProgressBar = true;
		handleProgressBarInteraction(event); // Mover inmediatamente al hacer clic
		document.addEventListener('mousemove', handleProgressBarMouseMove);
		document.addEventListener('mouseup', handleProgressBarMouseUp);
	}

	function handleProgressBarMouseMove(event: MouseEvent) {
		if (isDraggingProgressBar) {
			handleProgressBarInteraction(event); // Actualizar posición mientras se arrastra
		}
	}

	function handleProgressBarMouseUp() {
		isDraggingProgressBar = false;
		document.removeEventListener('mousemove', handleProgressBarMouseMove);
		document.removeEventListener('mouseup', handleProgressBarMouseUp);
		// No limpiar tooltipText aquí para que permanezca visible hasta mouseleave
	}

	function handleProgressBarKeyboard(event: KeyboardEvent) {
		if (!rendition || !epubInstance?.locations || !progressBarElement) return;

		let newPercentage = currentPercentage;
		const step = 0.01; // Mover 1% con cada tecla de flecha

		switch (event.key) {
			case 'ArrowLeft':
			case 'ArrowDown': // Algunas implementaciones usan ArrowDown para disminuir
				newPercentage = Math.max(0, currentPercentage - step);
				event.preventDefault(); // Prevenir scroll de página
				break;
			case 'ArrowRight':
			case 'ArrowUp': // Algunas implementaciones usan ArrowUp para aumentar
				newPercentage = Math.min(1, currentPercentage + step);
				event.preventDefault(); // Prevenir scroll de página
				break;
			case 'Home':
				newPercentage = 0;
				event.preventDefault();
				break;
			case 'End':
				newPercentage = 1;
				event.preventDefault();
				break;
			default:
				return; // No hacer nada para otras teclas
		}

		const cfi = epubInstance.locations.cfiFromPercentage(newPercentage);
		if (cfi) {
			rendition.display(cfi);
			// Actualizar tooltip si es necesario (opcional para teclado)
			if (epubInstance.locations) {
				const loc = epubInstance.locations.load(cfi);
				const pageNum = typeof loc === 'object' && loc && 'page' in loc ? (loc as any).page as number : 0;
				const percentageDisplay = Math.round(newPercentage * 100);
				tooltipText = `${percentageDisplay}% (${pageNum} / ${locationsTotal})`;
			}
		}
	}

	// Navegación global con flechas izquierda/derecha (para pasar página)
	function handleGlobalKeyDown(event: KeyboardEvent) {
		// Solo navegar si la rendition está lista y el foco no está en un elemento interactivo
		const target = event.target as HTMLElement;
		if (rendition && !isDraggingProgressBar && target.tagName !== 'INPUT' && target.tagName !== 'SELECT' && target.tagName !== 'TEXTAREA' && target.getAttribute('role') !== 'slider') {
			if (event.key === 'ArrowLeft') {
				rendition.prev();
				event.preventDefault(); // Prevenir scroll de página
			} else if (event.key === 'ArrowRight') {
				rendition.next();
				event.preventDefault(); // Prevenir scroll de página
			}
		}
	}

	function updateTooltipOnFocus() {
		if (rendition && epubInstance?.locations && locationsTotal > 0 && progressBarElement) {
			const percentageDisplay = Math.round(currentPercentage * 100);
			tooltipText = `${percentageDisplay}% (${currentPageInLocations} / ${locationsTotal})`;
		} else if (currentPercentage >= 0 && progressBarElement) { // Mostrar solo % si no hay locations o están cargando
			tooltipText = `${Math.round(currentPercentage * 100)}%`;
		} else {
			tooltipText = ''; // O un valor por defecto si se prefiere
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
	{#if !isLoading && !errorMessage } <!-- Header unificado: se muestra si no hay carga ni error -->
		<header class="flex items-center justify-between p-3 border-b border-border shadow-sm bg-surface flex-shrink-0">
			<button
				on:click={() => goto('/')}
				class="p-2 rounded-md hover:bg-surface-hover text-text-muted hover:text-text-base"
				aria-label={$_('reader.backToLibrary', { default: 'Back to library' })}
			>
				<ArrowLeft size={24} />
			</button>
			<div class="text-center overflow-hidden mx-2 flex-grow">
				{#if currentBook}
					<h1 class="text-lg font-semibold truncate" title={currentBook.title}>{currentBook.title}</h1>
					{#if currentChapterTitle}
						<p class="text-xs text-text-muted truncate" title={currentChapterTitle}>{currentChapterTitle}</p>
					{/if}
				{:else}
					<h1 class="text-lg font-semibold truncate">{$_('reader.pageTitle', { default: 'Reader' })}</h1>
				{/if}
			</div>
			<div class="w-10 flex-shrink-0">
				<!-- Botón de settings -->
				{#if rendition} <!-- Botón de settings solo si el libro está cargado y renderizado -->
				<div class="relative">
					<button
						on:click={toggleSettings}
						class="p-2 rounded-md hover:bg-surface-hover text-text-muted hover:text-text-base"
						aria-label="Open settings"
						aria-haspopup="true"
						aria-expanded={isSettingsOpen}
					>
						<Settings size={24} />
					</button>
					{#if isSettingsOpen}
					<div
						class="absolute top-full right-0 mt-2 w-56 bg-surface border border-border rounded-lg shadow-xl z-20 p-2"
						role="menu"
						use:clickOutside
						on:click_outside={closeSettings}
					>
						<div class="px-2 py-1"><ThemeSwitcher /></div>
						<div class="px-2 py-1"><LanguageSwitcher /></div>
						<div class="px-2 py-1"><FontSizeSwitcher currentRendition={rendition} /></div>
						<div class="px-2 py-1"><TtsConfigurator bind:ttsEngine={ttsEngine} bind:ttsLang={ttsLang} bind:piperVoiceKey={piperVoiceKey} /></div>
					</div>
					{/if}
				</div>
				{/if}
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
		{:else} <!-- Si no está cargando y no hay error, mostrar el visor -->
			<div bind:this={viewerElement} id="viewer" class="w-full h-full epub-viewer-container pb-16"></div>
			
			<!-- Pie de página con Barra de Progreso -->
			{#if rendition} <!-- La barra de progreso solo se muestra si la rendition está lista -->
				<div class="fixed bottom-0 left-0 right-0 p-3 bg-surface/90 backdrop-blur-sm border-t border-border shadow-up flex flex-col items-center justify-center">
					{#if isLoadingLocations}
					<p class="text-center text-sm text-text-muted">{$_('reader.loadingProgress', { default: 'Loading progress...' })}</p>
				{:else if rendition && epubInstance?.locations && locationsTotal > 0}
					<div class="w-full max-w-xl mx-auto relative">
						<div
							class="relative h-2.5 bg-border rounded-full cursor-pointer group"
							on:click|stopPropagation={handleProgressBarInteraction}
							on:mousedown|stopPropagation={handleProgressBarMouseDown}
							on:mouseleave={() => { if (!isDraggingProgressBar) tooltipText = ''; }}
							on:focus={updateTooltipOnFocus}
							on:keydown={handleProgressBarKeyboard}
							bind:this={progressBarElement}
							role="slider"
							aria-valuemin="0"
							aria-valuemax="100"
							aria-valuenow={Math.round(currentPercentage * 100)}
							aria-label={$_('reader.readingProgress', { default: 'Reading progress' })}
							tabindex="0"
						>
							<!-- svelte-ignore element_invalid_self_closing_tag -->
							<div class="absolute top-0 left-0 h-full bg-primary rounded-full" 
								style:width="{currentPercentage * 100}%" 
							/>
							<!-- Indicador Visual (Thumb) -->
							<!-- svelte-ignore element_invalid_self_closing_tag -->
							<div class="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-primary rounded-full shadow-lg pointer-events-none transition-opacity opacity-0 group-hover:opacity-100"
								style:left="calc({currentPercentage * 100}% - 8px)"
							/>
						</div>
						<!-- Tooltip -->
						{#if tooltipText && progressBarElement} <!-- Mostrar solo si hay texto y el elemento existe -->
						<div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-surface border border-border rounded-md text-xs text-text-base whitespace-nowrap shadow-lg z-20">
							{tooltipText}
						</div>
						{/if}
						<p class="text-center text-sm text-text-muted mt-1.5">
							{Math.round(currentPercentage * 100)}%
							{#if currentPageInLocations > 0 && locationsTotal > 0}
								({currentPageInLocations} / {locationsTotal})
							{/if}
						</p>
					</div>
				{:else}
					<p class="text-center text-sm text-text-muted">{$_('reader.progressNotAvailable', { default: 'Progress not available' })}</p>
				{/if}
			</div>
			{:else} <!-- Fallback si rendition no está lista pero no hay error ni carga (después de que el visor se haya intentado renderizar) -->
				<div class="absolute inset-0 flex flex-col items-center justify-center p-4 text-center">
					<p>{$_('reader.error.unexpected', { default: 'Could not display the book.' })}</p>
					<button on:click={() => goto('/')} class="mt-4 filled-button">{$_('reader.backToLibrary', { default: 'Back to Library' })}</button>
				</div>
			{/if}
		{/if}
	</main>
</div>

<svelte:window on:keydown={handleGlobalKeyDown} />

<style>
	/* Estilo para el contenedor relativo del tooltip si es necesario */
	.relative {
		position: relative;
		/* Asegurarse de que el z-index sea suficiente si hay otros elementos fijos */
	}
	/* Estilos para el foco en la barra de progreso para accesibilidad */
	[role="slider"]:focus-visible {
		outline: 2px solid rgb(var(--color-primary));
		outline-offset: 2px;
	}
	/* Eliminar el outline por defecto en elementos con tabindex si se prefiere un estilo de foco personalizado */
	[tabindex="0"]:focus {
		outline: none;
	}

	/* Asegurar que el thumb sea visible cuando la barra de progreso tiene foco */
	[role="slider"]:focus-visible .absolute.top-1\/2.-translate-y-1\/2,
	[role="slider"]:hover .absolute.top-1\/2.-translate-y-1\/2 {
		opacity: 1;
	}
	.epub-viewer-container :global(.epub-view) {
		user-select: text !important;
		-webkit-user-select: text !important;
		-moz-user-select: text !important;
		-ms-user-select: text !important;
	}
	#viewer {
		/* padding-bottom es la clave para el pie de página */
	}
	.shadow-up {
		box-shadow: 0 -4px 6px -1px rgb(0 0 0 / 0.1), 0 -2px 4px -2px rgb(0 0 0 / 0.1);
	}
</style>
