<script lang="ts">
    import { setLocale } from "$lib/i18n";
    import { locale as currentLocale, _ } from 'svelte-i18n' // Import the translation stor
    
    const suportedLocales = [
        {code: 'es', name: 'Español'},
        {code: 'en', name: 'English'}
    ]

    function handleChange(event: Event) {
        const newLocale = (event.target as HTMLSelectElement).value
        console.log("Changing Language", newLocale)
        setLocale(newLocale)
    }

</script>

<div class="relative w-full">
    <label for="language-select" class="block text-sm font-medium text-text-muted mb-1">Language</label>
    <select
        id="language-select"
        name="language"
        value={$currentLocale}
        on:change={handleChange}
        class="w-full appearance-none bg-background hover:bg-surface border border-border rounded-md py-2 pl-3 pr-8 text-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary transition-colors duration-200 cursor-pointer"
    >
        {#each suportedLocales as locale}
            <option value={locale.code}>{locale.name}</option>
        {/each}
    </select>
</div>