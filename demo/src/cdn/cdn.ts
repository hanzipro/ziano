// CDN source model + pure URL/snippet builders. No DOM, no state — just data in,
// strings out.

export type Source = 'jsdelivr' | 'unpkg' | 'esmsh'

export const SOURCE_LABEL: Record<Source, string> = {
  jsdelivr: 'jsDelivr',
  unpkg: 'unpkg',
  esmsh: 'esm.sh',
}

const SCOPE = '@hanzi.pro/webfonts-'
// 0.1.0 shipped stable, so both the live preview and the copyable snippet ride the
// `@latest` tag — it always resolves to the current stable release, so the demo never
// needs a per-release version bump. (During the RC phase we pinned exact versions to
// dodge jsDelivr's ~12h edge-cache serving a stale @rc mix mid-republish; a stable
// semver version is immutable, so @latest is safe now.)
const cdnVersion = (_id: string) => 'latest'

const ORIGIN: Record<Source, string> = {
  jsdelivr: 'https://cdn.jsdelivr.net/npm/',
  unpkg: 'https://unpkg.com/',
  esmsh: 'https://esm.sh/',
}

export const pkgBase = (source: Source, id: string, version: string = cdnVersion(id)) =>
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
  `<link rel="stylesheet" href="${pkgBase(source, id, cdnVersion(id))}/${cssEntry(weight, display)}" />`

// the copyable <head> drop-in for a selection — rides @latest; preconnect warms the
// connection. (Users who want immutable edge-caching can swap @latest for a pinned
// version like @0.1.0.)
export const snippet = (source: Source, id: string, weight?: number) =>
  [preconnectLine(source), linkLine(source, id, weight)].join('\n')

// ── self-host (npm/pnpm/yarn) ──────────────────────────────────
// For users who'd rather serve the fonts themselves: install the package(s), then
// import the CSS through a bundler — the woff2 ship in each package's own files/, so
// there's no extra asset wiring. Rides @latest like the CDN snippet now that 0.1.0 is
// the published `latest` dist-tag.
export type PM = 'npm' | 'pnpm' | 'yarn'
const INSTALL: Record<PM, string> = { npm: 'npm i', pnpm: 'pnpm add', yarn: 'yarn add' }
// the @scope/name@version spec the registry resolves
export const pkgSpec = (id: string) => `${SCOPE}${id}@${cdnVersion(id)}`
// one install command for any number of packages, in the chosen package manager
export const installCmd = (pm: PM, ids: readonly string[]) =>
  `${INSTALL[pm]} ${ids.map(pkgSpec).join(' ')}`
// single-package npm install (the playground's one-font snippet)
export const npmInstall = (id: string) => installCmd('npm', [id])
// the bundler import for the chosen display mode + weight (mirrors cssEntry — omit the
// weight for the whole family, pass it for the smaller per-weight entry).
export const npmImport = (id: string, weight?: number, display: Display = 'swap') =>
  `import '${SCOPE}${id}/${cssEntry(weight, display)}'`
