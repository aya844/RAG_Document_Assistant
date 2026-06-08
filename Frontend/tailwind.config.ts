import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        nude: {
          50:  '#faf8f5',
          100: '#f5f1eb',
          200: '#ede9e3',
          300: '#e8e2d9',
          400: '#ddd8d0',
          500: '#cec8bf',
          600: '#b5aea6',
          700: '#8c857c',
          800: '#5c5349',
          900: '#3d3530',
          950: '#2c2825',
        },
      },
      fontFamily: {
        sans:  ['var(--font-dm-sans)', 'sans-serif'],
        serif: ['var(--font-dm-serif)', 'serif'],
      },
    },
  },
  plugins: [],
}
export default config