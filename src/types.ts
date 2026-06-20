// Core domain types for Luminous Library.
// These are intentionally expressive so additional books can be added
// later without reshaping the reading experience.

export type ReadingMode = 'pure' | 'immersive' | 'analysis'

export type Theme = 'night' | 'sepia' | 'paper'

/** Named atmosphere presets drive the Immersive visual layer. */
export type AtmosphereKey =
  | 'awakening'
  | 'ceiling'
  | 'window'
  | 'door'
  | 'office'
  | 'threshold'
  | 'corridor'
  | 'dust'

export interface AnalysisNote {
  /** "What is happening?" — a plain, present-tense orientation. */
  happening: string
  /** "Key symbol" — the single most resonant image in this section. */
  keySymbol: string
  /** "Character tension" — the emotional pressure between figures. */
  tension: string
  /** "No-spoiler interpretation" — meaning, without revealing what comes next. */
  interpretation: string
  /** "One sentence to remember" — a distilled line to carry forward. */
  remember: string
}

export interface ReadingSection {
  id: string
  /** Optional small heading shown above the section, e.g. a scene label. */
  scene?: string
  /** Paragraphs of reading text. Each is a string. */
  paragraphs: string[]
  /** A single highlighted line offered for quote-saving. */
  pullQuote: string
  /** Mood preset for the immersive background. */
  atmosphere: AtmosphereKey
  /** Analysis content surfaced in Analysis mode. */
  analysis: AnalysisNote
}

export interface Chapter {
  id: string
  title: string
  sections: ReadingSection[]
  /** Reflective summary shown on the Afterglow screen. */
  afterglow: {
    atmosphere: string
    prompts: string[]
  }
}

export type BookStatus = 'available' | 'coming-soon'

export interface BookPalette {
  /** Tailwind-ready CSS color strings used to paint the card identity. */
  base: string
  accent: string
  glow: string
  /** A short atmosphere descriptor shown on the card. */
  mood: string
}

export interface Book {
  id: string
  title: string
  author: string
  year: string
  /** One-line invitation shown on the card. */
  tagline: string
  status: BookStatus
  palette: BookPalette
  chapters: Chapter[]
}

export interface SavedQuote {
  id: string
  text: string
  bookTitle: string
  author: string
  /** Section scene label or chapter title for provenance. */
  source: string
  savedAt: number
}
