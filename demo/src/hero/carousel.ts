// The hero's part-glyph carousel. The <figure>'s <li>s (⻍ 糹 厶 北 山 言 青 …) are
// the data; this reads them and breathes one at a time on a fixed, centred stage —
// random order, 60–90s each WITH a 5–10s dead-still hold mid-cycle. Weight settles
// once (a quick 3–5s morph, then holds); drift + scale run very slowly and are barely
// perceptible; entrance/exit are pure opacity (+ optional blur), never scaling the
// glyph. 安靜不打擾: it pauses in a hidden tab, and prefers-reduced-motion collapses
// it to a motionless crossfade.

const TAU = Math.PI * 2
const rand = (lo: number, hi: number): number => lo + Math.random() * (hi - lo)
const clamp01 = (x: number): number => (x < 0 ? 0 : x > 1 ? 1 : x)
// Baseline-everywhere smoothstep — eased 0→1 ramp between edges a..b
const smoothstep = (a: number, b: number, x: number): number => {
  const t = clamp01((x - a) / (b - a))
  return t * t * (3 - 2 * t)
}

// --- cycle shape -----------------------------------------------------------
// Each channel (opacity / blur / drift / scale / weight) picks its OWN mode + in/out
// fractions per cycle in makeSeed — so nothing moves in lockstep and no two cycles
// read the same (weight may hold/breathe/ramp; each scale axis may be off/held/pulsing).

// A few non-synced sine waves whose periods don't share a common multiple, so the
// summed drift never visibly repeats. Phases/amplitudes re-randomise every cycle.
type Layer = {
  ax: number
  ay: number
  fx: number
  fy: number
  px: number
  py: number
}

// scale: per-axis, chosen per cycle — off / a held squash / an oscillation
type ScaleChan = {
  mode: 'none' | 'static' | 'osc'
  base: number // held scale for 'static' (1 = none)
  amp: number
  freq: number
  phase: number
}
// how each end enters/leaves: a blur dissolve or a plain opacity fade. No scale and
// no movement are coupled to the transition — the entrance never squashes the glyph.
type TransMode = 'blur' | 'fade'

type Seed = {
  duration: number
  font: string
  baseX: number // per-cycle horizontal bias in vw (−left … +right), may overrun the edges
  baseY: number // per-cycle vertical bias as a fraction of --hero-stage-h (0 = centre)
  accent: boolean
  // each scale axis is an independent channel (off / held squash / oscillation)
  sx: ScaleChan
  sy: ScaleChan
  layers: readonly Layer[]
  // weight settles ONCE, smoothly and early: from→to over weightDur (3–5s), then holds
  weightFrom: number
  weightTo: number
  weightDelay: number // ms before the settle starts
  weightDur: number // ms the settle takes (kept short so it finishes fast)
  blurInDist: number // px the glyph emerges from (per cycle)
  blurOutDist: number // px it dissolves into (per cycle)
  breatheAmp: number
  breatheFreq: number
  breathePhase: number
  // shadow: usually a soft halo trailing the drift; occasionally a crisp echo (blur 0)
  // whose offset slowly slides on its own oscillation
  hardShadow: boolean
  shBaseX: number
  shBaseY: number
  shAmpX: number
  shAmpY: number
  shFreqX: number
  shFreqY: number
  shPhaseX: number
  shPhaseY: number
  // entrance / exit: each end picks its own mode (blur / fade); envelope timing desynced
  enterMode: TransMode
  exitMode: TransMode
  enterFrac: number // entrance occupies the first enterFrac of the cycle
  exitFrac: number // exit runs from exitFrac → 1
  holdStart: number // ms — the oscillation clock freezes here…
  holdDur: number // …for this long (a dead-still pause mid-cycle)
}

const makeLayer = (
  axHi: number,
  ayHi: number,
  fLo: number,
  fHi: number,
): Layer => ({
  ax: rand(axHi * 0.4, axHi),
  ay: rand(ayHi * 0.4, ayHi),
  fx: rand(fLo, fHi),
  fy: rand(fLo, fHi),
  px: rand(0, TAU),
  py: rand(0, TAU),
})

// per axis: ~32% none, ~20% a held squash/stretch (a constant, no change), ~48% a
// breath — slow but visible: ~1–2 fat↔thin swings over a cycle (period ~40–85s).
const makeScaleChan = (): ScaleChan => {
  const r = Math.random()
  if (r < 0.32) return { mode: 'none', base: 1, amp: 0, freq: 0, phase: 0 }
  if (r < 0.52) return { mode: 'static', base: 1 + rand(-0.14, 0.2), amp: 0, freq: 0, phase: 0 }
  return { mode: 'osc', base: 1, amp: rand(0.07, 0.16), freq: rand(0.012, 0.025), phase: rand(0, TAU) }
}

