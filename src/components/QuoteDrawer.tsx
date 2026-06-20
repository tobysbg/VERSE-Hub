import { AnimatePresence, motion } from 'framer-motion'
import type { SavedQuote } from '../types'

interface QuoteDrawerProps {
  open: boolean
  quotes: SavedQuote[]
  onClose: () => void
  onRemove: (id: string) => void
  onOpenPremium: () => void
}

function timeAgo(ts: number): string {
  const mins = Math.round((Date.now() - ts) / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins} min ago`
  const hrs = Math.round(mins / 60)
  if (hrs < 24) return `${hrs} hr ago`
  const days = Math.round(hrs / 24)
  return `${days} day${days > 1 ? 's' : ''} ago`
}

// Export-styled card — composed to look like it could become a shareable image.
function QuoteCard({
  quote,
  index,
  onRemove,
}: {
  quote: SavedQuote
  index: number
  onRemove: (id: string) => void
}) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: 40 }}
      transition={{ duration: 0.5, delay: index * 0.05, ease: [0.22, 1, 0.36, 1] }}
      className="group relative overflow-hidden rounded-2xl p-6"
      style={{
        background:
          'linear-gradient(155deg, rgba(31,40,35,0.9) 0%, rgba(12,16,14,0.96) 100%)',
        border: '1px solid rgba(169,196,180,0.18)',
        boxShadow: '0 24px 60px -40px rgba(0,0,0,0.9)',
      }}
    >
      {/* faint corner glow, like a museum print */}
      <div
        className="pointer-events-none absolute -right-10 -top-10 h-32 w-32 rounded-full opacity-40 blur-2xl"
        style={{ background: 'radial-gradient(circle, rgba(232,216,168,0.4), transparent 70%)' }}
      />
      <svg className="mb-4 opacity-30" width="26" height="20" viewBox="0 0 26 20" fill="none">
        <path
          d="M10 0C4 2 0 7 0 13c0 4 2 7 6 7 3 0 5-2 5-5s-2-5-5-5c-1 0-1 0-2 1 1-4 3-7 7-9L10 0zm15 0c-6 2-10 7-10 13 0 4 2 7 6 7 3 0 5-2 5-5s-2-5-5-5c-1 0-1 0-2 1 1-4 3-7 7-9L25 0z"
          fill="#a9c4b4"
        />
      </svg>

      <p className="font-display text-xl italic leading-snug text-white">{quote.text}</p>

      <div className="mt-5 flex items-end justify-between">
        <div>
          <p className="font-ui text-sm font-medium text-white/80">{quote.author}</p>
          <p className="font-ui text-xs text-white/45">
            {quote.bookTitle} · {quote.source}
          </p>
          <p className="mt-1 font-ui text-[0.65rem] uppercase tracking-widest2 text-white/30">
            Saved {timeAgo(quote.savedAt)}
          </p>
        </div>
        <button
          onClick={() => onRemove(quote.id)}
          className="rounded-full p-2 text-white/30 opacity-0 transition-all duration-300 hover:bg-white/5 hover:text-white/70 group-hover:opacity-100"
          aria-label="Remove quote"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
            <path d="M2 4h10M5 4V2.5h4V4M3.5 4l.5 8h6l.5-8" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>

      {/* watermark, reinforcing the "export" feel */}
      <p className="mt-4 border-t border-white/8 pt-3 font-ui text-[0.6rem] uppercase tracking-widest2 text-white/25">
        Luminous Library
      </p>
    </motion.div>
  )
}

export function QuoteDrawer({
  open,
  quotes,
  onClose,
  onRemove,
  onOpenPremium,
}: QuoteDrawerProps) {
  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
            onClick={onClose}
          />
          <motion.aside
            className="glass-strong scroll-quiet fixed right-0 top-0 z-50 flex h-full w-full max-w-md flex-col overflow-y-auto"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="flex items-center justify-between px-7 pb-4 pt-8">
              <div>
                <p className="eyebrow text-white/40">Your collection</p>
                <h2 className="mt-1 font-display text-3xl text-white">Saved Quotes</h2>
              </div>
              <button
                onClick={onClose}
                className="rounded-full border border-white/12 p-2.5 text-white/60 transition-colors hover:border-white/30 hover:text-white"
                aria-label="Close"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
                  <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </button>
            </div>

            <div className="flex flex-1 flex-col gap-4 px-7 pb-6">
              <AnimatePresence initial={false}>
                {quotes.length === 0 ? (
                  <motion.p
                    key="empty"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="mt-16 text-center font-reading text-white/45"
                  >
                    No quotes yet. While reading, tap{' '}
                    <span className="text-white/70">Save quote</span> to keep a line here.
                  </motion.p>
                ) : (
                  quotes.map((q, i) => (
                    <QuoteCard key={q.id} quote={q} index={i} onRemove={onRemove} />
                  ))
                )}
              </AnimatePresence>
            </div>

            <div className="border-t border-white/8 px-7 py-5">
              <button
                onClick={onOpenPremium}
                className="flex w-full items-center justify-between rounded-2xl border border-[#d8c084]/30 bg-[#d8c084]/5 px-5 py-4 text-left transition-colors hover:bg-[#d8c084]/10"
              >
                <span>
                  <span className="block font-ui text-sm font-medium text-[#e8d8a8]">
                    Export quotes as images
                  </span>
                  <span className="block font-ui text-xs text-white/45">
                    Available with Luminous Plus
                  </span>
                </span>
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden className="text-[#e8d8a8]">
                  <path d="M6 4l5 5-5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}
