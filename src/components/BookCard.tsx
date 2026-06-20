import { motion } from 'framer-motion'
import type { Book } from '../types'

interface BookCardProps {
  book: Book
  index: number
  onOpen: (book: Book) => void
}

// Each book renders its own bespoke atmosphere on the card so the three
// identities read as distinct the instant the library loads.
function CardArt({ book }: { book: Book }) {
  if (book.id === 'metamorphosis') {
    return (
      <div className="absolute inset-0 overflow-hidden">
        <div
          className="absolute inset-0"
          style={{
            background:
              'radial-gradient(120% 90% at 70% 0%, #20302a 0%, #0c1411 55%, #070a09 100%)',
          }}
        />
        {/* cold window light */}
        <div
          className="absolute -right-10 -top-6 h-56 w-40 rotate-12 opacity-40 blur-[2px]"
          style={{
            background:
              'linear-gradient(180deg, rgba(169,196,180,0.5), rgba(169,196,180,0) 70%)',
            clipPath:
              'polygon(0 0,100% 0,100% 100%,0 100%)',
          }}
        />
        {/* window frame shadow */}
        <svg
          className="absolute right-6 top-6 opacity-25"
          width="120"
          height="150"
          viewBox="0 0 120 150"
          fill="none"
        >
          <rect x="1" y="1" width="118" height="148" stroke="#a9c4b4" strokeWidth="1.5" />
          <line x1="60" y1="0" x2="60" y2="150" stroke="#a9c4b4" strokeWidth="1.5" />
          <line x1="0" y1="75" x2="120" y2="75" stroke="#a9c4b4" strokeWidth="1.5" />
        </svg>
        {/* abstract beetle silhouette, geometric not cartoonish */}
        <svg
          className="absolute bottom-6 left-7 opacity-20"
          width="90"
          height="70"
          viewBox="0 0 90 70"
          fill="none"
        >
          <ellipse cx="45" cy="40" rx="20" ry="26" fill="#0b1410" stroke="#5f7a6b" strokeWidth="1" />
          <line x1="45" y1="14" x2="45" y2="66" stroke="#5f7a6b" strokeWidth="0.75" />
          <path d="M25 30 L8 18 M25 42 L6 42 M25 54 L9 66" stroke="#5f7a6b" strokeWidth="1" />
          <path d="M65 30 L82 18 M65 42 L84 42 M65 54 L81 66" stroke="#5f7a6b" strokeWidth="1" />
        </svg>
      </div>
    )
  }

  if (book.id === 'crime-and-punishment') {
    return (
      <div className="absolute inset-0 overflow-hidden">
        <div
          className="absolute inset-0"
          style={{
            background:
              'radial-gradient(110% 80% at 30% 20%, #2a1012 0%, #160a0c 55%, #0c0708 100%)',
          }}
        />
        {/* candle glow */}
        <div
          className="absolute left-10 top-10 h-40 w-40 rounded-full opacity-50 blur-2xl animate-pulseGlow"
          style={{ background: 'radial-gradient(circle, rgba(232,168,92,0.6), transparent 70%)' }}
        />
        {/* falling snow */}
        <svg className="absolute inset-0 opacity-40" width="100%" height="100%">
          {Array.from({ length: 26 }).map((_, i) => (
            <circle
              key={i}
              cx={`${(i * 37) % 100}%`}
              cy={`${(i * 53) % 100}%`}
              r={i % 3 === 0 ? 1.4 : 0.9}
              fill="#e7e2dc"
            />
          ))}
        </svg>
      </div>
    )
  }

  // 1984
  return (
    <div className="absolute inset-0 overflow-hidden">
      <div
        className="absolute inset-0"
        style={{
          background:
            'linear-gradient(160deg, #1a1c1f 0%, #101113 55%, #0a0b0c 100%)',
        }}
      />
      {/* brutalist concrete grid */}
      <svg className="absolute inset-0 opacity-15" width="100%" height="100%">
        <defs>
          <pattern id="grid" width="34" height="34" patternUnits="userSpaceOnUse">
            <path d="M34 0 L0 0 0 34" fill="none" stroke="#b7bcc2" strokeWidth="0.6" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>
      {/* surveillance eye */}
      <svg
        className="absolute right-8 top-10 opacity-50"
        width="110"
        height="70"
        viewBox="0 0 110 70"
        fill="none"
      >
        <ellipse cx="55" cy="35" rx="50" ry="26" stroke="#b7bcc2" strokeWidth="1.4" />
        <circle cx="55" cy="35" r="13" stroke="#c8302b" strokeWidth="2" />
        <circle cx="55" cy="35" r="4" fill="#c8302b" />
      </svg>
      {/* warning bar */}
      <div className="absolute bottom-0 left-0 h-1.5 w-full" style={{ background: '#c8302b' }} />
    </div>
  )
}

export function BookCard({ book, index, onOpen }: BookCardProps) {
  const available = book.status === 'available'

  return (
    <motion.button
      type="button"
      disabled={!available}
      onClick={() => onOpen(book)}
      initial={{ opacity: 0, y: 28 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, delay: 0.15 + index * 0.12, ease: [0.22, 1, 0.36, 1] }}
      whileHover={available ? { y: -8 } : undefined}
      className={`group relative flex h-[26rem] w-full flex-col overflow-hidden rounded-3xl text-left transition-shadow duration-700 ease-luxe ${
        available ? 'cursor-pointer' : 'cursor-not-allowed'
      }`}
      style={{
        boxShadow:
          '0 30px 80px -40px rgba(0,0,0,0.9), inset 0 1px 0 rgba(255,255,255,0.05)',
        border: '1px solid rgba(255,255,255,0.07)',
      }}
    >
      <CardArt book={book} />

      {/* readability scrim */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/25 to-transparent" />

      {/* hover lift glow */}
      <div
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-700 ease-luxe group-hover:opacity-100"
        style={{ boxShadow: `inset 0 0 120px ${book.palette.glow}` }}
      />

      <div className="relative z-10 mt-auto flex flex-col gap-3 p-7">
        <span className="eyebrow text-white/55">{book.palette.mood}</span>
        <h3 className="font-display text-3xl font-medium leading-tight text-white">
          {book.title}
        </h3>
        <p className="font-ui text-sm text-white/60">
          {book.author} · {book.year}
        </p>
        <p className="mt-1 max-w-[26ch] font-reading text-[0.95rem] leading-relaxed text-white/75">
          {book.tagline}
        </p>

        <div className="mt-3 flex items-center gap-3">
          {available ? (
            <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/5 px-4 py-2 font-ui text-xs font-medium text-white/90 transition-colors duration-500 group-hover:border-white/40 group-hover:bg-white/10">
              Enter reading room
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
                <path d="M2 7h10M8 3l4 4-4 4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </span>
          ) : (
            <span className="eyebrow rounded-full border border-white/15 px-4 py-2 text-white/50">
              Coming soon
            </span>
          )}
        </div>
      </div>
    </motion.button>
  )
}
