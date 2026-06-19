// CDN source model + pure URL/snippet builders. No DOM, no state — just data in,
// strings out.

export type Source = 'jsdelivr' | 'unpkg' | 'esmsh'

export const SOURCE_LABEL: Record<Source, string> = {
  jsdelivr: 'jsDelivr',
  unpkg: 'unpkg',
  esmsh: 'esm.sh',
}

const SCOPE = '@hanzi.pro/webfonts-'
// PINNED = the immutable per-family version used by BOTH the live preview and the
// copyable snippet. We pin instead of the floating `@rc` tag on purpose: jsDelivr
// edge-caches each `@rc/files/*.woff2` URL for ~12h, so after the Shanggu CFF2→glyf
// republish `@rc` served a stale MIX of old-CFF2 + new-glyf slices (looked thin and
// uneven). An immutable @version sidesteps that. Families sit on different RCs; latest
// round = the emoji unicode-range prune (docs/safari-unicode-range-emoji-tofu.md).
// KEEP IN SYNC with the <link> pins in index.html — both match `npm view … dist-tags`.
// TODO(0.1.0): when stable 0.1.0 ships, collapse PINNED to a flat '0.1.0'.
const DEFAULT_VERSION = '0.1.0-rc.2'
const PINNED: Record<string, string> = {
  'shanggu-serif': '0.1.0-rc.5',
  'shanggu-sans': '0.1.0-rc.5',
  'shanggu-serif-tc': '0.1.0-rc.3',
  'shanggu-sans-tc': '0.1.0-rc.3',
  'genki-min': '0.1.0-rc.1',
  'genki-min-tc': '0.1.0-rc.1',
  'genki-gothic': '0.1.0-rc.1',
  'genki-gothic-tc': '0.1.0-rc.1',
}
const pinnedVersion = (id: string) => PINNED[id] ?? DEFAULT_VERSION

const ORIGIN: Record<Source, string> = {
  jsdelivr: 'https://cdn.jsdelivr.net/npm/',
  unpkg: 'https://unpkg.com/',
  esmsh: 'https://esm.sh/',
}

export const pkgBase = (source: Source, id: string, version: string = pinnedVersion(id)) =>
  `${ORIGIN[source]}${SCOPE}${id}@${version}`

// swap.css is the default display-mode entry (block.css / optional.css alongside).
// A weight selects the per-weight file swap/<w>.css (smaller — one weight only);
// omit it for the whole family. The demo loads the floating @rc so the preview is
// always current.
const cssEntry = (weight?: number) =>
  weight === undefined ? 'swap.css' : `swap/${weight}.css`

export const cssUrl = (source: Source, id: string, weight?: number) =>
  `${pkgBase(source, id)}/${cssEntry(weight)}`

// URL of one slice's woff2 (mirrors build.py woff2_name): vf → id.i.woff2,
// static → id.weight.i.woff2. Floats with cssUrl so the Performance API entries
// line up for the KB readout.
export const woff2Url = (source: Source, id: string, slice: number, weight?: number) =>
  `${pkgBase(source, id)}/files/${weight === undefined ? `${id}.${slice}` : `${id}.${weight}.${slice}`}.woff2`

export const preconnectHost = (source: Source) => new URL(ORIGIN[source]).origin

// the copyable <head> drop-in for a selection — pinned per-family version (best
// practice for users), preconnect warms the connection. weight → the per-weight entry.
export const snippet = (source: Source, id: string, weight?: number) =>
  [
    `<link rel="preconnect" href="${preconnectHost(source)}" crossorigin />`,
    `<link rel="stylesheet" href="${pkgBase(source, id, pinnedVersion(id))}/${cssEntry(weight)}" />`,
  ].join('\n')

// ── self-host (npm) ────────────────────────────────────────────
// For users who'd rather serve the fonts themselves: install the package, then import
// its CSS through a bundler — the woff2 ship in the package's own files/, so there's no
// extra asset wiring. Pinned to the same per-family version as the CDN snippet: the
// packages publish under the `rc` dist-tag, so `latest` hasn't moved and a bare
// `npm i @hanzi.pro/webfonts-…` wouldn't resolve.
export const npmInstall = (id: string) => `npm i ${SCOPE}${id}@${pinnedVersion(id)}`
// the bundler import for the chosen display mode + weight (mirrors cssEntry — omit the
// weight for the whole family, pass it for the smaller per-weight entry).
export const npmImport = (id: string, weight?: number) =>
  `import '${SCOPE}${id}/${cssEntry(weight)}'`
