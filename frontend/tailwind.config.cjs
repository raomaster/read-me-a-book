const defaultTheme = require('tailwindcss/defaultTheme');

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', ...defaultTheme.fontFamily.sans],
      },
      colors: {
        primary: 'rgb(var(--color-primary) / <alpha-value>)',
        background: 'rgb(var(--color-background) / <alpha-value>)',
        surface: 'rgb(var(--color-surface) / <alpha-value>)',
        border: 'rgb(var(--color-border) / <alpha-value>)',
        // These are the corrected names:
        'base':    'rgb(var(--color-text-base) / <alpha-value>)',
        'muted':   'rgb(var(--color-text-muted) / <alpha-value>)',
        'on-primary':'rgb(var(--color-text-on-primary) / <alpha-value>)'
      }
    }
  },
  plugins: [require('@tailwindcss/typography')]
};