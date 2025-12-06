import { writable } from "svelte/store";


// Define type for Theme
export type Theme = 'light' | 'dark' | 'princess' |  'ocean'

// Create instanse od Theme with default: null
const themeStore = writable<Theme | null>('light');

export default themeStore
