import { motion } from 'framer-motion'
import type { Book, Chapter } from '../types'

interface AfterglowProps {
  book: Book
  chapter: Chapter
  onReturn: () => void
  onReread: () => void
  onOpenPremium: () => void
}

// A slowly lighting building — the visual progress object.
// One window lights for the chapter just finished; the rest wait.
function LitBuilding() {
  const rows = 5
  const cols = 4
  const litCount = 6
  return (
    <svg width="180" height="220" viewBox="0 0 180 220" fill="none" aria-hidden>
      <defs>
        <linearGradient id="bld" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#121a16" />
          <stop offset="100%" stopColor="#080c0a" />
        </linearGradient>
      </defs>
      <rect x="30" y="20" width="120" height="190" rx="4" fill="url(#bld)" stroke="#2c3a33" strokeWidth="1.5" />
      {Array.from({ length: rows * cols }).map((_, i) => {
        const r = Math.floor(i / cols)
        const c = i % cols
        const x = 46 + c * 24
        const y = 36 + r * 34
        const lit = i < litCount
        return (
          <motion.rect
            key={i}
            x={x}
            y={y}
            width="16"
            height="22"
            rx="1.5"
            fill={lit ? '#e8d8a8' : '#16201b'}
            stroke="#2c3a33"
            strokeWidth="0.75"
            initial={{ opacity: lit ? 0 : 0.6 }}
            animate={{ opacity: lit ? [0, 1, 0.85] : 0.6 }}
            transition={{
              duration: 1.6,
              delay: lit ? 0.6 + i * 0.12 : 0,
              ease: 'easeOut',
            }}
            style={{ filter: lit ? 'drop-shadow(0 0 6px rgba(232,216,168,0.6))' : 'none' }}
          />
        )
      })}
    </svg>
  )
}

export function Afterglow({
  book,
  chapter,
  onReturn,
  onReread,
  onOpenPremium,
}: AfterglowProps) {
  return (
    <motion.div
      className="fixed inset-0 z-50 overflow-y-auto"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 1 }}
    >
      <div
        className="absolute inset-0"
        style={{
          background:
            'radial-gradient(120% 90% at 50% 10%, #14201b 0%, #0a0f0d 55%, #050706 100%)',
        }}
      />
      <div className="absolute inset-0 paper-grain opacity-[0.04]" />

      <div className="relative mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center px-6 py-20 text-center">
        <motion.p
          className="eyebrow text-kafka-cold/70"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          Afterglow
        </motion.p>

        <motion.h2
          className="mt-4 font-display text-5xl font-medium leading-tight text-white sm:text-6xl"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.32, ease: [0.22, 1, 0.36, 1] }}
        >
          {chapter.title}
        </motion.h2>

        <motion.div
          className="mt-10"
          initial={{ opacity: 0, scale: 0.94 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1.1, delay: 0.5, ease: [0.22, 1, 0.36, 1] }}
        >
          <LitBuilding />
          <p className="mt-3 font-ui text-[0.7rem] uppercase tracking-widest2 text-white/35">
            One room is lit. The library remembers.
          </p>
        </motion.div>

        <motion.p
          className="mt-10 max-w-xl text-balance font-reading text-lg leading-relaxed text-white/75"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.7 }}
        >
          {chapter.afterglow.atmosphere}
        </motion.p>

        <motion.div
          className="mt-12 w-full max-w-xl"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.95 }}
        >
          <p className="eyebrow mb-5 text-white/40">Sit with these</p>
          <div className="flex flex-col gap-4">
            {chapter.afterglow.prompts.map((prompt, i) => (
              <motion.div
                key={i}
                className="glass rounded-2xl px-6 py-5 text-left"
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 1.05 + i * 0.15 }}
              >
                <p className="font-reading text-[1.02rem] leading-relaxed text-white/85">
                  {prompt}
                </p>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div
          className="mt-14 flex flex-wrap items-center justify-center gap-4"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 1.6 }}
        >
          <button
            onClick={onReturn}
            className="inline-flex items-center justify-center rounded-full px-7 py-3 font-ui text-sm font-medium text-ink-950 transition-transform duration-500 ease-luxe hover:scale-[1.03]"
            style={{ background: 'linear-gradient(180deg, #f1e6c4, #d8c084)' }}
          >
            Return to Library
          </button>
          <button onClick={onReread} className="btn-ghost font-ui">
            Read again
          </button>
        </motion.div>

        <motion.button
          onClick={onOpenPremium}
          className="mt-8 font-ui text-xs text-white/40 underline-offset-4 transition-colors hover:text-white/70 hover:underline"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 1.9 }}
        >
          Unlock every reading room with Luminous Plus →
        </motion.button>

        <p className="mt-6 font-ui text-[0.7rem] text-white/25">{book.title}</p>
      </div>
    </motion.div>
  )
}
