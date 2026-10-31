/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        cream: "#f7efe3",
        paper: "#fffaf2",
        ink: "#2b2420",
        teal: { 700: "#1f5f5b", 800: "#174744", 100: "#dfece6" },
        clay: { 700: "#9a4322", 500: "#c8693d", 100: "#f7e0d2" },
        sand: "#efe3d0",
        peach: "#fbe6d4",
        olive: { 700: "#556130", 100: "#ecefd9" },
        gold: "#d9a441",
        plum: { 700: "#6e3550", 100: "#f3e1e8" },
        slate: { 700: "#34586a", 100: "#e1eaef" },
        amber: { 800: "#7a4a06", 100: "#fdf0d5" },
      },
      fontFamily: {
        display: ['"Fraunces"', "Georgia", "serif"],
        sans: ['"Inter"', "ui-sans-serif", "system-ui", "-apple-system", '"Segoe UI"', "Roboto", "sans-serif"],
      },
      keyframes: {
        rise: { "0%": { opacity: "0", transform: "translateY(6px)" }, "100%": { opacity: "1", transform: "none" } },
      },
      animation: { rise: "rise .35s ease-out both" },
      boxShadow: {
        soft: "0 1px 2px rgba(43,36,32,.04), 0 8px 24px -12px rgba(43,36,32,.18)",
        lift: "0 2px 4px rgba(43,36,32,.05), 0 16px 32px -14px rgba(43,36,32,.28)",
      },
    },
  },
  plugins: [],
};
