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

// font-display modes — each ships its own CSS entry (swap.css / block.css /
// optional.css, and the per-weight swap/<w>.css … beside them)
export type Display = 'swap' | 'block' | 'optional'

// the CSS entry for a display mode (+ optional single weight): <mode>.css for the
// whole family, <mode>/<w>.css for one weight (smaller). The live preview omits the
// mode → defaults to swap; the 用法 generator passes the reader's choice.
const cssEntry = (weight?: number, display: Display = 'swap') =>
  weight === undefined ? `${display}.css` : `${display}/${weight}.css`

export const cssUrl = (source: Source, id: string, weight?: number) =>
  `${pkgBase(source, id)}/${cssEntry(weight)}`

// URL of one slice's woff2 (mirrors build.py woff2_name): vf → id.i.woff2,
// static → id.weight.i.woff2. Floats with cssUrl so the Performance API entries
// line up for the KB readout.
export const woff2Url = (source: Source, id: string, slice: number, weight?: number) =>
  `${pkgBase(source, id)}/files/${weight === undefined ? `${id}.${slice}` : `${id}.${weight}.${slice}`}.woff2`

export const preconnectHost = (source: Source) => new URL(ORIGIN[source]).origin

// the two <head> lines, as reusable pieces (so a multi-font block can interleave one
// preconnect with many stylesheet links). weight → the per-weight entry.
export const preconnectLine = (source: Source) =>
  `<link rel="preconnect" href="${preconnectHost(source)}" crossorigin />`
export const linkLine = (source: Source, id: string, weight?: number, display: Display = 'swap') =>
  `<link rel="stylesheet" href="${pkgBase(source, id, pinnedVersion(id))}/${cssEntry(weight, display)}" />`

// the copyable <head> drop-in for a selection — pinned per-family version (best
// practice for users), preconnect warms the connection.
export const snippet = (source: Source, id: string, weight?: number) =>
  [preconnectLine(source), linkLine(source, id, weight)].join('\n')

// ── self-host (npm/pnpm/yarn) ──────────────────────────────────
// For users who'd rather serve the fonts themselves: install the package(s), then
// import the CSS through a bundler — the woff2 ship in each package's own files/, so
// there's no extra asset wiring. Pinned to the same per-family version as the CDN
// snippet: the packages publish under the `rc` dist-tag, so `latest` hasn't moved and a
// bare install wouldn't resolve.
export type PM = 'npm' | 'pnpm' | 'yarn'
const INSTALL: Record<PM, string> = { npm: 'npm i', pnpm: 'pnpm add', yarn: 'yarn add' }
// the @scope/name@version spec the registry resolves
export const pkgSpec = (id: string) => `${SCOPE}${id}@${pinnedVersion(id)}`
// one install command for any number of packages, in the chosen package manager
export const installCmd = (pm: PM, ids: readonly string[]) =>
  `${INSTALL[pm]} ${ids.map(pkgSpec).join(' ')}`
// single-package npm install (the playground's one-font snippet)
export const npmInstall = (id: string) => installCmd('npm', [id])
// the bundler import for the chosen display mode + weight (mirrors cssEntry — omit the
// weight for the whole family, pass it for the smaller per-weight entry).
export const npmImport = (id: string, weight?: number, display: Display = 'swap') =>
  `import '${SCOPE}${id}/${cssEntry(weight, display)}'`
