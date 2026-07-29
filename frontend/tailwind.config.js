/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          bg: '#F8FAFC',
          card: '#FFFFFF',
          sidebar: '#F1F5F9',
          border: '#E2E8F0',
          borderLight: '#CBD5E1',
          hover: '#E2E8F0',
        },
        brand: {
          50: '#EEF2FF',
          100: '#E0E7FF',
          500: '#6366F1',
          600: '#4F46E5',
          700: '#4338CA',
          violet: '#7C3AED',
          teal: '#0D9488',
          cyan: '#0284C7',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      }
    },
  },
  plugins: [],
}





