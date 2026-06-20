import { AnimatePresence, motion } from 'framer-motion'

interface PremiumModalProps {
  open: boolean
  onClose: () => void
}

const FEATURES: { title: string; detail: string }[] = [
  {
    title: 'Full immersive editions',
    detail: 'Every chapter as a designed reading room, not just the opening.',
  },
  {
    title: 'Audio atmosphere',
    detail: 'Scored ambience that breathes with the text — rain, rooms, distance.',
  },
  {
    title: 'Symbol maps',
    detail: 'Trace a single image — a door, a clock — across an entire book.',
  },
  {
    title: 'Quote export',
    detail: 'Turn any saved line into a gallery-quality shareable image.',
  },
  {
    title: 'Deep reading notes',
    detail: 'Layered interpretation for readers who want to go further.',
  },
  {
    title: 'Cross-book themes',
    detail: 'Follow a motif as it travels between Kafka, Dostoevsky, Orwell.',
  },
]

export function PremiumModal({ open, onClose }: PremiumModalProps) {
  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            className="fixed inset-0 z-[60] bg-black/70 backdrop-blur-md"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
            onClick={onClose}
          />
          <div className="fixed inset-0 z-[70] flex items-center justify-center overflow-y-auto p-4">
            <motion.div
              className="relative my-auto w-full max-w-2xl overflow-hidden rounded-3xl"
              initial={{ opacity: 0, y: 30, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 20, scale: 0.98 }}
              transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
              style={{
                background:
                  'radial-gradient(120% 90% at 50% 0%, #1a1c1f 0%, #0c0d0f 60%, #08090a 100%)',
                border: '1px solid rgba(216,192,132,0.22)',
                boxShadow: '0 50px 120px -40px rgba(0,0,0,0.95)',
              }}
            >
              {/* gold light wash */}
              <div
                className="pointer-events-none absolute -top-24 left-1/2 h-64 w-[34rem] -translate-x-1/2 rounded-full opacity-40 blur-3xl"
                style={{ background: 'radial-gradient(circle, rgba(232,216,168,0.4), transparent 70%)' }}
              />

              <button
                onClick={onClose}
                className="absolute right-5 top-5 z-10 rounded-full border border-white/12 p-2.5 text-white/60 transition-colors hover:border-white/30 hover:text-white"
                aria-label="Close"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
                  <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </button>

              <div className="relative px-8 pb-9 pt-12 sm:px-12">
                <p className="eyebrow text-[#e8d8a8]/80">Membership</p>
                <h2 className="mt-3 font-display text-5xl font-medium text-white">
                  Luminous Plus
                </h2>
                <p className="mt-4 max-w-md font-reading text-lg leading-relaxed text-white/65">
                  The full museum. Every book becomes an atmosphere you can step
                  inside, return to, and carry with you.
                </p>

                <div className="mt-9 grid grid-cols-1 gap-x-8 gap-y-5 sm:grid-cols-2">
                  {FEATURES.map((f, i) => (
                    <motion.div
                      key={f.title}
                      className="flex gap-3"
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 0.15 + i * 0.07 }}
                    >
                      <svg
                        className="mt-0.5 shrink-0 text-[#e8d8a8]"
                        width="18"
                        height="18"
                        viewBox="0 0 18 18"
                        fill="none"
                        aria-hidden
                      >
                        <circle cx="9" cy="9" r="8" stroke="currentColor" strokeWidth="1" opacity="0.4" />
                        <path d="M5.5 9.2L8 11.5 12.5 6.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                      <div>
                        <p className="font-ui text-sm font-medium text-white">{f.title}</p>
                        <p className="font-ui text-xs leading-relaxed text-white/50">{f.detail}</p>
                      </div>
                    </motion.div>
                  ))}
                </div>

                <div className="mt-10 flex flex-col items-center gap-3 border-t border-white/8 pt-7 sm:flex-row sm:justify-between">
                  <div className="text-center sm:text-left">
                    <p className="font-display text-3xl text-white">
                      $7<span className="font-ui text-base text-white/50"> / month</span>
                    </p>
                    <p className="font-ui text-xs text-white/40">Cancel anytime · 14-day trial</p>
                  </div>
                  <div className="flex flex-col items-center gap-2">
                    <button
                      onClick={onClose}
                      className="inline-flex items-center justify-center rounded-full px-8 py-3.5 font-ui text-sm font-semibold text-ink-950 transition-transform duration-500 ease-luxe hover:scale-[1.03]"
                      style={{ background: 'linear-gradient(180deg, #f1e6c4, #d8c084)' }}
                    >
                      Begin your membership
                    </button>
                    <p className="font-ui text-[0.65rem] text-white/30">
                      Design prototype — no payment is processed.
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  )
}
