import { motion } from 'framer-motion'
import type { Book } from '../types'
import { BookCard } from './BookCard'

interface LibraryProps {
  books: Book[]
  onOpenBook: (book: Book) => void
  onOpenQuotes: () => void
  onOpenPremium: () => void
  savedCount: number
}

export function Library({
  books,
  onOpenBook,
  onOpenQuotes,
  onOpenPremium,
  savedCount,
}: LibraryProps) {
  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Ambient backdrop: deep gradient + slow drifting light */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            'radial-gradient(120% 80% at 50% -10%, #14171a 0%, #0a0b0c 45%, #060708 100%)',
        }}
      />
      <div className="pointer-events-none absolute inset-0 paper-grain opacity-[0.04]" />
      <motion.div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-0 h-[60vh] w-[80vw] -translate-x-1/2 rounded-full blur-3xl"
        style={{ background: 'radial-gradient(circle, rgba(95,122,107,0.18), transparent 70%)' }}
        animate={{ opacity: [0.5, 0.8, 0.5] }}
        transition={{ duration: 12, repeat: Infinity, ease: 'easeInOut' }}
      />

      {/* Top bar */}
      <header className="relative z-10 mx-auto flex max-w-7xl items-center justify-between px-6 pt-8 sm:px-10">
        <div className="flex items-center gap-3">
          <div className="h-7 w-7 rounded-full" style={{ background: 'radial-gradient(circle at 35% 30%, #e8d8a8, #5f7a6b 60%, #0a0b0c)' }} />
          <span className="eyebrow text-white/70">Luminous Library</span>
        </div>
        <nav className="flex items-center gap-3">
          <button onClick={onOpenQuotes} className="btn-ghost font-ui">
            Saved Quotes
            {savedCount > 0 && (
              <span className="ml-2 rounded-full bg-white/10 px-2 py-0.5 text-xs text-white/80">
                {savedCount}
              </span>
            )}
          </button>
          <button
            onClick={onOpenPremium}
            className="inline-flex items-center justify-center rounded-full px-5 py-2.5 font-ui text-sm font-medium text-ink-950 transition-transform duration-500 ease-luxe hover:scale-[1.03]"
            style={{ background: 'linear-gradient(180deg, #f1e6c4, #d8c084)' }}
          >
            Luminous Plus
          </button>
        </nav>
      </header>

      {/* Hero */}
      <section className="relative z-10 mx-auto max-w-4xl px-6 pt-20 text-center sm:pt-28">
        <motion.p
          className="eyebrow mb-6 text-white/45"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
        >
          A reading room for the restless mind
        </motion.p>
        <motion.h1
          className="text-balance font-display text-6xl font-medium leading-[1.02] text-white sm:text-7xl"
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.08, ease: [0.22, 1, 0.36, 1] }}
        >
          Luminous Library
        </motion.h1>
        <motion.p
          className="mx-auto mt-7 max-w-xl text-balance font-reading text-lg leading-relaxed text-white/65"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.18, ease: [0.22, 1, 0.36, 1] }}
        >
          Classic literature, transformed into immersive reading rooms.
        </motion.p>
      </section>

      {/* Book grid */}
      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-28 pt-20 sm:px-10">
        <div className="grid grid-cols-1 gap-7 md:grid-cols-3">
          {books.map((book, i) => (
            <BookCard key={book.id} book={book} index={i} onOpen={onOpenBook} />
          ))}
        </div>

        <motion.p
          className="mx-auto mt-16 max-w-md text-center font-ui text-xs leading-relaxed text-white/35"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.7 }}
        >
          This is a design prototype. Reading text is original, copyright-safe prose
          written to evoke each work — not the published edition.
        </motion.p>
      </section>
    </div>
  )
}
