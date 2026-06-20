/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Cormorant Garamond"', 'Georgia', 'serif'],
        reading: ['Spectral', 'Georgia', 'serif'],
        ui: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        ink: {
          50: '#f6f6f4',
          900: '#0a0b0c',
          950: '#060708',
        },
        kafka: {
          deep: '#0c1411',
          moss: '#1b2a23',
          sage: '#5f7a6b',
          cold: '#a9c4b4',
        },
        dostoevsky: {
          deep: '#160a0c',
          ember: '#7a1f24',
          candle: '#e8a85c',
          snow: '#e7e2dc',
        },
        orwell: {
          deep: '#101113',
          concrete: '#3a3d42',
          warning: '#c8302b',
          fog: '#b7bcc2',
        },
      },
      letterSpacing: {
        widest2: '0.32em',
      },
      transitionTimingFunction: {
        luxe: 'cubic-bezier(0.22, 1, 0.36, 1)',
      },
      keyframes: {
        drift: {
          '0%': { transform: 'translateY(0) translateX(0)', opacity: '0' },
          '15%': { opacity: '0.5' },
          '85%': { opacity: '0.4' },
          '100%': { transform: 'translateY(-120px) translateX(20px)', opacity: '0' },
        },
        sway: {
          '0%, 100%': { transform: 'translateX(-2%) rotate(-0.4deg)' },
          '50%': { transform: 'translateX(2%) rotate(0.4deg)' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: '0.35' },
          '50%': { opacity: '0.6' },
        },
      },
      animation: {
        sway: 'sway 14s ease-in-out infinite',
        pulseGlow: 'pulseGlow 6s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
