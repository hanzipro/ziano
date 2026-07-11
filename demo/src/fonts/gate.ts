// The font gate's imperative half: reveal the page once its slices have landed.
// The showroom insists on first-paint 傳承字形 (see gate.css for the rationale) —
// but a loading screen must never strand anyone, so document.fonts.ready is
// raced against a hard timeout: past it, reveal anyway and let swap upgrade the
// text as slices arrive. Ugly beats blank.
const TIMEOUT_MS = 4_000

export const mountFontGate = (): void => {
  const root = document.documentElement
  // no pre-paint stamp → nothing to reveal (the no-JS path never reaches here)
  if (!root.classList.contains('fonts-pending')) return
  const timeout = new Promise<void>((resolve) => {
    setTimeout(resolve, TIMEOUT_MS)
  })
  Promise.race([document.fonts.ready.then(() => undefined), timeout]).then(() => {
    root.classList.remove('fonts-pending')
    root.classList.add('fonts-ready') // scopes the one-shot reveal fade
  })
}
