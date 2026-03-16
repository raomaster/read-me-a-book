<script lang="ts">
	// Importaciones necesarias de Svelte y otras librerías
	import { PUBLIC_TTS_MODE } from '$env/static/public';
	import { page } from '$app/stores';
	import { onMount, onDestroy, tick } from 'svelte';
	// Store de SvelteKit para acceder a información de la página actual (ej. parámetros de URL)
	import { bookStore, type Book } from '$lib/store/book.store'; // Nuestro store de libros y la interfaz Book
	import ePub, { type Book as EpubBookInstance, type Rendition } from 'epubjs';
	// Librería para manejar y renderizar EPUBs
	import { ArrowLeft, ArrowRight, Pause, Play, Settings } from '@lucide/svelte';
	// Iconos para la UI.
	import { goto } from '$app/navigation'; // Para navegar programáticamente a otras rutas
	import { _ } from 'svelte-i18n'; // Store para las traducciones
	import { browser } from '$app/environment';

	import { clickOutside } from '$lib/actions/clickOutside.action';
	import FontSizeSwitcher from '$lib/components/FontSizeSwitcher.svelte';
	import LanguageSwitcher from '$lib/components/LanguageSwitcher.svelte';
	import ThemeSwitcher from '$lib/components/ThemeSwitcher.svelte';
	import TtsConfigurator from '$lib/components/TTSConfigurator.svelte';
	import themeStore, { type Theme } from '$lib/store/theme.store';

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
	const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'https://leeme.mooo.com/api';
	let ttsEngine: string = 'piper';
	let ttsLang: string = 'es';
	let piperVoiceKey: string = 'es_MX-claude-high';
	// Añadimos control de velocidad (generación para XTTS y reproducción para cualquier motor)
	let ttsSpeed: number = 1.0; // Se usará al generar con XTTS (0.5 a 2.0 recomendado)
	let playbackRate: number = 1.0; // Se usará para reproducir el audio (0.75 a 2.0 recomendado)
	let currentAudio: HTMLAudioElement | null = null;
	let audioEl: HTMLAudioElement;
	// NUEVO: modo de entorno ('local' | 'gcloud')
	let ttsMode: 'local' | 'gcloud' =
		PUBLIC_TTS_MODE?.toLowerCase() === 'gcloud' ? 'gcloud' : 'local';
	// NUEVO: voz para Kokoro (solo español)
	let kokoroVoice: string = 'ef_dora';
	// NUEVO: nombre de voz para Cloud TTS (API)
	let cloudVoiceName: string = '';
	let isAudioPlaying = false; // Estado de reproducción
	let lastNavigationTime = 0; // Para evitar navegaciones múltiples consecutivas
	let isUserInteracting = false; // Para detectar interacciones manuales del usuario
	let hasNavigatedThisPage = false; // Para evitar múltiples navegaciones en la misma página
	let isTurningPagePromise: Promise<void> | null = null;
	let resolveTurnPage: (() => void) | null = null;
	interface QueueItem {
		text: string;
		elements: HTMLElement[];
		audioUrlPromise?: Promise<string>; // blob URL pre-fetched
		cfi?: string; // Add CFI to reconnect elements if detached
	}
	let readingQueue: QueueItem[] = []; // Cola con buffer adelantado
	let currentReadingElements: HTMLElement[] = []; // todos los elementos resaltados actualmente
	let currentReadingElement: HTMLElement | null = null; // legacy var to satisfy old refs

	// ---------- Helpers de cola y navegación ----------
	const MAX_CHUNK = 800;
	function splitIntoChunks(txt: string): string[] {
		if (txt.length <= MAX_CHUNK) return [txt];
		const parts: string[] = [];
		let remaining = txt.trim();
		while (remaining.length) {
			let sliceEnd = remaining.lastIndexOf(' ', MAX_CHUNK);
			if (sliceEnd < MAX_CHUNK * 0.6) sliceEnd = MAX_CHUNK;
			parts.push(remaining.slice(0, sliceEnd).trim());
			remaining = remaining.slice(sliceEnd).trim();
		}
		return parts;
	}

	function getEpubIframe(): HTMLIFrameElement | null {
		return viewerElement?.querySelector('iframe') ?? null;
	}

	/**
	 * Construye la cola de lectura con los elementos visibles en el viewport actual.
	 * Soporta modo spread (2 iframes side-by-side) y modo single-page (1 iframe).
	 * Si se proporciona startFrom, la cola empieza desde ese elemento.
	 */
	function buildPageQueue(startFrom: HTMLElement | null = null): QueueItem[] {
		if (!rendition || !epubInstance || !viewerElement) return [];

		// En modo spread Epub.js puede usar múltiples iframes (uno por página visible).
		const iframes = Array.from(viewerElement.querySelectorAll('iframe')) as HTMLIFrameElement[];
		if (iframes.length === 0) return [];

		const buffer = 8;
		const viewerRect = viewerElement.getBoundingClientRect();
		const viewerWidth = viewerElement.clientWidth;
		const currentLoc = rendition.currentLocation() as any;

		const result: QueueItem[] = [];
		// startLocated: si startFrom ya fue encontrado en algún iframe previo
		let startLocated = startFrom === null;

		for (const iframe of iframes) {
			const doc = iframe.contentDocument;
			if (!doc?.body) continue;

			// Posición horizontal del iframe dentro del viewer (puede ser 0 para el izquierdo, ~vw/2 para el derecho)
			const iframeOffsetLeft = iframe.getBoundingClientRect().left - viewerRect.left;
			const iframeWidth = iframe.clientWidth;

			// Ignorar iframes completamente fuera del área visible
			if (iframeOffsetLeft + iframeWidth <= -buffer || iframeOffsetLeft >= viewerWidth + buffer) continue;

			// Obtener la sección del spine para este iframe (para generar CFIs correctos)
			let section: any;
			try {
				const view = (rendition as any).manager?.views?._views?.find(
					(v: any) => v.element === iframe || v.iframe === iframe
				);
				section = view?.section
					?? (Number.isInteger(currentLoc?.start?.index)
						? epubInstance!.spine.get(currentLoc.start.index)
						: undefined);
			} catch {}

			// ¿El startFrom pertenece a este iframe?
			const startInThisIframe = startFrom != null && startFrom.ownerDocument === doc;

			// Si aún no encontramos startFrom y no está en este iframe, saltar este iframe
			if (!startLocated && !startInThisIframe) continue;

			const allBlocks = Array.from(
				doc.body.querySelectorAll('p, li, h1, h2, h3, h4, h5, h6')
			) as HTMLElement[];

			// Filtrar: solo elementos cuya posición ABSOLUTA (iframe offset + rect.left) esté dentro del viewer
			const pageElements = allBlocks.filter((el) => {
				const rect = el.getBoundingClientRect();
				if (rect.width === 0 && rect.height === 0) return false;
				const absLeft = rect.left + iframeOffsetLeft;
				return absLeft >= -buffer && absLeft < viewerWidth - buffer;
			});

			let startIdx = 0;
			if (!startLocated && startInThisIframe) {
				const foundIdx = pageElements.indexOf(startFrom!);
				startIdx = foundIdx >= 0 ? foundIdx : 0;
				startLocated = true;
			}

			for (const el of pageElements.slice(startIdx)) {
				const txt = el.textContent?.trim() || '';
				if (!txt) continue;
				let elCfi: string | undefined;
				try {
					if (section?.cfiFromElement) elCfi = section.cfiFromElement(el);
				} catch {}
				splitIntoChunks(txt).forEach((chunk) =>
					result.push({ text: chunk, elements: [el], cfi: elCfi })
				);
			}
		}
		return result;
	}

	/**
	 * Gira a la siguiente página y reconstruye la cola para continuar la narración.
	 * Llamado cuando la cola se agota (último párrafo de la página terminó).
	 */
	async function continueToNextPage() {
		if (!rendition) {
			isAudioPlaying = false;
			return;
		}

		isTurningPagePromise = new Promise((resolve) => {
			resolveTurnPage = resolve;
			// Seguro de timeout: si relocated no llega en 3s, continuar de todas formas
			setTimeout(() => {
				if (resolveTurnPage) {
					resolveTurnPage();
					resolveTurnPage = null;
					isTurningPagePromise = null;
				}
			}, 3000);
		});

		try {
			await rendition.next();
		} catch (err) {
			console.warn('[TTS] Page turn failed:', err);
			if (resolveTurnPage) {
				resolveTurnPage();
				resolveTurnPage = null;
				isTurningPagePromise = null;
			}
			isAudioPlaying = false;
			return;
		}

		// Esperar a que relocated confirme la nueva página
		await isTurningPagePromise;

		// Esperamos un frame de render para garantizar que Epub.js haya aplicado
		// el CSS transform/scroll y el layout de los iframes esté actualizado.
		await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));

		// Reconstruir cola para la nueva página
		readingQueue = buildPageQueue();
		const iframe2 = getEpubIframe();
		console.log('[TTS] New page queue size:', readingQueue.length,
			'| iframeWidth:', iframe2?.contentWindow?.innerWidth,
			'| viewerWidth:', viewerElement?.clientWidth,
			'| first left:', readingQueue[0]?.elements[0]?.getBoundingClientRect().left);
		if (readingQueue.length > 0) {
			playItem(0);
		} else {
			isAudioPlaying = false;
		}
	}

	// ---------- Audio prefetch helpers ----------
	async function fetchAudioUrl(text: string): Promise<string> {
		const url = new URL(`${BACKEND_URL}${ttsMode === 'gcloud' ? '' : '/text_to_audio'}`);

		let response: Response;

		if (ttsMode === 'local') {
			// Local backend: usa query params y body JSON con text
			url.searchParams.append('tts_provider', ttsEngine);
			url.searchParams.append('lang', ttsLang);
			if (ttsEngine === 'piper' && piperVoiceKey) {
				url.searchParams.append('piper_voice_key', piperVoiceKey);
			}
			if (ttsEngine === 'kokoro' && kokoroVoice) {
				url.searchParams.append('kokoro_voice', kokoroVoice);
			}

			console.log('TTS request (local)', {
				text,
				engine: ttsEngine,
				lang: ttsLang,
				piperVoiceKey,
				kokoroVoice
			});

			response = await fetch(url.toString(), {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ text })
			});
		} else {
			// GCloud backend: enviar todo en el body y sin query params
			// provider: 'gtts' o 'cloud_tts'
			const body: any = {
				text,
				provider: ttsEngine,
				lang: ttsLang
			};
			if (ttsEngine === 'cloud_tts' && cloudVoiceName) {
				body.voice_name = cloudVoiceName;
			}

			console.log('TTS request (gcloud)', body);

			response = await fetch(url.toString(), {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(body)
			});
		}

		if (!response.ok) {
			const errorText = await response.text().catch(() => '');
			throw new Error(`TTS request failed: ${response.status} - ${errorText}`);
		}

		const blob = await response.blob();
		return URL.createObjectURL(blob);
	}

	function clearHighlight() {
		currentReadingElements.forEach((el) => (el.style.backgroundColor = ''));
		currentReadingElements = [];
	}

	async function playItem(index: number) {
		if (index >= readingQueue.length) {
			isAudioPlaying = false;
			return;
		}
		const item = readingQueue[index];
		const targetElement = item.elements?.[0];

		if (isTurningPagePromise) {
			await isTurningPagePromise;
		}

		// Clear previous highlights first
		clearHighlight();

		// En Epub.js 0.3.x los nodos de las páginas no se destruyen en paginated mode (siguen vivos en columnas ocultas del DOM).
		// Re-vincularlos desde el CFI falla porque retorna un rango ampliado, volviendo amarillo todo el libro.
		// Así que confiaremos en las referencias originales de HTMLElement guardadas en 'elements'.

		// Get the elements to highlight
		currentReadingElements = item.elements;

		if (isTurningPagePromise) {
			await isTurningPagePromise;
		}

		// Apply the highlight
		currentReadingElements.forEach((el) => {
			if (el && el.style) {
				el.style.backgroundColor = 'rgba(255,255,0,0.3)';
			}
		});

		// Stop any current audio before starting new one
		if (currentAudio) {
			currentAudio.pause();
			currentAudio.src = '';
			currentAudio = null;
			isAudioPlaying = false;
		}

		// ensure audio fetched
		if (!item.audioUrlPromise) {
			item.audioUrlPromise = fetchAudioUrl(item.text);
		}
		const audioUrl = await item.audioUrlPromise;

		// prefetch next
		if (index + 1 < readingQueue.length) {
			const next = readingQueue[index + 1];
			if (!next.audioUrlPromise) next.audioUrlPromise = fetchAudioUrl(next.text);
		}

		// --- Fast cross-fade helpers (≈100–150 ms) ---
		const fadeOut = (audio: HTMLAudioElement, cb: () => void) => {
			const step = 0.1; // reduce volume by 10 % each tick
			const interval = setInterval(() => {
				if (audio.volume > step) {
					audio.volume = Math.max(0, audio.volume - step);
				} else {
					clearInterval(interval);
					cb();
				}
			}, 10); // run every 10 ms → ~100 ms total
		};

		// Fast fade-in (~50 ms) to avoid audible "tump" at start.
		const fadeIn = (audio: HTMLAudioElement) => {
			audio.volume = 0;
			const step = 1; // +20 % each tick
			const interval = setInterval(() => {
				if (audio.volume < 1 - step) {
					audio.volume = Math.min(1, audio.volume + step);
				} else {
					audio.volume = 1;
					clearInterval(interval);
				}
			}, 50); // 10 ms tick → 40–50 ms total
		};

		// play
		currentAudio = new Audio(audioUrl);
		audioEl = currentAudio;
		audioEl = currentAudio;
		audioEl = currentAudio;
		currentAudio.volume = 0; // start muted to prevent click
		currentAudio.play();
		fadeIn(currentAudio);
		isAudioPlaying = true;
		setupMediaSession();
		if (browser && 'mediaSession' in navigator)
			navigator.mediaSession.playbackState = 'playing';

		// Cuando el audio termina, reproducimos el siguiente o giramos de página si la cola se agotó.
		currentAudio.addEventListener('ended', async () => {
			const nextIndex = index + 1;
			if (nextIndex >= readingQueue.length) {
				// Cola agotada: girar página y continuar si TTS sigue activo
				if (isAudioPlaying && rendition) {
					await continueToNextPage();
				} else {
					isAudioPlaying = false;
				}
				return;
			}
			playItem(nextIndex);
		}, { once: true });
	}

	let isSettingsOpen = false;

	// Dynamically adjust bottom padding so text is never hidden by footer
	let footerElement: HTMLDivElement | null = null;
	let headerElement: HTMLElement | null = null;
	$: if (viewerElement && footerElement && headerElement) {
		const footerH = footerElement.offsetHeight;
		const headerH = headerElement.offsetHeight;
		// Shrink viewer so it doesn't go under footer
		viewerElement.style.height = `calc(100% - ${footerH}px - ${headerH}px)`;
		// Also ensure inner EPUB iframe has bottom margin so last line isn't hidden
		if (rendition) {
			const cssPadding = `body { margin-bottom: ${footerH + 16}px !important; margin-top: ${headerH + 16}px !important; }`;
			rendition.themes.override('body', cssPadding);
			// Ensure future spine items also get padding
			if (!(rendition as any).__paddingHookAdded) {
				rendition.hooks.content.register((contents: any) => {
					const doc = contents.document;
					const style = doc.createElement('style');
					style.textContent = cssPadding;
					doc.head.appendChild(style);
				});
				(rendition as any).__paddingHookAdded = true;
			}
		}
	}

	onDestroy(() => {
		if (browser && 'mediaSession' in navigator) {
			navigator.mediaSession.playbackState = 'none';
			navigator.mediaSession.setActionHandler('play', null);
			navigator.mediaSession.setActionHandler('pause', null);
			navigator.mediaSession.setActionHandler('stop', null);
		}
	});

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
			const savedPlaybackRate = localStorage.getItem('playbackRate');
			const storedTtsMode = localStorage.getItem('tts-mode');
			const storedKokoroVoice = localStorage.getItem('kokoro-voice');
			const storedCloudVoiceName = localStorage.getItem('cloud-voice-name');

			if (storedTtsEngine) ttsEngine = storedTtsEngine;
			if (storedTtsLang) ttsLang = storedTtsLang;
			if (storedPiperVoiceKey) piperVoiceKey = storedPiperVoiceKey;
			if (storedTtsMode) ttsMode = storedTtsMode as 'local' | 'gcloud';
			if (storedKokoroVoice) kokoroVoice = storedKokoroVoice;
			if (storedCloudVoiceName) cloudVoiceName = storedCloudVoiceName;
			if (savedPlaybackRate) {
				const v = parseFloat(savedPlaybackRate);
				if (!Number.isNaN(v)) {
					// Limitar al rango 0.5x–2.0x
					playbackRate = Math.min(2, Math.max(0.5, v));
				}
			}
		}

		isLoadingLocations = false;

		const initEpubViewer = async () => {
			cleanupPreviousInstance(); // Primero, limpiar cualquier instancia previa del visor EPUB

			// Reiniciar los estados del componente al inicio de la carga
			isLoading = true;
			errorMessage = undefined;
			currentBook = undefined;
			currentChapterTitle = '';

			const bookId = $page.params.bookId;
			if (!bookId) {
				// Verificar si el bookId (de la URL) está presente
				errorMessage = $_('reader.error.noBookId', { default: 'Book ID not provided.' });
				isLoading = false;
				return;
			}

			const books = $bookStore;
			const foundBook = books.find((b) => b.id === bookId);
			if (!foundBook) {
				// Si no se encuentra el libro en el store, mostrar error
				errorMessage = $_('reader.error.bookNotFound', {
					default: 'Book not found in your library.'
				});
				isLoading = false;
				return;
			}
			currentBook = foundBook;

			if (!currentBook.data) {
				// Verificar si el libro tiene los datos (ArrayBuffer) necesarios para renderizar
				console.error('Book data (ArrayBuffer) is missing for book:', currentBook.id);
				errorMessage = $_('reader.error.epubLoadFailed', {
					default: 'Book data is missing or corrupted.'
				});
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
				console.error(
					'EPUB viewer element (#viewer) still not found in DOM after isLoading=false and tick.'
				);
				errorMessage = $_('reader.error.epubLoadFailed', {
					default: 'Viewer element failed to render.'
				});
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

				// --- Lógica de Clic para Hablar (TTS) ---
				// Simplificada: utilizamos el target del evento para obtener el bloque más cercano (p, li, h1-h6)
				tempRendition.on('click', (event: MouseEvent) => {
					console.log('EPUBJS CLICK EVENT RECEIVED:', event);

					// Mark user interaction
					isUserInteracting = true;
					setTimeout(() => {
						isUserInteracting = false;
					}, 2000); // Reset after 2 seconds

					// Stop any current audio and clear queue
					if (currentAudio) {
						currentAudio.pause();
						currentAudio.src = '';
						currentAudio = null;
						isAudioPlaying = false;
					}
					clearHighlight();
					readingQueue = [];

					const target = event.target as HTMLElement | null;
					if (!target) return;

					const blockElement = target.closest('p, li, h1, h2, h3, h4, h5, h6');
					if (!blockElement) return;

					// --------- CONSTRUCCIÓN DE COLA PARA PÁGINA ACTUAL Y REPRODUCCIÓN ---------
					readingQueue = buildPageQueue(blockElement as HTMLElement);
					console.log('Queue size', readingQueue.length);
					if (readingQueue.length > 0) playItem(0);
				});

				// Manejar cambios de ubicación (evento correcto: 'relocated')
				tempRendition.on('relocated', (location: any) => {
					if (resolveTurnPage) {
						resolveTurnPage();
						resolveTurnPage = null;
						isTurningPagePromise = null;
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
						if (locationsTotal > 0 && epubInstance.locations) {
							// Asegurarse de que locations exista
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
				tempEpubInstance.locations
					.generate(1000)
					.then(() => {
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
					})
					.catch((err: unknown) => {
						console.error('Error generating locations', err);
					})
					.finally(() => {
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
				errorMessage = $_('reader.error.epubLoadFailed', {
					default: 'Failed to load the EPUB file.'
				}); // isLoading is already false
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

		// Reanudar audio cuando el usuario vuelve de pantalla bloqueada
		const handleVisibilityChange = () => {
			if (!document.hidden && currentAudio && currentAudio.paused && isAudioPlaying) {
				currentAudio.play().catch(() => {});
				if ('mediaSession' in navigator)
					navigator.mediaSession.playbackState = 'playing';
			}
		};
		document.addEventListener('visibilitychange', handleVisibilityChange);

		return () => {
			document.removeEventListener('visibilitychange', handleVisibilityChange);
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
			} else {
				// 'light' o cualquier otro tema no oscuro
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
	// NUEVO: persistir modo y voces adicionales
	$: if (browser && ttsMode) localStorage.setItem('tts-mode', ttsMode);
	$: if (browser && kokoroVoice) localStorage.setItem('kokoro-voice', kokoroVoice);
	$: if (browser && cloudVoiceName) localStorage.setItem('cloud-voice-name', cloudVoiceName);
	$: if (browser && audioEl) {
		audioEl.playbackRate = playbackRate;
		// En la mayoría de navegadores modernos se mantiene el tono por defecto.
		// Si ves cambios de tono, podemos ajustar preservesPitch si el navegador lo soporta.
		if ('preservesPitch' in audioEl) (audioEl as any).preservesPitch = true;
		if ('preservesPitch' in audioEl) audioEl.preservesPitch = true;
		localStorage.setItem('playbackRate', String(playbackRate));
	}

	async function speakText(textToSpeak: string, element?: HTMLElement) {
		if (!textToSpeak.trim()) {
			console.warn('No text to speak.');
			return;
		}
		// Resaltar y desplazar
		if (element) {
			if (currentReadingElement) {
				(currentReadingElement as HTMLElement).style.background = '';
			}
			currentReadingElement = element;
			(currentReadingElement as HTMLElement).style.background = 'rgba(255,255,0,0.3)';
			currentReadingElement.scrollIntoView({ block: 'center', behavior: 'smooth' });
		}

		// Detener la reproducción actual si existe
		if (currentAudio) {
			currentAudio.pause();
			currentAudio.src = '';
			currentAudio = null;
			isAudioPlaying = false;
		}

		try {
			console.log('Text to Speech (streaming):', textToSpeak);

			const url = new URL(`${BACKEND_URL}${ttsMode === 'gcloud' ? '' : '/text_to_audio'}`);

			let response: Response;

			if (ttsMode === 'local') {
				// Local backend: usa query params y body JSON con text
				url.searchParams.append('tts_provider', ttsEngine);
				url.searchParams.append('lang', ttsLang);
				if (ttsEngine === 'piper' && piperVoiceKey) {
					url.searchParams.append('piper_voice_key', piperVoiceKey);
				}
				if (ttsEngine === 'kokoro' && kokoroVoice) {
					url.searchParams.append('kokoro_voice', kokoroVoice);
				}

				response = await fetch(url.toString(), {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ text: textToSpeak })
				});
			} else {
				// GCloud backend: enviar todo en el body y sin query params
				const body: any = {
					text: textToSpeak,
					provider: ttsEngine,
					lang: ttsLang
				};
				if (ttsEngine === 'cloud_tts' && cloudVoiceName) {
					body.voice_name = cloudVoiceName;
				}

				response = await fetch(url.toString(), {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify(body)
				});
			}

			if (!response.ok) {
				let errorDetail = response.statusText;
				try {
					const errorData = await response.json();
					errorDetail = errorData.detail || errorData.error || errorDetail;
				} catch {
					/* ignore parsing error */
				}
				throw new Error(`Backend error: ${errorDetail}`);
			}

			// Si el navegador no soporta streaming en fetch, recurrimos al blob completo
			if (!response.body) {
				const audioBlob = await response.blob();
				const audioUrl = URL.createObjectURL(audioBlob);
				currentAudio = new Audio(audioUrl);
				currentAudio.play();
				return;
			}

			const mimeType =
				response.headers.get('content-type')?.split(';')[0] ||
				(ttsEngine === 'piper' ? 'audio/wav' : 'audio/mpeg');

			// Si el tipo no es soportado por MediaSource o es WAV, usar descarga completa
			if (!MediaSource.isTypeSupported(mimeType) || mimeType === 'audio/wav') {
				const audioBlob = await response.blob();
				const fallbackUrl = URL.createObjectURL(audioBlob);
				currentAudio = new Audio(fallbackUrl);
				audioEl = currentAudio;
				isAudioPlaying = true;
				currentAudio.addEventListener('play', () => {
					isAudioPlaying = true;
				});
				currentAudio.addEventListener('pause', () => {
					isAudioPlaying = false;
				});
				currentAudio.addEventListener('ended', () => {
					isAudioPlaying = false;
					if (readingQueue.length) {
						const next = readingQueue.shift();
						if (next) {
							readingQueue.unshift(next as QueueItem);
							playItem(0);
						}
					}
				});
				currentAudio.play();
				return;
			}

			const mediaSource = new MediaSource();
			const audioUrl = URL.createObjectURL(mediaSource);
			currentAudio = new Audio(audioUrl);
			isAudioPlaying = true; // actualizar inmediatamente
			// Sincronizar estado de reproducción
			currentAudio.addEventListener('play', () => {
				isAudioPlaying = true;
			});
			currentAudio.addEventListener('pause', () => {
				isAudioPlaying = false;
			});
			currentAudio.addEventListener('ended', () => {
				isAudioPlaying = false;
				if (readingQueue.length) {
					const next = readingQueue.shift();
					if (next) {
						readingQueue.unshift(next as QueueItem);
						playItem(0);
					}
				}
			});
			currentAudio.play();

			mediaSource.addEventListener('sourceopen', () => {
				const sourceBuffer = mediaSource.addSourceBuffer(mimeType);
				const reader = response.body!.getReader();
				const queue: Uint8Array[] = [];

				const appendNextChunk = () => {
					if (queue.length && !sourceBuffer.updating) {
						const chunk = queue.shift()!;
						sourceBuffer.appendBuffer(
							chunk.buffer instanceof ArrayBuffer
								? chunk.buffer
								: new Uint8Array(chunk.buffer as unknown as ArrayBuffer)
						);
					}
				};

				const pump = async () => {
					const { value, done } = await reader.read();

					if (done) {
						if (!sourceBuffer.updating) {
							mediaSource.endOfStream();
						} else {
							sourceBuffer.addEventListener('updateend', () => mediaSource.endOfStream(), {
								once: true
							});
						}
						return;
					}

					if (value) {
						if (sourceBuffer.updating || queue.length) {
							queue.push(value);
						} else {
							sourceBuffer.appendBuffer(value);
						}
					}

					if (!sourceBuffer.updating) {
						pump();
					}
				};

				sourceBuffer.addEventListener(
					'updateend',
					() => {
						appendNextChunk();
					},
					false
				);

				pump();
			});
		} catch (error) {
			console.error('Error speaking text (streaming):', error);
		}
	}

	function toggleSettings() {
		isSettingsOpen = !isSettingsOpen;
	}
	function closeSettings() {
		isSettingsOpen = false;
	}

	function setupMediaSession() {
		if (!browser || !('mediaSession' in navigator)) return;
		navigator.mediaSession.metadata = new MediaMetadata({
			title: currentBook?.title ?? 'Leyendo...',
			artist: 'Voxenfy',
			album: currentBook?.title ?? '',
			artwork: [
				{ src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
				{ src: '/icon-512.png', sizes: '512x512', type: 'image/png' }
			]
		});
		navigator.mediaSession.setActionHandler('play', () => {
			currentAudio?.play();
			isAudioPlaying = true;
			navigator.mediaSession.playbackState = 'playing';
		});
		navigator.mediaSession.setActionHandler('pause', () => {
			currentAudio?.pause();
			isAudioPlaying = false;
			navigator.mediaSession.playbackState = 'paused';
		});
		navigator.mediaSession.setActionHandler('stop', () => {
			if (currentAudio) {
				currentAudio.pause();
				currentAudio.src = '';
				currentAudio = null;
			}
			isAudioPlaying = false;
			navigator.mediaSession.playbackState = 'none';
		});
	}

	function toggleAudio() {
		if (!currentAudio) return;
		if (currentAudio.paused) {
			currentAudio.play();
			isAudioPlaying = true;
			if (browser && 'mediaSession' in navigator)
				navigator.mediaSession.playbackState = 'playing';
		} else {
			currentAudio.pause();
			isAudioPlaying = false;
			if (browser && 'mediaSession' in navigator)
				navigator.mediaSession.playbackState = 'paused';
		}
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
			if (event.type === 'mousedown' || (event.type === 'mousemove' && isDraggingProgressBar)) {
				// Solo navega si es click o drag activo
				rendition.display(cfi);
			}
			// Actualizar texto del tooltip
			if (epubInstance.locations) {
				const pageIndex = (epubInstance.locations as any).locationFromCfi(cfi);
				const pageNum = (pageIndex ?? -1) + 1;
				const percentageDisplay = Math.round(percentage * 100);
				tooltipText = `${percentageDisplay}% (${pageNum > 0 ? pageNum : '...'} / ${locationsTotal})`;
			} else if (percentage !== currentPercentage) {
				// Mostrar solo porcentaje si locations no está listo y el porcentaje cambia
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
		if (
			rendition &&
			!isDraggingProgressBar &&
			target.tagName !== 'INPUT' &&
			target.tagName !== 'SELECT' &&
			target.tagName !== 'TEXTAREA' &&
			target.getAttribute('role') !== 'slider'
		) {
			if (event.key === 'ArrowLeft') {
				// Mark user interaction
				isUserInteracting = true;
				setTimeout(() => {
					isUserInteracting = false;
				}, 2000);

				rendition.prev();
				event.preventDefault(); // Prevenir scroll de página
			} else if (event.key === 'ArrowRight') {
				// Mark user interaction
				isUserInteracting = true;
				setTimeout(() => {
					isUserInteracting = false;
				}, 2000);

				rendition.next();
				event.preventDefault(); // Prevenir scroll de página
			}
		}
	}

	function updateTooltipOnFocus() {
		if (rendition && epubInstance?.locations && locationsTotal > 0 && progressBarElement) {
			const percentageDisplay = Math.round(currentPercentage * 100);
			tooltipText = `${percentageDisplay}% (${currentPageInLocations} / ${locationsTotal})`;
		} else if (currentPercentage >= 0 && progressBarElement) {
			// Mostrar solo % si no hay locations o están cargando
			tooltipText = `${Math.round(currentPercentage * 100)}%`;
		} else {
			tooltipText = ''; // O un valor por defecto si se prefiere
		}
	}
</script>

<svelte:head>
	<title>
		{currentBook ? currentBook.title : $_('reader.pageTitle', { default: 'Reader' })} - {$_(
			'pageTitle',
			{ default: 'Read Me a Book' }
		)}
	</title>
	<meta
		name="description"
		content={$_('reader.metaDescription', {
			values: { bookTitle: currentBook?.title || 'book' },
			default: `Reading ${currentBook?.title || 'book'}`
		})}
	/>
</svelte:head>

<div class="bg-background text-text-base flex h-screen flex-col">
	{#if !isLoading && !errorMessage}
		<!-- Header unificado: se muestra si no hay carga ni error -->
		<header
			bind:this={headerElement}
			class="border-border bg-surface flex flex-shrink-0 items-center justify-between border-b p-3 shadow-sm"
		>
			<button
				on:click={() => goto('/')}
				class="hover:bg-surface-hover text-text-muted hover:text-text-base rounded-md p-2"
				aria-label={$_('reader.backToLibrary', { default: 'Back to library' })}
			>
				<ArrowLeft size={24} />
			</button>
			<div class="mx-2 flex-grow overflow-hidden text-center">
				{#if currentBook}
					<h1 class="truncate text-lg font-semibold" title={currentBook.title}>
						{currentBook.title}
					</h1>
					{#if currentChapterTitle}
						<p class="text-text-muted truncate text-xs" title={currentChapterTitle}>
							{currentChapterTitle}
						</p>
					{/if}
				{:else}
					<h1 class="truncate text-lg font-semibold">
						{$_('reader.pageTitle', { default: 'Reader' })}
					</h1>
				{/if}
			</div>
			<div class="w-10 flex-shrink-0">
				<!-- Botón de settings -->
				{#if rendition}
					<!-- Botón de settings solo si el libro está cargado y renderizado -->
					<div class="relative">
						<button
							on:click={toggleSettings}
							class="hover:bg-surface-hover text-text-muted hover:text-text-base rounded-md p-2"
							aria-label="Open settings"
							aria-haspopup="true"
							aria-expanded={isSettingsOpen}
						>
							<Settings size={24} />
						</button>
						{#if isSettingsOpen}
							<div
								class="bg-surface border-border absolute right-0 top-full z-20 mt-2 w-56 rounded-lg border p-2 shadow-xl"
								role="menu"
								use:clickOutside
								on:click_outside={closeSettings}
							>
								<div class="px-2 py-1"><ThemeSwitcher /></div>
								<div class="px-2 py-1"><LanguageSwitcher /></div>
								<div class="px-2 py-1"><FontSizeSwitcher currentRendition={rendition} /></div>

								<!-- NUEVO: selector de modo -->
								<div class="px-2 py-1">
									<label class="text-text-muted mb-1 block text-sm font-medium">Modo</label>
									<select
										bind:value={ttsMode}
										class="bg-background hover:bg-surface border-border text-text-muted focus-visible:ring-primary w-full cursor-pointer appearance-none rounded-md border py-2 pl-3 pr-8 transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2"
									>
										<option value="local">Local</option>
										<option value="gcloud">GCloud</option>
									</select>
								</div>

								<!-- TTS Configurator con nuevas props -->
								<div class="px-2 py-1">
									<TtsConfigurator
										bind:ttsEngine
										bind:ttsLang
										bind:piperVoiceKey
										bind:playbackRate
										mode={ttsMode}
										bind:kokoroVoice
										bind:cloudVoiceName
									/>
								</div>
							</div>
						{/if}
					</div>
				{/if}
			</div>
		</header>
	{/if}

	<main class="relative flex-grow overflow-hidden">
		{#if isLoading}
			<div class="absolute inset-0 flex items-center justify-center">
				<p>{$_('reader.loadingBook', { default: 'Loading book...' })}</p>
			</div>
		{:else if errorMessage}
			<div class="absolute inset-0 flex flex-col items-center justify-center p-4 text-center">
				<p class="text-lg text-red-500">{errorMessage}</p>
				<button on:click={() => goto('/')} class="filled-button mt-4"
					>{$_('reader.backToLibrary', { default: 'Back to Library' })}</button
				>
			</div>
		{:else}
			<!-- Si no está cargando y no hay error, mostrar el visor -->
			<div bind:this={viewerElement} id="viewer" class="epub-viewer-container h-full w-full"></div>

			{#if rendition}
				<!-- Navegación táctil de página -->
				<button
					on:click={() => {
						isUserInteracting = true;
						setTimeout(() => {
							isUserInteracting = false;
						}, 2000);
						rendition!.prev();
					}}
					class="bg-surface/80 hover:bg-surface fixed bottom-28 left-2 z-20 rounded-full p-3 shadow md:bottom-1/2 md:translate-y-1/2"
					aria-label="Página anterior"
				>
					<ArrowLeft size={20} />
				</button>
				<button
					on:click={() => {
						isUserInteracting = true;
						setTimeout(() => {
							isUserInteracting = false;
						}, 2000);
						rendition!.next();
					}}
					class="bg-surface/80 hover:bg-surface fixed bottom-28 right-2 z-20 rounded-full p-3 shadow md:bottom-1/2 md:translate-y-1/2"
					aria-label="Página siguiente"
				>
					<ArrowRight size={20} />
				</button>
			{/if}

			<!-- Pie de página con Barra de Progreso -->
			{#if rendition}
				<!-- La barra de progreso solo se muestra si la rendition está lista -->
				<div
					bind:this={footerElement}
					class="bg-surface/90 border-border shadow-up fixed bottom-0 left-0 right-0 flex flex-col items-center justify-center gap-2 border-t p-3 backdrop-blur-sm"
				>
					{#if isLoadingLocations}
						<p class="text-text-muted text-center text-sm">
							{$_('reader.loadingProgress', { default: 'Loading progress...' })}
						</p>
					{:else if rendition && epubInstance?.locations && locationsTotal > 0}
						<!-- Controles de audio -->
						<div class="mb-2 flex items-center justify-center">
							<button
								on:click|stopPropagation={toggleAudio}
								class="bg-primary shadow-primary/50 hover:bg-primary/90 focus:ring-primary/60 rounded-full p-3 text-white shadow-lg transition hover:shadow-2xl focus:outline-none focus:ring-4"
								aria-label={isAudioPlaying ? 'Pause audio' : 'Play audio'}
							>
								{#if isAudioPlaying}
									<Pause size={24} />
								{:else}
									<Play size={24} />
								{/if}
							</button>
						</div>
						<div class="relative mx-auto w-full max-w-xl">
							<div
								class="bg-border group relative h-2.5 cursor-pointer rounded-full"
								on:click|stopPropagation={handleProgressBarInteraction}
								on:mousedown|stopPropagation={handleProgressBarMouseDown}
								on:mouseleave={() => {
									if (!isDraggingProgressBar) tooltipText = '';
								}}
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
								<div
									class="bg-primary absolute left-0 top-0 h-full rounded-full"
									style:width="{currentPercentage * 100}%"
								/>
								<!-- Indicador Visual (Thumb) -->
								<!-- svelte-ignore element_invalid_self_closing_tag -->
								<div
									class="bg-primary pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 rounded-full opacity-0 shadow-lg transition-opacity group-hover:opacity-100"
									style:left="calc({currentPercentage * 100}% - 8px)"
								/>
							</div>
							<!-- Tooltip -->
							{#if tooltipText && progressBarElement}
								<!-- Mostrar solo si hay texto y el elemento existe -->
								<div
									class="bg-surface border-border text-text-base absolute bottom-full left-1/2 z-20 mb-2 -translate-x-1/2 whitespace-nowrap rounded-md border px-2 py-1 text-xs shadow-lg"
								>
									{tooltipText}
								</div>
							{/if}
							<p class="text-text-muted mt-1.5 text-center text-sm">
								{Math.round(currentPercentage * 100)}%
								{#if currentPageInLocations > 0 && locationsTotal > 0}
									({currentPageInLocations} / {locationsTotal})
								{/if}
							</p>
						</div>
					{:else}
						<p class="text-text-muted text-center text-sm">
							{$_('reader.progressNotAvailable', { default: 'Progress not available' })}
						</p>
					{/if}
				</div>
			{:else}
				<!-- Fallback si rendition no está lista pero no hay error ni carga (después de que el visor se haya intentado renderizar) -->
				<div class="absolute inset-0 flex flex-col items-center justify-center p-4 text-center">
					<p>{$_('reader.error.unexpected', { default: 'Could not display the book.' })}</p>
					<button on:click={() => goto('/')} class="filled-button mt-4"
						>{$_('reader.backToLibrary', { default: 'Back to Library' })}</button
					>
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
	[role='slider']:focus-visible {
		outline: 2px solid rgb(var(--color-primary));
		outline-offset: 2px;
	}
	/* Eliminar el outline por defecto en elementos con tabindex si se prefiere un estilo de foco personalizado */
	/* Asegurar que el thumb sea visible cuando la barra de progreso tiene foco */
	[role='slider']:focus-visible .absolute.top-1\/2.-translate-y-1\/2,
	[role='slider']:hover .absolute.top-1\/2.-translate-y-1\/2 {
		opacity: 1;
	}
	.epub-viewer-container :global(.epub-view) {
		user-select: text !important;
		-webkit-user-select: text !important;
		-moz-user-select: text !important;
		-ms-user-select: text !important;
	}
	.shadow-up {
		box-shadow:
			0 -4px 6px -1px rgb(0 0 0 / 0.1),
			0 -2px 4px -2px rgb(0 0 0 / 0.1);
	}
</style>
