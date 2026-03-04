/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          violet: {
            50: '#f5f3ff',
            100: '#ede9fe',
            200: '#ddd6fe',
            300: '#c4b5fd',
            400: '#a78bfa',
            500: '#8b5cf6',
            600: '#6B46FF', // Electric Violet (Primary Highlight)
            700: '#5b21b6',
            800: '#4c1d95',
            900: '#2e1065',
            950: '#1E123D', // Dark Indigo (Step/Phase Chips)
          },
          obsidian: {
            DEFAULT: '#0D0B1A', // Primary Background (Cyber-Noir)
            light: '#160D33',   // Secondary Gradient End
            dark: '#2D1B69',    // Secondary Gradient Start
          }
        },
        slate: {
          50: '#f8fafc',
          900: '#0f172a',
          950: '#020617',
        }
      },
      borderRadius: {
        '3xl': '24px',
        '4xl': '32px',
      },
      backdropBlur: {
        xs: '2px',
      }



    },
  },
  plugins: [],
}
