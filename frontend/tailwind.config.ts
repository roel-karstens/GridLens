import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        destructive: 'hsl(0 84% 60%)',
        border: 'hsl(216 12.2% 83.9%)',
        input: 'hsl(216 12.2% 83.9%)',
        ring: 'hsl(263 80% 50%)',
        background: 'hsl(0 0% 100%)',
        foreground: 'hsl(215 13.8% 34.9%)',
        primary: {
          DEFAULT: 'hsl(263 80% 50%)',
          foreground: 'hsl(210 40% 98%)',
        },
        secondary: {
          DEFAULT: 'hsl(216 14.3% 95.3%)',
          foreground: 'hsl(215 13.8% 34.9%)',
        },
        muted: {
          DEFAULT: 'hsl(216 14.3% 95.3%)',
          foreground: 'hsl(215.4 16.3% 46.9%)',
        },
      },
      borderRadius: {
        lg: '0.5rem',
        md: '0.375rem',
        sm: '0.25rem',
      },
    },
  },
  plugins: [],
}

export default config
