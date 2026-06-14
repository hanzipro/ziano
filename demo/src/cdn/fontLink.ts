// CDN stylesheet management. `useSource` makes the chosen CDN the only one serving
// the webfont sheets: it ensures every family is loaded from that origin (so the
// roster previews + specimen all switch) and prunes the other origins' <link>s —
// including the ones hard-coded in <head>. Idempotent (keyed by href).
import type { Source } from './cdn'
import { cssUrl, preconnectHost } from './cdn'

const fontLinks = () =>
  [...document.querySelectorAll<HTMLLinkElement>('link[rel="stylesheet"][href*="webfonts-"]')]

const ensure = (source: Source, id: string): void => {
  const href = cssUrl(source, id)
  if (fontLinks().some((l) => l.href === href)) return
  document.head.append(
    Object.assign(document.createElement('link'), { rel: 'stylesheet', href }),
  )
}

export const useSource = (source: Source, ids: readonly string[]): void => {
  ids.forEach((id) => ensure(source, id))
  const origin = preconnectHost(source)
  fontLinks()
    .filter((l) => !l.href.startsWith(origin))
    .forEach((l) => l.remove())
}

// Load the selected font's single-weight stylesheet (swap/<w>.css) on top of the
// whole-family swap.css the roster already pulls — to exercise the per-weight files
// and let the copy snippet recommend the smaller import. `weight: null` clears it
// (back to whole-family). Only one per-weight extra at a time (marked data-weight-file).
export const useWeight = (source: Source, id: string, weight: number | null): void => {
  document.querySelectorAll('link[data-weight-file]').forEach((l) => l.remove())
  if (weight === null) return
  const link = Object.assign(document.createElement('link'), {
    rel: 'stylesheet',
    href: cssUrl(source, id, weight),
  })
  link.dataset.weightFile = ''
  document.head.append(link)
}
