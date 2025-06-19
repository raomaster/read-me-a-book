<script lang="ts">
    import ThemeSwitcher from "$lib/components/ThemeSwitcher.svelte";
import { bookStore } from "$lib/store/book.store";

    let fileInput: HTMLInputElement;

    async function handleFileSelect(event: Event) {
        const target = event.target as HTMLInputElement;
        if (target.files && target.files[0]){
            const file = target.files[0]
            await bookStore.addBook(file);
        }
    }
</script>

<!-- The main app canvas with our background color. It takes the full screen height and has padding. -->
<div class="min-h-screen bg-background p-4 sm:p-6 lg:p-8">

  <!-- 
    THIS IS THE NEW CONTENT CARD.
    It has a white background, rounded corners, and a shadow, making it "float"
    above the gray app canvas. All our content will live inside this card.
  -->
  <main class="mx-auto max-w-7xl rounded-lg bg-surface p-4 sm:p-6 lg:p-8 shadow-md">
    
    <!-- The header is now inside the card -->
    <header class="flex items-center justify-between border-b border-border pb-5">
      <h1 class="text-2xl font-bold tracking-tight text-text-base">My Library</h1>
      <ThemeSwitcher />

      <!-- Styled button with professional hover and focus states for accessibility -->
      <button 
        type="button"
        class="
          inline-flex h-12 items-center justify-center gap-2 rounded-lg 
          bg-primary px-6 py-3 
          text-base font-medium text-on-primary 
          duration-200 hover:bg-primary/90 
          focus-visible:outline-offset-2 focus-visible:outline-primary
        "
        on:click={() => fileInput.click()}
      >
        <!-- SVG Icon for the plus sign, for a sharper look -->
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-5 w-5">
          <path d="M10.75 4.75a.75.75 0 0 0-1.5 0v4.5h-4.5a.75.75 0 0 0 0 1.5h4.5v4.5a.75.75 0 0 0 1.5 0v-4.5h4.5a.75.75 0 0 0 0-1.5h-4.5v-4.5Z" />
        </svg> Import Publication
      </button>

      <!-- The file input is visually hidden but still accessible for screen readers -->
      <input
        type="file"
        accept=".epub"
        bind:this={fileInput}
        on:change={handleFileSelect}
        class="sr-only"
      />
    </header>

    <!-- The responsive book grid -->
    <div class="grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3 sm:gap-x-6 lg:grid-cols-4 xl:grid-cols-6 xl:gap-x-8">
      
      {#if $bookStore.length === 0}
        <p class="col-span-full text-center text-muted">You haven't imported any books yet.</p>
      {/if}

      <!-- Each book card is a link that works as a 'group' for hover effects -->
      {#each $bookStore as book (book.id)}
        <a href={`/reader/${encodeURIComponent(book.id)}`} class="group block text-center">
          
          <!-- The container for the cover image with shadows and hover effects -->
          <div class="relative mx-auto h-64 w-44 overflow-hidden rounded-md bg-gray-200 shadow-md transition-all duration-300 group-hover:shadow-xl group-hover:-translate-y-1">
            <img 
              src={book.coverUrl} 
              alt={`Cover of ${book.title}`} 
              class="h-full w-full object-cover" 
            />
          </div>
          
          <!-- Book title and tag -->
          <h3 class="mt-4 block truncate text-sm font-semibold text-gray-900 group-hover:text-indigo-600">{book.title}</h3>
          <p class="mt-1 block text-xs font-medium text-muted">EPUB</p>
        </a>
      {/each}

    </div>
  </main>
</div>