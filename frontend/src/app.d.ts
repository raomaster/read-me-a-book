// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}

	// New event: click_outside
	namespace svelte.JSX {
		interface HTMLAttributes<T extends EventTarget> {
			'on:click_outside'?: (event: CustomEvent<any>  & { target: T } ) => void;
		}
	}

	/** Custom event `click_outside` para acciones/directivas */
	namespace svelteHTML {
		interface HTMLAttributes<T extends EventTarget = EventTarget> {
			'on:click_outside'?: (e: CustomEvent<void> & { target: T }) => void;
		}
	}
}

export {};
