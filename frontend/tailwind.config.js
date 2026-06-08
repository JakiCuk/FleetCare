/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Design tokens (DESIGN_SYSTEM §1)
        bg: '#f8fafc',
        surface: '#ffffff',
        border: '#e2e8f0',
        'border-soft': '#f1f5f9',
        text: '#0f172a',
        'text-muted': '#64748b',
        'text-faint': '#94a3b8',
        primary: '#2563eb',
        'primary-bg': '#eff6ff',
        sidebar: '#1a2332',
        // State colors (chips/badge)
        'state-green': '#16a34a',
        'state-green-bg': '#dcfce7',
        'state-yellow': '#d97706',
        'state-yellow-bg': '#fef3c7',
        'state-red': '#dc2626',
        'state-red-bg': '#fee2e2',
        'state-blue': '#2563eb',
        'state-blue-bg': '#dbeafe',
        'state-purple': '#7c3aed',
        'state-purple-bg': '#ede9fe',
        'state-orange': '#ea580c',
        'state-orange-bg': '#ffedd5',
        'state-gray': '#475569',
        'state-gray-bg': '#f1f5f9',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'monospace'],
      },
      borderRadius: {
        card: '10px',
      },
      maxWidth: {
        content: '1200px',
      },
      spacing: {
        sidebar: '168px',
      },
      boxShadow: {
        card: '0 1px 3px rgba(15, 23, 42, 0.04)',
        modal: '0 20px 50px rgba(15, 23, 42, 0.25)',
      },
    },
  },
  plugins: [],
};
