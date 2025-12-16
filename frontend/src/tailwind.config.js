/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Your specific palette
        'app-bg': "#001233",      // Deepest Navy
        'app-surface': "#001845", // Panel Backgrounds
        'app-border': "#33415c",  // Borders
        'app-accent': "#0466c8",  // Primary Blue (Action)
        'app-accent-sub': "#0353a4", // Secondary Blue
        'text-main': "#ffffff",
        'text-muted': "#979dac",  // Muted Grey/Blue
      },
      fontFamily: {
        // Apple-style font stack
        sans: ['"SF Pro Display"', '-apple-system', 'BlinkMacSystemFont', '"Inter"', 'sans-serif'],
        mono: ['"SF Mono"', 'Menlo', 'monospace'],
      },
      boxShadow: {
        'subtle': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.2), 0 2px 4px -1px rgba(0, 0, 0, 0.1)',
      }
    },
  },
  plugins: [],
}