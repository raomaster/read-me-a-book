<script lang="ts">

    import { _ } from 'svelte-i18n';
    
    export let ttsEngine: string;
    export let ttsLang: string;
    export let piperVoiceKey: string;

    const ttsProviders = [
        {value: 'piper', label: 'Piper TTSS (Local)'},
        {value: 'gtts', label: 'gTTS (Online)'}
    ]
    // These should ideally come from the backend's PIPER_VOICES_CONFIG
    // For now, hardcode based on the backend context provided.

    const piperVoices =  [
        { value: 'es_MX-claude-high', label: 'Spanish (Mexico) - Claude High' },
        { value: 'es_ES-mls_9972-low', label: 'Spanish (Spain) - MLS Low' }
    ]

    const supportedLanguages = [
        { value: 'en', label: 'English' },
        { value: 'es', label: 'Spanish' }
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
            {#each ttsProviders as provider }
                <option value={provider.value}>{provider.label}</option>
            { /each}
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

    {#if ttsEngine === 'piper'}
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
</div>