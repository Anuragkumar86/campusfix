import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f1f4fe",
          100: "#e1e8fd",
          200: "#c9d5fb",
          300: "#a5b8f7",
          400: "#7c92f1",
          500: "#5b6fe8",
          600: "#4650db",
          700: "#3b40c0",
          800: "#33379a",
          900: "#2f337a",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgb(15 23 42 / 0.04), 0 1px 3px rgb(15 23 42 / 0.04)",
        lift: "0 4px 12px -2px rgb(15 23 42 / 0.08), 0 2px 4px -2px rgb(15 23 42 / 0.05)",
        pop: "0 24px 48px -12px rgb(15 23 42 / 0.28)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.96) translateY(4px)" },
          "100%": { opacity: "1", transform: "scale(1) translateY(0)" },
        },
        "slide-down": {
          "0%": { opacity: "0", transform: "translateY(-6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-up": "fade-up .35s cubic-bezier(.16,1,.3,1) both",
        "fade-in": "fade-in .2s ease-out both",
        "scale-in": "scale-in .2s cubic-bezier(.16,1,.3,1) both",
        "slide-down": "slide-down .2s ease-out both",
      },
    },
  },
  plugins: [],
};
export default config;