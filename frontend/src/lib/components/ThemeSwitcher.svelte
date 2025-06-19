<script lang='ts'>
    import themeStore , { type Theme } from "$lib/store/theme.store";
    
    const themes: Theme[] = ['light', 'dark', 'ocean', 'princess'];

    function handleThemeChange(event: Event) {
        const target = event.target as HTMLSelectElement;
        themeStore.set(target.value as Theme)
    }
</script>


<div class="theme-switcher flex items-center gap-2">
    <label for="theme-select" class="text-sm font-medium text-text-muted">Theme:</label>
    <select 
        name="theme-select"
        class="rounded-md border-border bg-surface p-2 text-sm text-base focus:border-primary focus:ring-primary"
        id="theme-select"
        value={$themeStore}
        on:change={handleThemeChange}
    >
        {#each themes as theme (theme)}
            <option value={theme}>{theme.charAt(0).toUpperCase() + theme.slice(1)}</option>
        {/each}
    </select>
</div>