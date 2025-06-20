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
				'primary-hover': 'rgb(var(--color-primary-hover) / <alpha-value>)',
				secondary: 'rgb(var(--color-secondary) / <alpha-value>)',
				'surface-hover': 'rgb(var(--color-surface-hover) / <alpha-value>)',				
				background: 'rgb(var(--color-background) / <alpha-value>)',
				surface: 'rgb(var(--color-surface) / <alpha-value>)',
				border: 'rgb(var(--color-border) / <alpha-value>)',
				'text-base': 'rgb(var(--color-text-base) / <alpha-value>)',
				'text-muted': 'rgb(var(--color-text-muted) / <alpha-value>)',
				'on-primary': 'rgb(var(--color-text-on-primary) / <alpha-value>)'
      }
    }
  },
  plugins: [require('@tailwindcss/typography')]
};