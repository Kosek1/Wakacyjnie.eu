/**
 * Konfiguracja Tailwind CLI — 1:1 odzwierciedla to, co wcześniej było
 * wklejone jako `tailwind.config = {...}` w <head> każdej strony i
 * kompilowane w przeglądarce przez cdn.tailwindcss.com (wolne, bo
 * przeglądarka użytkownika musi to zrobić przy KAŻDYM wejściu na stronę).
 * Tailwind CLI robi to raz, na etapie builda na Netlify — wynik to jeden
 * mały, zminifikowany, gotowy plik CSS (assets/css/tailwind.css).
 *
 * `content` wskazuje WSZYSTKIE pliki HTML w repo, żeby wygenerowany CSS
 * zawierał klasy użyte gdziekolwiek na stronie (nie tylko w index.html) —
 * dzięki temu ten sam plik CSS można później podpiąć też pod pozostałe
 * podstrony i artykuły bez ponownego budowania.
 */
module.exports = {
  content: [
    "./*.html",
    "./artykuly/**/*.html",
    "./poradniki/**/*.html",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui"],
        display: ['"Plus Jakarta Sans"', "ui-sans-serif", "system-ui"],
      },
      colors: {
        ink: {
          950: "#141310",
          900: "#1c1a16",
          800: "#2a2722",
          700: "#3e3a32",
          600: "#5c5648",
          500: "#7a7364",
          400: "#a39c8c",
          300: "#c7c0b1",
          200: "#e2ddd0",
          100: "#efebe1",
          50: "#faf8f3",
        },
        accent: {
          50: "#fff4e9",
          100: "#ffe2c4",
          300: "#ffb570",
          500: "#e8752e",
          600: "#c85f1e",
          700: "#a14a17",
        },
        leaf: {
          500: "#3f6a52",
          600: "#345a44",
        },
        teal: {
          50: "#eaf7f6",
          100: "#cdeeec",
          500: "#4fb8b3",
          600: "#3b9a95",
        },
      },
      boxShadow: {
        soft: "0 1px 2px rgba(20,19,16,0.04), 0 12px 28px -8px rgba(20,19,16,0.10)",
        softer: "0 1px 1px rgba(20,19,16,0.03), 0 6px 16px -6px rgba(20,19,16,0.08)",
        lifted: "0 30px 70px -20px rgba(20,19,16,0.35)",
      },
      transitionTimingFunction: {
        out: "cubic-bezier(0.23, 1, 0.32, 1)",
        inout: "cubic-bezier(0.77, 0, 0.175, 1)",
      },
      borderRadius: {
        "4xl": "2rem",
      },
    },
  },
  plugins: [],
};
