import { memo } from 'react'
import { motion } from 'framer-motion'
import type { AtmosphereKey } from '../types'

interface AtmosphereProps {
  variant: AtmosphereKey
  /** When false (Pure mode) the layer renders nothing. */
  active: boolean
}

// Floating dust particles, deterministic so they don't reflow on re-render.
function Dust({ count = 26 }: { count?: number }) {
  return (
    <div className="absolute inset-0 overflow-hidden">
      {Array.from({ length: count }).map((_, i) => {
        const left = (i * 53) % 100
        const size = (i % 4) + 1
        const delay = (i % 7) * 1.4
        const duration = 14 + (i % 6) * 3
        return (
          <motion.span
            key={i}
            className="absolute rounded-full bg-kafka-cold/40"
            style={{
              left: `${left}%`,
              bottom: '-10px',
              width: size,
              height: size,
            }}
            animate={{ y: [0, -420], opacity: [0, 0.5, 0] }}
            transition={{
              duration,
              delay,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        )
      })}
    </div>
  )
}

function WindowLight({ strong = false }: { strong?: boolean }) {
  return (
    <motion.div
      className="absolute inset-0"
      animate={{ opacity: strong ? [0.5, 0.75, 0.5] : [0.3, 0.5, 0.3] }}
      transition={{ duration: 16, repeat: Infinity, ease: 'easeInOut' }}
    >
      {/* projected window shape with mullions, slowly swaying */}
      <div className="absolute left-[8%] top-[6%] h-[78%] w-[34%] animate-sway">
        <div
          className="h-full w-full"
          style={{
            background:
              'linear-gradient(150deg, rgba(169,196,180,0.22), rgba(169,196,180,0.02) 70%)',
            clipPath: 'polygon(6% 0, 100% 4%, 94% 100%, 0 96%)',
          }}
        />
        <div className="absolute inset-0">
          <div className="absolute left-1/2 top-0 h-full w-px bg-kafka-cold/20" />
          <div className="absolute left-0 top-1/2 h-px w-full bg-kafka-cold/20" />
        </div>
      </div>
    </motion.div>
  )
}

const ClockTick = memo(function ClockTick() {
  return (
    <svg
      className="absolute right-[7%] top-[12%] h-28 w-28 opacity-[0.13]"
      viewBox="0 0 100 100"
      fill="none"
    >
      <circle cx="50" cy="50" r="46" stroke="#a9c4b4" strokeWidth="1" />
      {Array.from({ length: 12 }).map((_, i) => {
        const a = (i / 12) * Math.PI * 2
        return (
          <line
            key={i}
            x1={50 + Math.sin(a) * 40}
            y1={50 - Math.cos(a) * 40}
            x2={50 + Math.sin(a) * 44}
            y2={50 - Math.cos(a) * 44}
            stroke="#a9c4b4"
            strokeWidth="1"
          />
        )
      })}
      <motion.line
        x1="50"
        y1="50"
        x2="50"
        y2="18"
        stroke="#a9c4b4"
        strokeWidth="1.4"
        style={{ originX: '50px', originY: '50px' }}
        animate={{ rotate: 360 }}
        transition={{ duration: 60, repeat: Infinity, ease: 'linear' }}
      />
      <motion.line
        x1="50"
        y1="50"
        x2="50"
        y2="28"
        stroke="#a9c4b4"
        strokeWidth="2"
        style={{ originX: '50px', originY: '50px' }}
        animate={{ rotate: 360 }}
        transition={{ duration: 720, repeat: Infinity, ease: 'linear' }}
      />
    </svg>
  )
})

function DoorSilhouette() {
  return (
    <motion.div
      className="absolute bottom-0 right-[10%] h-[72%] w-[20%]"
      initial={{ opacity: 0 }}
      animate={{ opacity: 0.5 }}
      transition={{ duration: 2 }}
    >
      <div
        className="h-full w-full rounded-t-[6px]"
        style={{
          background:
            'linear-gradient(180deg, rgba(8,12,10,0.0), rgba(8,12,10,0.85))',
          boxShadow: 'inset 0 0 60px rgba(0,0,0,0.6)',
        }}
      />
      {/* light leaking under and around the door */}
      <div
        className="absolute -left-1 top-[10%] h-[80%] w-1 blur-[2px]"
        style={{ background: 'linear-gradient(180deg, rgba(169,196,180,0.5), transparent)' }}
      />
      <div
        className="absolute bottom-0 left-0 h-1.5 w-full blur-[2px]"
        style={{ background: 'rgba(232,216,168,0.4)' }}
      />
    </motion.div>
  )
}

// Faint bureaucratic stamps / file shapes drifting in the background.
function PaperBureaucracy() {
  return (
    <div className="absolute inset-0 overflow-hidden opacity-[0.09]">
      {[
        { top: '18%', left: '12%', r: -8 },
        { top: '62%', left: '70%', r: 6 },
        { top: '40%', left: '46%', r: -3 },
      ].map((p, i) => (
        <motion.div
          key={i}
          className="absolute"
          style={{ top: p.top, left: p.left }}
          animate={{ rotate: [p.r, p.r + 2, p.r], opacity: [0.6, 0.9, 0.6] }}
          transition={{ duration: 18 + i * 4, repeat: Infinity, ease: 'easeInOut' }}
        >
          <svg width="120" height="120" viewBox="0 0 120 120" fill="none">
            <rect x="14" y="14" width="92" height="92" rx="4" stroke="#a9c4b4" strokeWidth="2" />
            <rect x="26" y="26" width="68" height="68" rx="50%" stroke="#a9c4b4" strokeWidth="1" />
            <line x1="32" y1="60" x2="88" y2="60" stroke="#a9c4b4" strokeWidth="2" />
            <line x1="40" y1="48" x2="80" y2="48" stroke="#a9c4b4" strokeWidth="1" />
            <line x1="40" y1="72" x2="80" y2="72" stroke="#a9c4b4" strokeWidth="1" />
          </svg>
        </motion.div>
      ))}
    </div>
  )
}

function AbstractBeetle() {
  return (
    <motion.svg
      className="absolute bottom-[8%] left-1/2 h-48 w-48 -translate-x-1/2 opacity-[0.07]"
      viewBox="0 0 120 120"
      fill="none"
      animate={{ y: [0, -8, 0] }}
      transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut' }}
    >
      <ellipse cx="60" cy="62" rx="26" ry="36" fill="#0b1410" stroke="#5f7a6b" strokeWidth="1" />
      <line x1="60" y1="28" x2="60" y2="96" stroke="#5f7a6b" strokeWidth="0.75" />
      <path
        d="M34 44 L12 30 M34 62 L8 62 M34 80 L12 96"
        stroke="#5f7a6b"
        strokeWidth="1"
        strokeLinecap="round"
      />
      <path
        d="M86 44 L108 30 M86 62 L112 62 M86 80 L108 96"
        stroke="#5f7a6b"
        strokeWidth="1"
        strokeLinecap="round"
      />
      <circle cx="60" cy="24" r="9" fill="#0b1410" stroke="#5f7a6b" strokeWidth="1" />
    </motion.svg>
  )
}

const ColdGlow = ({ position = '60% 18%' }: { position?: string }) => (
  <div
    className="absolute inset-0"
    style={{
      background: `radial-gradient(70% 50% at ${position}, rgba(169,196,180,0.12), transparent 60%)`,
    }}
  />
)

export function Atmosphere({ variant, active }: AtmosphereProps) {
  if (!active) return null

  return (
    <motion.div
      key={variant}
      aria-hidden
      className="pointer-events-none absolute inset-0 overflow-hidden"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 1.4, ease: 'easeInOut' }}
    >
      {/* subtle paper texture present across all immersive scenes */}
      <div className="absolute inset-0 paper-grain opacity-[0.05]" />

      {variant === 'awakening' && (
        <>
          <ColdGlow position="50% 10%" />
          <Dust count={22} />
        </>
      )}

      {variant === 'ceiling' && (
        <>
          <ColdGlow position="50% 0%" />
          <ClockTick />
          <Dust count={14} />
        </>
      )}

      {variant === 'window' && (
        <>
          <WindowLight strong />
          <Dust count={18} />
        </>
      )}

      {variant === 'door' && (
        <>
          <ColdGlow position="80% 50%" />
          <DoorSilhouette />
          <Dust count={12} />
        </>
      )}

      {variant === 'office' && (
        <>
          <ColdGlow position="50% 20%" />
          <PaperBureaucracy />
          <ClockTick />
        </>
      )}

      {variant === 'threshold' && (
        <>
          <WindowLight />
          <DoorSilhouette />
          <ColdGlow position="40% 30%" />
        </>
      )}

      {variant === 'corridor' && (
        <>
          <ColdGlow position="30% 40%" />
          <AbstractBeetle />
          <Dust count={16} />
        </>
      )}

      {variant === 'dust' && (
        <>
          <WindowLight strong />
          <Dust count={34} />
          <div
            className="absolute inset-0"
            style={{
              background:
                'radial-gradient(50% 40% at 22% 60%, rgba(232,216,168,0.10), transparent 60%)',
            }}
          />
        </>
      )}

      {/* vignette to keep the reading column the brightest region */}
      <div
        className="absolute inset-0"
        style={{ boxShadow: 'inset 0 0 220px rgba(0,0,0,0.7)' }}
      />
    </motion.div>
  )
}