// each end: ~60% blur dissolve, ~40% plain opacity fade
const pickTransMode = (): TransMode => (Math.random() < 0.6 ? 'blur' : 'fade')

const makeSeed = (): Seed => {
  const duration = rand(60_000, 90_000)
  // Exit window in REAL seconds so the dissolve always takes ≥6s however long the cycle
  // runs (longer cycles just hold in the centre longer before leaving).
  const exitSecs = rand(6_000, 10_000)
  // horizontal placement: mostly right (clear of the figcaption + its red block on the
  // left), occasionally centred, and only ~15% to the left — and that left is kept gentle
  // so it avoids the far-left figcaption columns.
  const place = Math.random()
  const leftPlaced = place < 0.15
  const baseX = leftPlaced ? rand(-16, -4) : place < 0.35 ? rand(-7, 7) : rand(10, 34)
  // vertical placement: default is centre-low; only ~30% of cycles ride higher than
  // the middle. The glyph's ink already ~fills the stage, so the low bias is kept
  // small (≤0.12) — #why's background starts right below the stage and the figure's
  // overflow:clip would guillotine anything pushed further down.
  const baseY = Math.random() < 0.7 ? rand(0.05, 0.12) : rand(-0.15, -0.05)
  const enterFrac = rand(0.1, 0.22)
  const exitFrac = 1 - exitSecs / duration
  // a dead-still hold, placed wholly inside the visible plateau (after entrance,
  // before exit) with 1s margins so the freeze never overlaps a transition.
  const holdDur = rand(5_000, 10_000)
  const pStart = enterFrac * duration + 1_000
  const pEnd = exitFrac * duration - 1_000
  const holdStart = pStart + Math.random() * Math.max(0, pEnd - pStart - holdDur)
  // mostly the heritage serif; occasionally the default sans. Only serif cycles may
  // carry the crisp echo — the sans always gets the soft blur shadow.
  const font = Math.random() < 0.2 ? 'var(--font-default)' : 'var(--font-alternative)'
  const isSerif = font === 'var(--font-alternative)'
  return {
    duration,
    font,
    baseX,
    baseY,
    // left-placed glyphs (over the figcaption's red block) are mostly accent-coloured;
    // elsewhere an accent glyph is just an occasional touch
    accent: leftPlaced ? Math.random() < 0.75 : Math.random() < 0.15,
    // each axis decides independently → some cycles don't scale, some squash one way,
    // some pulse both axes out of sync
    sx: makeScaleChan(),
    sy: makeScaleChan(),
    // mostly-horizontal drift on top of baseX: coarse sway, mid wander, faint tremor.
    // Vertical amplitudes are tiny — the glyph fills the height, so it must not slide up
    // or down enough to crop. Frequencies are very low → the slide is near-imperceptible.
    layers: [
      makeLayer(30, 5, 0.0015, 0.005),
      makeLayer(16, 4, 0.004, 0.009),
      makeLayer(7, 2, 0.008, 0.015),
    ].slice(0, Math.random() < 0.6 ? 3 : 2),
    // weight settles once, quickly, then holds steady — done within ~3–5s of the start
    weightFrom: rand(300, 760),
    weightTo: rand(260, 880),
    weightDelay: rand(200, 800),
    weightDur: rand(2_800, 4_200),
    // emerge/dissolve depth varies; blur-breathing is off entirely ~30% of cycles
    blurInDist: rand(60, 115),
    blurOutDist: rand(85, 120),
    breatheAmp: Math.random() < 0.3 ? 0 : rand(0.6, 2.2),
    breatheFreq: rand(0.008, 0.028),
    breathePhase: rand(0, TAU),
    // a crisp (blur-0) echo with a slowly sliding offset — serif only, ~25% of its cycles
    hardShadow: isSerif && Math.random() < 0.25,
    shBaseX: rand(-8, 12),
    shBaseY: rand(-8, 12),
    shAmpX: rand(6, 18),
    shAmpY: rand(6, 18),
    shFreqX: rand(0.02, 0.06),
    shFreqY: rand(0.02, 0.06),
    shPhaseX: rand(0, TAU),
    shPhaseY: rand(0, TAU),
    enterMode: pickTransMode(),
    exitMode: pickTransMode(),
    enterFrac,
    exitFrac,
    holdStart,
    holdDur,
  }
}

