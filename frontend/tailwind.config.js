/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        charcoal: {
          950: "#0B0D0F",
          900: "#12151A",
          800: "#1A1E24",
          700: "#242830",
          600: "#333944",
        },
        amber: {
          400: "#F2B84B",
          500: "#E5A430",
          600: "#C8871E",
        },
      },
      fontFamily: {
        display: ["'Fraunces'", "serif"],
        body: ["'Inter'", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 40px rgba(229,164,48,0.12)",
      },
    },
  },
  plugins: [],
}
