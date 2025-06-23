/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        united: {
          blue: '#0747A6',
          darkblue: '#1E3D8F',
          gold: '#FFB81C',
          orange: '#FF6B35',
        },
        demand: {
          'very-high': '#FF4B4B',
          'high': '#FFB81C',
          'medium': '#F59E0B',
          'low': '#00C851',
        }
      },
      fontFamily: {
        sans: [
          'Geist',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'system-ui',
          'sans-serif'
        ],
        mono: [
          'Geist Mono',
          'SF Mono',
          'Monaco',
          'Cascadia Code',
          'Roboto Mono',
          'Consolas',
          'Courier New',
          'monospace'
        ],
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1.5', letterSpacing: '-0.01em' }],
        'sm': ['0.875rem', { lineHeight: '1.5', letterSpacing: '-0.01em' }],
        'base': ['1rem', { lineHeight: '1.6', letterSpacing: '-0.011em' }],
        'lg': ['1.125rem', { lineHeight: '1.5', letterSpacing: '-0.017em' }],
        'xl': ['1.25rem', { lineHeight: '1.4', letterSpacing: '-0.019em' }],
        '2xl': ['1.5rem', { lineHeight: '1.3', letterSpacing: '-0.025em' }],
        '3xl': ['1.875rem', { lineHeight: '1.2', letterSpacing: '-0.031em' }],
        '4xl': ['2.25rem', { lineHeight: '1.1', letterSpacing: '-0.037em' }],
      },
      fontWeight: {
        light: '300',
        normal: '400',
        medium: '500',
        semibold: '600',
        bold: '700',
        extrabold: '800',
      },
      letterSpacing: {
        tighter: '-0.05em',
        tight: '-0.025em',
        normal: '-0.011em',
        wide: '0.025em',
        wider: '0.05em',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-in-out',
        'pulse-dot': 'pulseDot 2s infinite',
        'gradient-x': 'gradient-x 3s ease infinite',
      },
      keyframes: {
        'gradient-x': {
          '0%, 100%': {
            'background-size': '200% 200%',
            'background-position': 'left center'
          },
          '50%': {
            'background-size': '200% 200%',
            'background-position': 'right center'
          }
        }
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      transitionProperty: {
        'colors': 'color, background-color, border-color, text-decoration-color, fill, stroke',
      }
    },
  },
  plugins: [],
};