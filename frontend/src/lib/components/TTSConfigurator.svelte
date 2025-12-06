<script lang="ts">
    // Componente: TTSConfigurator.svelte
    import { _ } from 'svelte-i18n';
    // NUEVO: para carga automática al montar en gcloud
    import { onMount } from 'svelte';
    
    export let ttsEngine: string;
    export let ttsLang: string;
    export let piperVoiceKey: string;
    export let playbackRate: number = 1;
    // NUEVO: modo de entorno ('local'|'gcloud'), por defecto local
    export let mode: 'local' | 'gcloud' = 'local';
    // NUEVO: nombre de voz para Cloud TTS (API)
    export let cloudVoiceName: string = '';
    // NUEVO: voz de Kokoro (solo local, español)
    export let kokoroVoice: string = 'ef_dora';

    // NUEVO: URL del backend (igual que en reader/+page.svelte)
    const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'https://leeme.mooo.com/api';

    // Proveedores por modo
    const ttsProvidersLocal = [
        { value: 'piper', label: 'Piper (Local)' },
        { value: 'gtts', label: 'gTTS (Local)' },
        { value: 'kokoro', label: 'Kokoro (Local)' }
    ];
    const ttsProvidersGcloud = [
        { value: 'cloud_tts', label: 'Google Cloud TTS (API)' },
        { value: 'gtts', label: 'gTTS (API)' }
    ];

    // Derivar proveedores disponibles según modo
    $: availableTtsProviders = mode === 'local' ? ttsProvidersLocal : ttsProvidersGcloud;

    // Voces Kokoro (español)
    const kokoroVoices = [
        { value: 'ef_dora', label: 'Kokoro - ef_dora (Español)' },
        { value: 'em_alex', label: 'Kokoro - em_alex (Español)' },
        { value: 'em_santa', label: 'Kokoro - em_santa (Español)' }
    ];
    // Voces Piper (local), incluyendo es_AR
    const piperVoices = [
        { value: 'es_AR-daniela-high', label: 'Spanish (Argentina) - Daniela High' },
        { value: 'es_ES-carlfm-high', label: 'Spanish (Spain) - Carlfm High' },
        { value: 'es_ES-mls_9972-low', label: 'Spanish (Spain) - MLS Low' },
        { value: 'es_MX-claude-high', label: 'Spanish (Mexico) - Claude High' },
        { value: 'es_MX-ald-medium', label: 'Spanish (Mexico) - Ald Medium' },
        { value: 'es_MX-laura-high', label: 'Spanish (Mexico) - Laura High' }
    ];

    // Voces para Cloud TTS (API) — ampliadas en español (es-ES y es-US)
    const cloudTtsVoices = [
        // Español (España) - Standard
        { name: 'es-ES-Standard-A', label: 'es-ES Standard A' },
        { name: 'es-ES-Standard-B', label: 'es-ES Standard B' },
        { name: 'es-ES-Standard-C', label: 'es-ES Standard C' },
        { name: 'es-ES-Standard-D', label: 'es-ES Standard D' },

        // Español (España) - WaveNet
        { name: 'es-ES-Wavenet-A', label: 'es-ES WaveNet A' },
        { name: 'es-ES-Wavenet-B', label: 'es-ES WaveNet B' },
        { name: 'es-ES-Wavenet-C', label: 'es-ES WaveNet C' },
        { name: 'es-ES-Wavenet-D', label: 'es-ES WaveNet D' },

        // Español (Estados Unidos) - Standard
        { name: 'es-US-Standard-A', label: 'es-US Standard A' },
        { name: 'es-US-Standard-B', label: 'es-US Standard B' },
        { name: 'es-US-Standard-C', label: 'es-US Standard C' },
        { name: 'es-US-Standard-D', label: 'es-US Standard D' },

        // Español (Estados Unidos) - WaveNet
        { name: 'es-US-Wavenet-A', label: 'es-US WaveNet A' },
        { name: 'es-US-Wavenet-B', label: 'es-US WaveNet B' },
        { name: 'es-US-Wavenet-C', label: 'es-US WaveNet C' },
        { name: 'es-US-Wavenet-D', label: 'es-US WaveNet D' },

        // Opcional: deja algunas en inglés por si eliges ttsLang='en'
        { name: 'en-US-Standard-A', label: 'en-US Standard A' },
        { name: 'en-US-Standard-B', label: 'en-US Standard B' }
    ];

    // Filtrado por idioma seleccionado
    let filteredCloudVoices = cloudTtsVoices.filter(v => {
        if (ttsLang === 'es') return v.name.startsWith('es-');
        if (ttsLang === 'en') return v.name.startsWith('en-');
        return true;
    });

    // Reactividad: actualizar filtrado si cambian voces/idioma
    $: filteredCloudVoices = cloudTtsVoices.filter(v => {
        if (ttsLang === 'es') return v.name.startsWith('es-');
        if (ttsLang === 'en') return v.name.startsWith('en-');
        return true;
    });




    // Garantizar que el engine sea válido para el modo
    $: {
        if (mode === 'gcloud' && !['gtts', 'cloud_tts'].includes(ttsEngine)) {
            ttsEngine = 'cloud_tts';
        }
        if (mode === 'local' && !['piper', 'gtts', 'kokoro'].includes(ttsEngine)) {
            ttsEngine = 'piper';
        }
    }

    // Defaults de voz al cambiar engine/idioma
    $: {
        // Mantener defaults de Piper
        if (!piperVoiceKey) {
            piperVoiceKey = piperVoices[0]?.value || '';
        }
        // Mantener defaults de Kokoro, SIN tocar ttsLang aquí
        if (mode === 'local' && ttsEngine === 'kokoro') {
            if (!kokoroVoice) {
                kokoroVoice = kokoroVoices[0]?.value || 'ef_dora';
            }
        }
        // ELIMINADO: no establecer cloudVoiceName aquí (para evitar ciclo), lo hacemos en bloque aparte
        // ELIMINADO: no forzar ttsLang aquí (para evitar ciclo), lo hacemos en bloque aparte
    }

    // NUEVO: forzar español cuando se selecciona Kokoro (no depende de filteredCloudVoices)
    $: if (mode === 'local' && ttsEngine === 'kokoro' && ttsLang !== 'es') {
        ttsLang = 'es';
    }

    // NUEVO: default de cloudVoiceName en modo gcloud (depende de filteredCloudVoices, NO modifica ttsLang)
    $: if (mode === 'gcloud' && ttsEngine === 'cloud_tts') {
        if (!cloudVoiceName || !filteredCloudVoices.some(v => v.name === cloudVoiceName)) {
            cloudVoiceName = filteredCloudVoices[0]?.name || '';
        }
    }

    const supportedLanguages = [
        { value: 'es', label: 'Español' },
        { value: 'en', label: 'English' }
    ]
