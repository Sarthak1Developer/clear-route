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
          bg: '#0A0F1D',
          card: '#111827',
          surface: '#1F2937',
          border: '#374151',
          accent: '#06B6D4',
          accentHover: '#0891B2',
          primary: '#3B82F6',
          primaryHover: '#2563EB',
          textMuted: '#9CA3AF',
        },
        congestion: {
          low: '#10B981',      // 0 - 25%
          moderate: '#F59E0B', // 26 - 50%
          high: '#F97316',     // 51 - 75%
          severe: '#EF4444',   // 76 - 100%
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Courier New', 'monospace'],
      }
    },
  },
  plugins: [],
}