type Motion = {
  x: number
  y: number
  bx: number
  by: number
  scaleX: number
  scaleY: number
  blur: number
  opacity: number
  weight: number
  sx: number // text-shadow offset x
  sy: number // text-shadow offset y
  sBlur: number // text-shadow blur radius (0 = crisp echo)
  shadowMix: number // text-shadow colour strength (% of currentColor)
}

const clampWeight = (w: number): number => (w < 250 ? 250 : w > 900 ? 900 : w)

// a scale axis this frame: a slow oscillation, a held squash, or 1. Ungated — the
// scale is NOT tied to the entrance, so fading in never changes the glyph's scale.
const evalScale = (c: ScaleChan, t: number): number =>
  c.mode === 'osc'
    ? 1 + c.amp * Math.sin(TAU * c.freq * t + c.phase)
    : c.mode === 'static'
      ? c.base
      : 1

// pure: (elapsed ms, seed) → the glyph's transform/filter/opacity/weight this frame
const motion = (ms: number, s: Seed): Motion => {
  const p = clamp01(ms / s.duration)
  // warp the oscillation clock so the drift/scale FREEZE during the mid-cycle hold, then
  // resume seamlessly — the envelope (p) keeps real time so the ends still land.
  const me =
    ms >= s.holdStart + s.holdDur ? ms - s.holdDur : ms > s.holdStart ? s.holdStart : ms
  const t = me / 1000 // seconds — sine frequencies are in Hz

  // drift + scale run continuously (ungated): they're not coupled to the fade, so the
  // entrance/exit is pure opacity (+ blur). The glyph simply drifts/breathes throughout.
  let x = 0
  let y = 0
  for (const l of s.layers) {
    x += l.ax * Math.sin(TAU * l.fx * t + l.px)
    y += l.ay * Math.sin(TAU * l.fy * t + l.py)
  }

  // entrance (0→1 over enterFrac) and exit (0→1 from exitFrac) progress
  const enterT = smoothstep(0, s.enterFrac, p)
  const exitT = smoothstep(s.exitFrac, 1, p)

  // blur only on ends whose mode is 'blur'; breathing rides on top throughout
  const blurIn = s.enterMode === 'blur' ? s.blurInDist * (1 - enterT) : 0
  const blurOut = s.exitMode === 'blur' ? s.blurOutDist * exitT : 0
  const breathe = s.breatheAmp * (0.5 + 0.5 * Math.sin(TAU * s.breatheFreq * t + s.breathePhase))
  const blur = blurIn + blurOut + breathe

  // both ends fade opacity only — neither moves nor scales the glyph
  const opEnter = enterT
  const opExit = s.exitMode === 'blur' ? 1 - 0.9 * exitT : 1 - exitT
  const opacity = Math.min(opEnter, opExit)

  // weight settles once, smoothly, then holds — finished within ~3–5s of the start
  const weight = clampWeight(
    s.weightFrom + (s.weightTo - s.weightFrom) * smoothstep(s.weightDelay, s.weightDelay + s.weightDur, ms),
  )

  const scaleX = evalScale(s.sx, t)
  const scaleY = evalScale(s.sy, t)

  // shadow: a hard cycle draws a crisp echo (blur 0) whose offset slowly slides on its
  // own oscillation; otherwise a soft halo trailing slightly opposite the drift.
  const shX = s.hardShadow ? s.shBaseX + s.shAmpX * Math.sin(TAU * s.shFreqX * t + s.shPhaseX) : -x * 0.15
  const shY = s.hardShadow ? s.shBaseY + s.shAmpY * Math.sin(TAU * s.shFreqY * t + s.shPhaseY) : -y * 0.15

  return {
    x,
    y,
    bx: s.baseX,
    by: s.baseY,
    scaleX,
    scaleY,
    blur,
    opacity,
    weight,
    sx: shX,
    sy: shY,
    sBlur: s.hardShadow ? 0 : 8 + (Math.abs(x) + Math.abs(y)) * 0.05,
    shadowMix: s.hardShadow ? 30 : 12,
  }
}

// --- imperative shell ------------------------------------------------------
const reset = (el: HTMLElement): void => {
  el.style.opacity = '0'
  el.style.transform = ''
  el.style.filter = ''
  el.style.textShadow = ''
  el.style.color = ''
  el.style.fontFamily = ''
  el.style.fontWeight = ''
}

