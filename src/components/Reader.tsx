import { useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import type { Book, ReadingMode, SavedQuote, Theme } from '../types'
import { Atmosphere } from './Atmosphere'
import { AnalysisPanel, AnalysisDrawerMobile } from './AnalysisPanel'
import { Afterglow } from './Afterglow'

interface ReaderProps {
  book: Book
  onReturn: () => void
  onSaveQuote: (quote: SavedQuote) => void
  onOpenQuotes: () => void
  onOpenPremium: () => void
  savedCount: number
}

const THEMES: Record<
  Theme,
  { page: string; text: string; muted: string; columnDark: boolean }
> = {
  night: {
    page: 'radial-gradient(130% 90% at 50% 0%, #14171a 0%, #0a0b0c 50%, #060708 100%)',
    text: 'rgba(236,234,228,0.92)',
    muted: 'rgba(236,234,228,0.5)',
    columnDark: true,
  },
  sepia: {
    page: 'radial-gradient(130% 90% at 50% 0%, #241c12 0%, #1a140d 55%, #120d08 100%)',
    text: 'rgba(240,225,196,0.94)',
    muted: 'rgba(240,225,196,0.55)',
    columnDark: true,
  },
  paper: {
    page: 'radial-gradient(130% 90% at 50% 0%, #f0ece2 0%, #e6e1d6 60%, #ddd7ca 100%)',
    text: 'rgba(26,21,15,0.9)',
    muted: 'rgba(26,21,15,0.55)',
    columnDark: false,
  },
}

const FONT_STEPS = [1, 1.12, 1.26, 1.42]

function ModeToggle({
  mode,
  onChange,
}: {
  mode: ReadingMode
  onChange: (m: ReadingMode) => void
}) {
  const options: { key: ReadingMode; label: string }[] = [
    { key: 'pure', label: 'Pure' },
    { key: 'immersive', label: 'Immersive' },
    { key: 'analysis', label: 'Analysis' },
  ]
  return (
    <div className="relative flex items-center rounded-full border border-white/12 bg-black/30 p-1 backdrop-blur">
      {options.map((o) => {
        const active = mode === o.key
        return (
          <button
            key={o.key}
            onClick={() => onChange(o.key)}
            className="relative z-10 rounded-full px-4 py-1.5 font-ui text-xs font-medium transition-colors duration-300"
            style={{ color: active ? '#0a0b0c' : 'rgba(255,255,255,0.7)' }}
          >
            {active && (
              <motion.span
                layoutId="mode-pill"
                className="absolute inset-0 -z-10 rounded-full"
                style={{ background: 'linear-gradient(180deg,#f1e6c4,#d8c084)' }}
                transition={{ type: 'spring', stiffness: 380, damping: 32 }}
              />
            )}
            {o.label}
          </button>
        )
      })}
    </div>
  )
}

export function Reader({
  book,
  onReturn,
  onSaveQuote,
  onOpenQuotes,
  onOpenPremium,
  savedCount,
}: ReaderProps) {
  const chapter = book.chapters[0]
  const sections = chapter.sections

  const [index, setIndex] = useState(0)
  const [direction, setDirection] = useState(1)
  const [mode, setMode] = useState<ReadingMode>('immersive')
  const [theme, setTheme] = useState<Theme>('night')
  const [fontStep, setFontStep] = useState(1)
  const [afterglow, setAfterglow] = useState(false)
  const [justSaved, setJustSaved] = useState(false)

  const section = sections[index]
  const t = THEMES[theme]
  const fontScale = FONT_STEPS[fontStep]

  const immersive = mode === 'immersive'
  const analysisOpen = mode === 'analysis'

  // In immersive mode the canvas is always dark so atmosphere reads correctly.
  const pageBackground = immersive
    ? 'radial-gradient(130% 90% at 50% 0%, #0e1714 0%, #0a0f0d 55%, #060708 100%)'
    : t.page
  const textColor = immersive ? 'rgba(236,238,233,0.94)' : t.text
  const mutedColor = immersive ? 'rgba(236,238,233,0.55)' : t.muted

  const progress = ((index + 1) / sections.length) * 100

  const goNext = () => {
    if (index < sections.length - 1) {
      setDirection(1)
      setIndex((i) => i + 1)
    } else {
      setAfterglow(true)
    }
  }

  const goPrev = () => {
    if (index > 0) {
      setDirection(-1)
      setIndex((i) => i - 1)
    }
  }

  const handleSave = () => {
    onSaveQuote({
      id: `${book.id}-${section.id}-${Date.now()}`,
      text: section.pullQuote,
      bookTitle: book.title,
      author: book.author,
      source: section.scene ?? chapter.title,
      savedAt: Date.now(),
    })
    setJustSaved(true)
    window.setTimeout(() => setJustSaved(false), 1800)
  }

  const variants = useMemo(
    () => ({
      enter: (dir: number) => ({ opacity: 0, x: dir > 0 ? 60 : -60, filter: 'blur(6px)' }),
      center: { opacity: 1, x: 0, filter: 'blur(0px)' },
      exit: (dir: number) => ({ opacity: 0, x: dir > 0 ? -60 : 60, filter: 'blur(6px)' }),
    }),
    [],
  )

  return (
    <div className="relative min-h-screen w-full overflow-hidden">
      {/* Page surface */}
      <motion.div
        className="absolute inset-0"
        animate={{ background: pageBackground }}
        transition={{ duration: 1.2, ease: 'easeInOut' }}
        style={{ background: pageBackground }}
      />

      {/* Immersive atmosphere */}
      <AnimatePresence mode="wait">
        <Atmosphere key={section.atmosphere} variant={section.atmosphere} active={immersive} />
      </AnimatePresence>

      {/* Top bar */}
      <header className="relative z-20 mx-auto flex max-w-6xl items-center justify-between px-5 pt-6 sm:px-8">
        <button
          onClick={onReturn}
          className="inline-flex items-center gap-2 font-ui text-sm transition-opacity duration-300 hover:opacity-100"
          style={{ color: mutedColor }}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
            <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Library
        </button>

        <div className="text-center">
          <p className="eyebrow" style={{ color: mutedColor }}>
            {book.author}
          </p>
          <p className="font-display text-lg leading-tight" style={{ color: textColor }}>
            {chapter.title}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onOpenQuotes}
            className="relative rounded-full border border-white/12 p-2.5 transition-colors duration-300 hover:border-white/30"
            style={{ color: mutedColor }}
            aria-label="Saved quotes"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
              <path d="M4 2h8v12l-4-2.5L4 14V2z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
            </svg>
            {savedCount > 0 && (
              <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-[#d8c084] text-[10px] font-semibold text-ink-950">
                {savedCount}
              </span>
            )}
          </button>
        </div>
      </header>

      {/* Reading column */}
      <main className="relative z-10 mx-auto flex min-h-[calc(100vh-9rem)] max-w-3xl flex-col justify-center px-6 py-10 sm:px-8">
        <AnimatePresence mode="wait" custom={direction}>
          <motion.article
            key={section.id}
            custom={direction}
            variants={variants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            className="relative"
          >
            {/* readability scrim only in immersive mode */}
            {immersive && (
              <div
                className="absolute -inset-x-8 -inset-y-10 -z-10 rounded-[2rem]"
                style={{
                  background:
                    'radial-gradient(80% 70% at 50% 50%, rgba(6,8,7,0.72), rgba(6,8,7,0) 80%)',
                }}
              />
            )}

            {section.scene && (
              <motion.p
                className="eyebrow mb-6"
                style={{ color: immersive ? 'rgba(169,196,180,0.8)' : mutedColor }}
              >
                {section.scene}
              </motion.p>
            )}

            <div
              className="font-reading"
              style={{
                color: textColor,
                fontSize: `${1.22 * fontScale}rem`,
                lineHeight: 1.85,
              }}
            >
              {section.paragraphs.map((p, i) => (
                <p key={i} className="mb-6 last:mb-0">
                  {p}
                </p>
              ))}
            </div>

            {/* Pull quote + save */}
            <div
              className="mt-10 border-l-2 pl-5"
              style={{ borderColor: immersive ? 'rgba(169,196,180,0.5)' : mutedColor }}
            >
              <p
                className="font-display text-xl italic leading-snug"
                style={{ color: textColor }}
              >
                “{section.pullQuote}”
              </p>
              <button
                onClick={handleSave}
                className="mt-4 inline-flex items-center gap-2 rounded-full border px-4 py-2 font-ui text-xs font-medium transition-all duration-400 ease-luxe"
                style={{
                  color: justSaved ? '#0a0b0c' : textColor,
                  borderColor: justSaved ? 'transparent' : 'rgba(255,255,255,0.18)',
                  background: justSaved ? 'linear-gradient(180deg,#f1e6c4,#d8c084)' : 'transparent',
                }}
              >
                {justSaved ? (
                  <>
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
                      <path d="M2 7.5L5.5 11 12 3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    Saved to your quotes
                  </>
                ) : (
                  <>
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
                      <path d="M3.5 2h7v10l-3.5-2.2L3.5 12V2z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
                    </svg>
                    Save quote
                  </>
                )}
              </button>
            </div>
          </motion.article>
        </AnimatePresence>
      </main>

      {/* Bottom control bar */}
      <div className="fixed inset-x-0 bottom-0 z-30 px-4 pb-5">
        <div className="mx-auto flex max-w-3xl flex-col gap-3">
          {/* progress */}
          <div className="flex items-center gap-3 px-1">
            <span className="font-ui text-[0.7rem] tabular-nums" style={{ color: mutedColor }}>
              {String(index + 1).padStart(2, '0')}
            </span>
            <div className="h-px flex-1 overflow-hidden rounded-full bg-white/10">
              <motion.div
                className="h-full rounded-full"
                style={{ background: 'linear-gradient(90deg,#5f7a6b,#e8d8a8)' }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              />
            </div>
            <span className="font-ui text-[0.7rem] tabular-nums" style={{ color: mutedColor }}>
              {String(sections.length).padStart(2, '0')}
            </span>
          </div>

          <div className="glass flex flex-wrap items-center justify-between gap-3 rounded-2xl px-3 py-2.5">
            <button
              onClick={goPrev}
              disabled={index === 0}
              className="rounded-full p-2 transition-opacity duration-300 disabled:opacity-25"
              style={{ color: textColor }}
              aria-label="Previous section"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden>
                <path d="M11 4L6 9l5 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>

            <ModeToggle mode={mode} onChange={setMode} />

            {/* theme + font controls */}
            <div className="flex items-center gap-2">
              <div className="flex items-center rounded-full border border-white/12 bg-black/20 p-1">
                {(['night', 'sepia', 'paper'] as Theme[]).map((th) => (
                  <button
                    key={th}
                    onClick={() => setTheme(th)}
                    className="h-6 w-6 rounded-full transition-transform duration-300 hover:scale-110"
                    aria-label={`${th} theme`}
                    style={{
                      background:
                        th === 'night'
                          ? '#0a0b0c'
                          : th === 'sepia'
                            ? '#c9a86a'
                            : '#ece7dc',
                      outline: theme === th ? '2px solid #d8c084' : '1px solid rgba(255,255,255,0.15)',
                      outlineOffset: '1px',
                    }}
                  />
                ))}
              </div>

              <div className="flex items-center rounded-full border border-white/12 bg-black/20">
                <button
                  onClick={() => setFontStep((s) => Math.max(0, s - 1))}
                  disabled={fontStep === 0}
                  className="px-2.5 py-1 font-reading text-xs transition-opacity disabled:opacity-30"
                  style={{ color: textColor }}
                  aria-label="Decrease font size"
                >
                  A
                </button>
                <button
                  onClick={() => setFontStep((s) => Math.min(FONT_STEPS.length - 1, s + 1))}
                  disabled={fontStep === FONT_STEPS.length - 1}
                  className="px-2.5 py-1 font-reading text-base transition-opacity disabled:opacity-30"
                  style={{ color: textColor }}
                  aria-label="Increase font size"
                >
                  A
                </button>
              </div>
            </div>

            <button
              onClick={goNext}
              className="rounded-full p-2 transition-transform duration-300 hover:translate-x-0.5"
              style={{ color: textColor }}
              aria-label="Next section"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden>
                <path d="M7 4l5 5-5 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Analysis surfaces */}
      <AnalysisPanel open={analysisOpen} note={section.analysis} scene={section.scene} />
      <AnalysisDrawerMobile open={analysisOpen} note={section.analysis} scene={section.scene} />

      {/* Afterglow overlay */}
      <AnimatePresence>
        {afterglow && (
          <Afterglow
            book={book}
            chapter={chapter}
            onReturn={onReturn}
            onReread={() => {
              setAfterglow(false)
              setDirection(-1)
              setIndex(0)
            }}
            onOpenPremium={onOpenPremium}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
