import { useCallback, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { BOOKS, SEED_QUOTES } from './data/books'
import type { Book, SavedQuote } from './types'
import { Library } from './components/Library'
import { Reader } from './components/Reader'
import { QuoteDrawer } from './components/QuoteDrawer'
import { PremiumModal } from './components/PremiumModal'

type View = 'library' | 'reader'

export default function App() {
  const [view, setView] = useState<View>('library')
  const [activeBook, setActiveBook] = useState<Book | null>(null)
  const [quotes, setQuotes] = useState<SavedQuote[]>(SEED_QUOTES)
  const [quotesOpen, setQuotesOpen] = useState(false)
  const [premiumOpen, setPremiumOpen] = useState(false)

  const openBook = useCallback((book: Book) => {
    if (book.status !== 'available') return
    setActiveBook(book)
    setView('reader')
  }, [])

  const returnToLibrary = useCallback(() => {
    setView('library')
    // Keep the book in memory briefly so the exit animation can play.
    window.setTimeout(() => setActiveBook(null), 600)
  }, [])

  const saveQuote = useCallback((quote: SavedQuote) => {
    setQuotes((prev) => {
      if (prev.some((q) => q.text === quote.text)) return prev
      return [quote, ...prev]
    })
  }, [])

  const removeQuote = useCallback((id: string) => {
    setQuotes((prev) => prev.filter((q) => q.id !== id))
  }, [])

  return (
    <div className="relative min-h-screen">
      <AnimatePresence mode="wait">
        {view === 'library' && (
          <motion.div
            key="library"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          >
            <Library
              books={BOOKS}
              onOpenBook={openBook}
              onOpenQuotes={() => setQuotesOpen(true)}
              onOpenPremium={() => setPremiumOpen(true)}
              savedCount={quotes.length}
            />
          </motion.div>
        )}

        {view === 'reader' && activeBook && (
          <motion.div
            key="reader"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          >
            <Reader
              book={activeBook}
              onReturn={returnToLibrary}
              onSaveQuote={saveQuote}
              onOpenQuotes={() => setQuotesOpen(true)}
              onOpenPremium={() => setPremiumOpen(true)}
              savedCount={quotes.length}
            />
          </motion.div>
        )}
      </AnimatePresence>

      <QuoteDrawer
        open={quotesOpen}
        quotes={quotes}
        onClose={() => setQuotesOpen(false)}
        onRemove={removeQuote}
        onOpenPremium={() => {
          setQuotesOpen(false)
          setPremiumOpen(true)
        }}
      />

      <PremiumModal open={premiumOpen} onClose={() => setPremiumOpen(false)} />
    </div>
  )
}
