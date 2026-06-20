# Luminous Library

**Classic literature, transformed into immersive reading rooms.**

A design-forward MVP that reimagines public-domain classics not as e-books, but
as quiet, cinematic reading rooms. The text stays the center of the experience;
each section adds a subtle visual atmosphere — light, dust, a window's shadow, a
door — that supports the reading without ever competing with it.

> This is a frontend prototype. There is no backend, authentication, or payment.
> All data is local mock data. The reading text is **original, copyright-safe
> prose** written to evoke each work rather than reproduce it.

## Run it

```bash
npm install
npm run dev
```

Then open the printed local URL (default http://localhost:5173).

Other scripts:

```bash
npm run build     # type-check + production build
npm run preview   # preview the production build
npm run lint      # type-check only (tsc --noEmit)
```

## Stack

TypeScript · React 18 · Vite · Tailwind CSS · Framer Motion. No backend.

## What's implemented

- **Library / landing** — title, subtitle, three book cards each with a bespoke
  visual identity (Kafka cold green-grey & beetle/window motifs; Dostoevsky
  candlelight & snow; Orwell brutalist grid & surveillance eye). Only *The
  Metamorphosis* is playable; the others are marked **Coming soon**.
- **Reader** — large serif typography, page-like layout, smooth blurred page
  transitions, prev/next, a progress indicator, and the chapter title. Eight
  short reading sections.
- **Reading modes** — **Pure**, **Immersive**, and **Analysis** with an animated
  pill toggle.
- **Themes & type** — **Night / Sepia / Paper** theme swatches and four font-size
  steps.
- **Immersive atmosphere layer** — per-section CSS/SVG/Framer Motion moods:
  drifting dust, a swaying window-frame light, a ticking clock, a door
  silhouette with leaking light, faint bureaucratic stamps, and an abstract
  (non-cartoonish) beetle. A vignette + scrim guarantee the text always wins.
- **Analysis mode** — side panel (desktop) / bottom drawer (mobile) with *What is
  happening?*, *Key symbol*, *Character tension*, *No-spoiler interpretation*,
  and *One sentence to remember*, all per-section and spoiler-safe.
- **Quote saving** — a *Save quote* button per section, plus a *Saved Quotes*
  drawer of export-styled, share-ready quote cards (pre-seeded so it feels alive).
- **Afterglow** — a reflective end-of-chapter screen with an atmosphere summary,
  three reflection prompts, and a slowly lighting building as a progress object.
- **Luminous Plus** — a non-functional premium modal (full immersive editions,
  audio atmosphere, symbol maps, quote export, deep reading notes, cross-book
  themes). No payment is processed.

## Project structure

```
src/
  App.tsx                 # view state + shared drawers/modals
  main.tsx
  types.ts                # Book, Chapter, ReadingSection, AnalysisNote, SavedQuote, ...
  data/books.ts           # mock books + original reading text + analysis + seed quotes
  components/
    Library.tsx
    BookCard.tsx
    Reader.tsx
    Atmosphere.tsx
    AnalysisPanel.tsx
    QuoteDrawer.tsx
    Afterglow.tsx
    PremiumModal.tsx
  styles/index.css        # Tailwind + design primitives (glass, eyebrow, grain)
```

## What could be added later

- Real content for *Crime and Punishment* and *1984* (the data model already
  supports multiple chapters per book).
- Per-chapter progress persistence (localStorage) and a true "growing archive".
- Real quote-to-image export and audio atmosphere tracks.
- Keyboard navigation (←/→), touch-swipe paging, and reduced-motion handling.
- Routing for deep links into specific reading rooms.
