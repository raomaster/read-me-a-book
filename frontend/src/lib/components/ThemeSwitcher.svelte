<script lang='ts'>
    import themeStore , { type Theme } from "$lib/store/theme.store";
    
    const themes: Theme[] = ['light', 'dark', 'princess', 'ocean'];

</script>


<div class="relative w-full sm:w-auto">
    <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
        <svg class="w-5 h-5 text-text-muted" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <!-- Icono SVG (sin cambios) -->
            <path d="M10 2a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 2zM5.05 5.05a.75.75 0 011.06 0l1.06 1.06a.75.75 0 01-1.06 1.06l-1.06-1.06a.75.75 0 010-1.06zM2 10a.75.75 0 01.75-.75h1.5a.75.75 0 010 1.5h-1.5A.75.75 0 012 10zm1.06 5.95a.75.75 0 010-1.06l1.06-1.06a.75.75 0 011.06 1.06l-1.06 1.06a.75.75 0 01-1.06 0zM10 18a.75.75 0 01-.75-.75v-1.5a.75.75 0 011.5 0v1.5A.75.75 0 0110 18zm3.95-1.06a.75.75 0 010 1.06l-1.06 1.06a.75.75 0 01-1.06-1.06l1.06-1.06a.75.75 0 011.06 0zm2.29-8.19a.75.75 0 01.75.75v0a.75.75 0 01-.75.75h-1.5a.75.75 0 010-1.5h1.5zM10 6a4 4 0 100 8 4 4 0 000-8z" />
        </svg>
    </div>
    <label for="theme-select" class="block text-sm font-medium text-text-muted mb-1">Theme</label>
    <select
        aria-label="Select theme"
        id="theme-select"
        bind:value={$themeStore}
        class="
            w-full appearance-none 
            bg-background                             /* CLAVE: Usa el fondo de página para separación visual */
            hover:bg-surface                          /* MEJORA: En hover, se eleva al color de la tarjeta */
            border border-border                      /* Correcto: Borde sutil contra el fondo */
            rounded-md 
            py-2 pl-10 pr-8 
            text-text-muted                           /* Correcto: Texto secundario */
            focus-visible:outline-none                /* Accesibilidad: Anillo de foco solo para teclado */
            focus-visible:ring-2 
            focus-visible:ring-primary
            transition-colors duration-200 cursor-pointer"
    >
        {#each themes as theme (theme)}
            <option value={theme}>{theme.charAt(0).toUpperCase() + theme.slice(1)}</option>
        {/each}
    </select>
</div>