import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: '#0a0a0a',
          surface: '#0d0d0d',
          panel: '#0e0e0e',
          raised: '#141414',
          hover: '#161616',
          active: '#1c1c1c',
        },
        border: {
          DEFAULT: '#1f1f1f',
          strong: '#2a2a2a',
          subtle: '#161616',
        },
        fg: {
          DEFAULT: '#ddd',
          muted: '#aaa',
          dim: '#888',
          faint: '#666',
          fainter: '#555',
        },
        accent: {
          blue: '#9ad',
          green: '#5a8',
          orange: '#c74',
          yellow: '#fc6',
          magenta: '#c5c',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'system-ui', 'sans-serif'],
        mono: ['SF Mono', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      fontSize: {
        '2xs': '10px',
        xs: '11px',
      },
      letterSpacing: {
        widelabel: '1.2px',
        widerlabel: '1.5px',
      },
    },
  },
  plugins: [],
};

export default config;
