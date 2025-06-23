<script lang="ts">
	// Importaciones necesarias de Svelte y otras librerías
	import { onMount, tick } from 'svelte';
	import { page } from '$app/stores'; // Store de SvelteKit para acceder a información de la página actual (ej. parámetros de URL)
	import { bookStore, type Book } from '$lib/store/book.store'; // Nuestro store de libros y la interfaz Book
	import ePub, { type Rendition, type Book as EpubBookInstance } from 'epubjs'; // Librería para manejar y renderizar EPUBs
	import { ArrowLeft, Settings, Play, Pause, Loader2 } from '@lucide/svelte';
	import { goto } from '$app/navigation'; // Para navegar programáticamente a otras rutas
	import { _ } from 'svelte-i18n'; // Store para las traducciones
	import { browser } from '$app/environment';

	import themeStore, { type Theme } from '$lib/store/theme.store';
	import LanguageSwitcher from '$lib/components/LanguageSwitcher.svelte';
	import ThemeSwitcher from '$lib/components/ThemeSwitcher.svelte';
	import { clickOutside } from '$lib/actions/clickOutside.action';
	import FontSizeSwitcher from '$lib/components/FontSizeSwitcher.svelte';
	import TtsConfigurator from '$lib/components/TTSConfigurator.svelte';

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
	let isReadingContinuously = false; // Nuevo estado para controlar la lectura continua
	let currentHighlightedCfi: string | null = null; // Nuevo estado para el CFI del texto resaltado
	let isAudioPlaying = false; // Para controlar el estado de reproducción
	let isAudioLoading = false; // Para mostrar un indicador de carga


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
			// Limpiar los datos de ubicaciones de epubjs del localStorage para evitar SyntaxError por datos corruptos.
			if (browser) {
				localStorage.removeItem('epubjs-locations');
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
					spread: 'auto', // Intentar mostrar dos páginas si el espacio lo permite (ej. en pantallas anchas)
					allowScriptedContent: true
				});

				// Restaurar última posición de lectura si está disponible
				let lastLocationCfi: string | null = null;
				if (browser && currentBook) {
					lastLocationCfi = localStorage.getItem(`${currentBook.id}-lastLocationCfi`);
				}
				
				// Mostrar el contenido del libro. Esto puede tomar un momento.
				await tempRendition.display(lastLocationCfi || undefined);
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

				// --- Lógica de Clic para Hablar (TTS) - El Método Correcto y Definitivo ---
				// Mis disculpas por los intentos anteriores. Este es el método correcto, usando el
				// evento 'click' que la propia librería epubjs proporciona. Es la forma más simple y robusta.
				tempRendition.on('click', async (event: any) => {
					// LOG DE DEPURACIÓN INMEDIATO: Para confirmar que el evento se dispara.
					console.log('EPUBJS CLICK EVENT RECEIVED:', event);

					// El evento de epubjs nos da el CFI directamente. No necesitamos calcularlo.
					let cfi = event.cfi;

					const clickedElement = event.target as HTMLElement;

					// Fallback: Si el evento no proporciona un CFI, intentamos generarlo desde el elemento clicado.
					// Esto aumenta la robustez si el clic ocurre en un elemento que epubjs no mapea directamente.
					if (!cfi && clickedElement && rendition) {
						try {
							const view = rendition.manager.current();
							if (view && view.contents) {
								cfi = (view.contents as any).cfiFromNode(clickedElement);
								console.log('CFI generado manualmente desde el nodo:', cfi);
							}
						} catch (e) {
							console.warn('No se pudo generar un CFI desde el elemento clicado:', e);
						}
					}

					// Si clickedElement es válido, procedemos a leer. CFI puede ser null, lo cual readTextSegment maneja.
					if (clickedElement) {
						isReadingContinuously = true; // Un clic inicia la lectura continua
						readTextSegment(clickedElement, cfi); // Pasar CFI (puede ser null)
					} else {
						console.warn('El elemento clicado no fue válido. No se puede procesar el clic.');
					}
				});

				// Manejar cambios de ubicación (evento correcto: 'relocated')
				tempRendition.on('relocated', (location: any) => {
					if (isReadingContinuously) {
						// Darle un momento a Svelte/DOM para actualizarse después del cambio de página
						tick().then(() => {
							startReadingFromCurrentView();
						});
					}

					if (epubInstance?.locations) {
						// Forzamos el tipo a 'any' para acceder a 'start.cfi' y confiamos en las verificaciones de nulidad.
						const startLocationObject = (location as any)?.start;
						if (!startLocationObject || typeof startLocationObject.cfi !== 'string') {
							return;
						}

						const cfi = startLocationObject.cfi;

						// Guardamos la última posición de lectura para este libro
						if (browser && currentBook) {
							localStorage.setItem(`${currentBook.id}-lastLocationCfi`, cfi);
						}

						currentPercentage = epubInstance.locations.percentageFromCfi(cfi);
						// Actualizar números de página si las ubicaciones están cargadas
						if (locationsTotal > 0 && epubInstance.locations) { // Asegurarse de que locations exista
							// Usar locationFromCfi que devuelve un índice (0-based) y es más robusto entre versiones de epubjs
							const pageIndex = (epubInstance.locations as any).locationFromCfi(cfi);
							currentPageInLocations = (pageIndex ?? -1) + 1; // Convertir a número de página (1-based), resulta en 0 si es null
						}
					} else {
						// Fallback si locations aún no está listo
						// Podríamos estimar el porcentaje basado en el CFI si es necesario,
						// pero por ahora, simplemente no actualizamos la página/total si locations no está listo.
					}
				});


				isLoadingLocations = true; 
				// Usar la promesa de .generate() es más limpio que el evento 'locationsGenerated'
				tempEpubInstance.locations.generate(1000).then(() => {
					if (!epubInstance?.locations || !rendition) return;

					locationsTotal = epubInstance.locations.length();
					console.log(`EPUB.js: Locations generated. Total locations: ${locationsTotal}`);

					// Después de que las ubicaciones estén listas, actualiza la página y el porcentaje
					// basándose en la vista actual.
					const currentLocation = rendition.currentLocation();
					const startOfCurrentLocation = (currentLocation as any)?.start;

					if (startOfCurrentLocation && typeof startOfCurrentLocation.cfi === 'string') {
						const cfi = startOfCurrentLocation.cfi;
						currentPercentage = epubInstance.locations.percentageFromCfi(cfi);
						const pageIndex = (epubInstance.locations as any).locationFromCfi(cfi);
						currentPageInLocations = (pageIndex ?? -1) + 1;
					}
				}).catch((err: unknown) => {
					console.error('Error generating locations', err);
				}).finally(() => {
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

	// Función auxiliar para eliminar el resaltado actual
	function removeHighlight() {
		if (rendition && currentHighlightedCfi) {
			rendition.annotations.remove(currentHighlightedCfi, 'highlight');
			currentHighlightedCfi = null;
		}
	}

	function togglePlayback() {
		if (!currentAudio) {
			// Si no hay audio, y el usuario presiona Play, iniciar lectura continua desde la vista actual
			if (!isAudioPlaying) {
				isReadingContinuously = true;
				startReadingFromCurrentView();
			}
			return;
		}

		if (isAudioPlaying) {
			currentAudio.pause();
			isReadingContinuously = false; // Pausar detiene la lectura continua
		} else {
			currentAudio.play();
			isReadingContinuously = true; // Reanudar la lectura continua
		}
	}

	// Función para encontrar y leer el primer elemento legible en la vista actual
	async function startReadingFromCurrentView() {
		if (!rendition || !epubInstance || !isReadingContinuously) {
			return;
		}

		const location = rendition.currentLocation();

		if (!location || !location.start?.cfi) {
			console.warn('No se encontró la ubicación actual para iniciar la lectura.');
			isReadingContinuously = false;
			return;
		}

		try {
			// Obtener el elemento al principio de la vista actual usando el CFI
			const range = await epubInstance.getRange(location.start.cfi);
			if (!range) {
				console.warn('No se pudo obtener el rango desde el CFI inicial. Avanzando página.');
				rendition.next();
				return;
			}

			const startNode = range.startContainer;
			const element = (startNode.nodeType === Node.TEXT_NODE ? startNode.parentElement : startNode) as HTMLElement;

			// Encontrar el elemento de bloque legible más cercano
			const readableElement = element.closest('p, li, h1, h2, h3, h4, h5, h6, div') as HTMLElement;

			if (readableElement && readableElement.textContent?.trim()) {
				const view = rendition.manager.current();
				const cfi = view ? (view.contents as any).cfiFromNode(readableElement) : null;
				readTextSegment(readableElement, cfi);
			} else {
				// Si el primer elemento visible no es legible, avanzar a la siguiente página
				console.log('Primer elemento visible no es legible, avanzando...');
				rendition.next();
			}
		} catch (e) {
			console.error('Error al iniciar la lectura desde la vista actual:', e);
			isReadingContinuously = false;
		}
	}

	// Nueva función para encontrar y leer el siguiente segmento de texto
	function findAndReadNextSegment(currentElement: HTMLElement) {
		if (!rendition || !isReadingContinuously) return;

		const view = rendition.manager.current();
		if (!view || !view.document) return;

		// Obtener todos los elementos legibles en el capítulo actual y filtrar los vacíos
		const allReadableElements = Array.from(
			view.document.querySelectorAll('p, li, h1, h2, h3, h4, h5, h6, div')
		).filter((el) => el.textContent?.trim());

		const currentIndex = allReadableElements.findIndex((el) => el.isSameNode(currentElement));

		if (currentIndex > -1 && currentIndex + 1 < allReadableElements.length) {
			const nextElement = allReadableElements[currentIndex + 1] as HTMLElement;
			const cfi = (view.contents as any).cfiFromNode(nextElement);
			readTextSegment(nextElement, cfi);
		} else {
			// Si no hay más elementos legibles, ir a la siguiente página
			console.log('Fin de los elementos legibles en la sección, avanzando página...');
			rendition.next();
		}
	}

	// Renombrada de speakText a readTextSegment para reflejar su rol en la lectura de un segmento
	async function readTextSegment(element: HTMLElement, cfi: string | null) { // CFI es ahora opcional
		const textToSpeak = element.textContent?.trim() || '';
		if (!textToSpeak.trim()) {
			console.warn("El elemento no tiene texto para leer:", element);
			if (isReadingContinuously) findAndReadNextSegment(element); // Si está vacío, buscar el siguiente
			return;
		}

		// Detener y limpiar completamente la instancia de audio anterior
		if (currentAudio) {
			currentAudio.pause();
			currentAudio.onplaying = null;
			currentAudio.onpause = null;
			currentAudio.onended = null;
			currentAudio.onerror = null;
			currentAudio.src = '';
			currentAudio = null;
		}
		removeHighlight(); // Asegurarse de que el resaltado anterior se elimine
		if (rendition && cfi) {
			// Solo resaltar si el CFI está disponible
			// Usar el tipo 'highlight' que es estándar en epubjs para el resaltado
			rendition.annotations.highlight(cfi, {}, (e: any) => {}, 'tts-highlight');
			currentHighlightedCfi = cfi; // Guardar el CFI para poder eliminar el resaltado después
		}

		isAudioPlaying = false;
		isAudioLoading = true;

		try {
			console.log("Text to Speech: ", textToSpeak);

			const url = new URL(`${BACKEND_URL}/text_to_audio`);
			url.searchParams.append('tts_provider', ttsEngine);
			url.searchParams.append('lang', ttsLang);
			if (ttsEngine === 'piper' && piperVoiceKey) {
				url.searchParams.append('piper_voice_key', piperVoiceKey);
			}
			
			const response = await fetch(url.toString(), {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Accept': 'audio/wav, audio/mpeg' // Indicar que esperamos audio
				},
				body: JSON.stringify({ text: textToSpeak })
			});
			
			if (!response.ok) {
				let errorDetail = response.statusText;
				try {
					const errorData = await response.json();
					errorDetail = errorData.detail || errorDetail;
				} catch (e) { /* No es un error JSON, usar statusText */ }
				throw new Error(`Backend error: ${errorDetail}`);
			}
			
			const audioBlob = await response.blob();
			const audioUrl = URL.createObjectURL(audioBlob);
			currentAudio = new Audio(audioUrl);

			// Sincronizar el estado de reproducción con los eventos del elemento de audio y manejar la continuidad
			currentAudio.onplaying = () => { isAudioPlaying = true; };
			currentAudio.onpause = () => {
				isAudioPlaying = false;
				// No limpiar el resaltado aquí para que el usuario sepa dónde se detuvo
			};
			currentAudio.onended = () => {
				isAudioPlaying = false;
				if (isReadingContinuously) {
					findAndReadNextSegment(element); // Buscar el siguiente segmento en lugar de solo cambiar de página
				} else {
					currentAudio = null; // Limpiar audio si no es continuo
					removeHighlight();
				}
			};
			currentAudio.onerror = (e) => {
				console.error("Error de reproducción de audio:", e);
				isAudioPlaying = false; isAudioLoading = false; currentAudio = null;
				isReadingContinuously = false; // Detener lectura continua en caso de error
				removeHighlight();
			};

			await currentAudio.play();
		} catch (error) {
			console.error("Error speaking text:", error);
			currentAudio = null; // Asegurar que se limpie en caso de error
			isReadingContinuously = false;
			removeHighlight();
		} finally {
			isAudioLoading = false; // Ocultar el indicador de carga
		}
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
				const pageIndex = (epubInstance.locations as any).locationFromCfi(cfi);
				const pageNum = (pageIndex ?? -1) + 1;
				const percentageDisplay = Math.round(percentage * 100);
				tooltipText = `${percentageDisplay}% (${pageNum > 0 ? pageNum : '...'} / ${locationsTotal})`;
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
				const pageIndex = (epubInstance.locations as any).locationFromCfi(cfi);
				const pageNum = (pageIndex ?? -1) + 1;
				const percentageDisplay = Math.round(newPercentage * 100);
				tooltipText = `${percentageDisplay}% (${pageNum > 0 ? pageNum : '...'} / ${locationsTotal})`;
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

				<!-- Controles de Audio -->
				<div class="absolute left-4 bottom-3">
					{#if isAudioLoading}
						<button class="p-2 rounded-full bg-surface-hover text-text-muted cursor-not-allowed" disabled>
							<Loader2 class="animate-spin" size={24} />
						</button>
					{:else}
						<button 
							on:click={togglePlayback} 
							class="p-2 rounded-full bg-surface-hover text-text-base hover:bg-primary hover:text-on-primary transition-colors"
							aria-label={isAudioPlaying ? $_('reader.tts.pause', { default: 'Pause audio' }) : $_('reader.tts.play', { default: 'Play audio' })}
						>
							{#if isAudioPlaying}
								<Pause size={24} />
							{:else}
								<Play size={24} />
							{/if}
						</button>
					{/if}
				</div>

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

	/* Estilos globales para el resaltado de TTS */
	:global(.tts-highlight) {
		background-color: yellow !important; /* O el color que prefieras */
		opacity: 0.5 !important;
	}
</style>
