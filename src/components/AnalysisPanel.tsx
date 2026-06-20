import { AnimatePresence, motion } from 'framer-motion'
import type { AnalysisNote } from '../types'

interface AnalysisPanelProps {
  open: boolean
  note: AnalysisNote
  scene?: string
}

interface FieldProps {
  label: string
  value: string
  index: number
  accent?: boolean
}

function Field({ label, value, index, accent }: FieldProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.05 * index, ease: [0.22, 1, 0.36, 1] }}
      className="border-t border-white/8 pt-5 first:border-t-0 first:pt-0"
    >
      <p className="eyebrow mb-2 text-white/40">{label}</p>
      <p
        className={`font-reading leading-relaxed ${
          accent
            ? 'text-[1.05rem] italic text-kafka-cold'
            : 'text-[0.96rem] text-white/80'
        }`}
      >
        {value}
      </p>
    </motion.div>
  )
}

export function AnalysisPanel({ open, note, scene }: AnalysisPanelProps) {
  return (
    <AnimatePresence>
      {open && (
        <motion.aside
          key="analysis"
          initial={{ opacity: 0, x: 40 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 40 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="glass-strong scroll-quiet pointer-events-auto fixed right-4 top-1/2 z-30 hidden max-h-[78vh] w-[22rem] -translate-y-1/2 overflow-y-auto rounded-3xl p-7 lg:block"
          style={{ boxShadow: '0 40px 100px -50px rgba(0,0,0,0.9)' }}
        >
          <div className="mb-6">
            <p className="eyebrow text-white/40">Reading notes</p>
            {scene && (
              <p className="mt-1 font-display text-2xl text-white">{scene}</p>
            )}
          </div>

          <div className="flex flex-col gap-5">
            <Field label="What is happening?" value={note.happening} index={0} />
            <Field label="Key symbol" value={note.keySymbol} index={1} />
            <Field label="Character tension" value={note.tension} index={2} />
            <Field label="No-spoiler interpretation" value={note.interpretation} index={3} />
            <Field label="One sentence to remember" value={note.remember} index={4} accent />
          </div>

          <p className="mt-7 border-t border-white/8 pt-5 font-ui text-[0.7rem] leading-relaxed text-white/30">
            Notes stay within the current section. Nothing here reveals what comes next.
          </p>
        </motion.aside>
      )}
    </AnimatePresence>
  )
}

// Compact bottom drawer used on smaller screens where the side panel is hidden.
export function AnalysisDrawerMobile({ open, note, scene }: AnalysisPanelProps) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          key="analysis-mobile"
          initial={{ opacity: 0, y: 60 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 60 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="glass-strong scroll-quiet fixed inset-x-3 bottom-24 z-30 max-h-[50vh] overflow-y-auto rounded-3xl p-6 lg:hidden"
        >
          <p className="eyebrow mb-4 text-white/40">Reading notes · {scene}</p>
          <div className="flex flex-col gap-4">
            <Field label="What is happening?" value={note.happening} index={0} />
            <Field label="Key symbol" value={note.keySymbol} index={1} />
            <Field label="Character tension" value={note.tension} index={2} />
            <Field label="No-spoiler interpretation" value={note.interpretation} index={3} />
            <Field label="One sentence to remember" value={note.remember} index={4} accent />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