</script>

<div class="space-y-4">
    <div>
        <label for="tts-engine-select"
            class="block text-sm font-medium text-text-muted mb-1"
            >
            {$_('reader.ttssEngineLabel', {default: 'TTS Engine'})}
        </label>

        <select
            id="tts-engine-select"
            bind:value={ttsEngine}
            class="w-full appearance-none bg-background hover:bg-surface border border-border rounded-md py-2 pl-3 pr-8 text-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary transition-colors duration-200 cursor-pointer"
        >
            {#each availableTtsProviders as provider}
                <option value={provider.value}>{provider.label}</option>
            {/each}
        </select>
    </div>
    <div>
        <label for="tts-lang-select" class="block text-sm font-medium text-text-muted mb-1">
            {$_('reader.ttsLanguageLabel', { default: 'Language' })}
        </label>
        <select
            id="tts-lang-select"
            bind:value={ttsLang}
            class="w-full appearance-none bg-background hover:bg-surface border border-border rounded-md py-2 pl-3 pr-8 text-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary transition-colors duration-200 cursor-pointer"
        >
            {#each supportedLanguages as langOption}
                <option value={langOption.value}>{langOption.label}</option>
            {/each}
        </select>
    </div>

    {#if mode === 'local' && ttsEngine === 'piper'}
        <div>
            <label for="piper-voice-select" class="block text-sm font-medium text-text-muted mb-1">
                {$_('reader.piperVoiceLabel', { default: 'Piper Voice' })}
            </label>
            <select
                id="piper-voice-select"
                bind:value={piperVoiceKey}
                class="w-full appearance-none bg-background hover:bg-surface border border-border rounded-md py-2 pl-3 pr-8 text-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary transition-colors duration-200 cursor-pointer"
            >
                {#each piperVoices as voice}
                    <option value={voice.value}>{voice.label}</option>
                {/each}
            </select>
        </div>
    {/if}

    {#if mode === 'local' && ttsEngine === 'kokoro'}
        <div>
            <label for="kokoro-voice-select" class="block text-sm font-medium text-text-muted mb-1">
                {$_('reader.kokoroVoiceLabel', { default: 'Kokoro Voice' })}
            </label>
            <select
                id="kokoro-voice-select"
                bind:value={kokoroVoice}
                class="w-full appearance-none bg-background hover:bg-surface border border-border rounded-md py-2 pl-3 pr-8 text-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary transition-colors duration-200 cursor-pointer"
            >
                {#each kokoroVoices as v}
                    <option value={v.value}>{v.label}</option>
                {/each}
            </select>
        </div>
    {/if}

    {#if mode === 'gcloud' && ttsEngine === 'cloud_tts'}
        <div>
            <label for="cloud-voice-select" class="block text-sm font-medium text-text-muted mb-1">
                {$_('reader.cloudTtsVoiceLabel', { default: 'Cloud TTS Voice' })}
            </label>

            <select
                id="cloud-voice-select"
                bind:value={cloudVoiceName}
                class="w-full appearance-none bg-background hover:bg-surface border border-border rounded-md py-2 pl-3 pr-8 text-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary transition-colors duration-200 cursor-pointer"
            >
                {#each filteredCloudVoices as v}
                    <option value={v.name}>{v.label}</option>
                {/each}
            </select>
        </div>
    {/if}

    <div class="mt-3">
        <label class="block text-sm font-medium mb-1">{$_('reader.playbackSpeedLabel', { default: 'Playback Speed' })}</label>
        <input
            type="range"
            min="0.5"
            max="2"
            step="0.1"
            bind:value={playbackRate}
            class="w-full"
        />
        <div class="text-xs mt-1">{playbackRate}x</div>
    </div>
</div>