const apply = (el: HTMLElement, m: Motion): void => {
  el.style.opacity = m.opacity.toFixed(3)
  el.style.transform = `translate3d(calc(${m.bx.toFixed(2)}vw + ${m.x.toFixed(2)}px), calc(${m.by.toFixed(3)} * var(--hero-stage-h) + ${m.y.toFixed(2)}px), 0) scale(${m.scaleX.toFixed(3)}, ${m.scaleY.toFixed(3)})`
  el.style.filter = `blur(${m.blur.toFixed(2)}px)`
  el.style.fontWeight = m.weight.toFixed(0)
  el.style.textShadow = `${m.sx.toFixed(1)}px ${m.sy.toFixed(1)}px ${m.sBlur.toFixed(1)}px color-mix(in srgb, currentColor ${m.shadowMix}%, transparent)`
}

// random next index, never the same glyph twice in a row
const pickNext = (n: number, prev: number): number => {
  let next = prev
  while (next === prev) next = Math.floor(Math.random() * n)
  return next
}

// The full motion path: a single rAF clock that only advances while the stage is
// on-screen and the tab is visible.
const runMotion = (items: readonly HTMLElement[], stage: Element): (() => void) => {
  let active: HTMLElement | null = null
  let seed = makeSeed()
  let prev = -1
  let elapsed = 0
  let lastTs = performance.now()
  let onscreen = true
  let raf = 0

  const advance = (): void => {
    if (active) reset(active)
    prev = pickNext(items.length, prev)
    active = items[prev]
    seed = makeSeed()
    elapsed = 0
    active.style.fontFamily = seed.font
    active.style.color = seed.accent ? 'var(--ui-accent)' : ''
  }

  items.forEach(reset)
  advance()

  const running = (): boolean => onscreen && !document.hidden

  const frame = (ts: number): void => {
    const dt = ts - lastTs
    lastTs = ts
    if (running() && active) {
      elapsed += dt
      if (elapsed >= seed.duration) advance()
      else apply(active, motion(elapsed, seed))
    }
    raf = requestAnimationFrame(frame)
  }
  raf = requestAnimationFrame(frame)

  // resync the clock on resume so a paused gap doesn't jump the animation forward
  const resync = (): void => {
    lastTs = performance.now()
  }
  document.addEventListener('visibilitychange', resync)
  const io = new IntersectionObserver(
    ([entry]) => {
      onscreen = entry.isIntersecting
      resync()
    },
    { threshold: 0 },
  )
  io.observe(stage)

  return () => {
    cancelAnimationFrame(raf)
    io.disconnect()
    document.removeEventListener('visibilitychange', resync)
    items.forEach(reset)
  }
}

// prefers-reduced-motion: no transform, no blur, no rAF — just a slow opacity
// crossfade between glyphs. Weight still varies per cycle (it isn't motion).
const runCrossfade = (items: readonly HTMLElement[]): (() => void) => {
  let prev = -1
  let timer = 0
  items.forEach((el) => {
    reset(el)
    el.style.transition = 'opacity 2.5s ease'
  })

  const step = (): void => {
    if (prev >= 0) items[prev].style.opacity = '0'
    prev = pickNext(items.length, prev)
    const el = items[prev]
    el.style.fontFamily = Math.random() < 0.2 ? 'var(--font-default)' : 'var(--font-alternative)'
    el.style.fontWeight = String(Math.round(rand(250, 900)))
    // a static left/right bias is placement, not motion — fine under reduced-motion.
    // Same bias as the motion path: mostly right, ~15% gentle-left, rest centred.
    const place = Math.random()
    const leftPlaced = place < 0.15
    const bx = leftPlaced ? rand(-16, -4) : place < 0.35 ? rand(-7, 7) : rand(10, 34)
    el.style.transform = `translateX(${bx.toFixed(2)}vw)`
    el.style.color = (leftPlaced ? Math.random() < 0.75 : Math.random() < 0.15) ? 'var(--ui-accent)' : ''
    el.style.opacity = '1'
    timer = window.setTimeout(step, rand(60_000, 90_000))
  }
  step()

  return () => {
    clearTimeout(timer)
    items.forEach((el) => {
      el.style.transition = ''
      reset(el)
    })
  }
}

export const mountCarousel = (selector: string): void => {
  const stage = document.querySelector<HTMLElement>(selector)
  const items = stage ? [...stage.querySelectorAll<HTMLElement>('li')] : []
  if (!stage || items.length < 2) return

  // the figcaption names the set; keep AT from reading each frame's lone glyph
  items.forEach((el) => el.setAttribute('aria-hidden', 'true'))

  const reduce = matchMedia('(prefers-reduced-motion: reduce)')
  let stop = (): void => {}

  const start = (): void => {
    stop()
    stop = reduce.matches ? runCrossfade(items) : runMotion(items, stage)
  }

  start()
  reduce.addEventListener('change', start)
}
