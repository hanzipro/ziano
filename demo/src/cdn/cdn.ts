// CDN source model + pure URL/snippet builders. No DOM, no state — just data in,
// strings out.

export type Source = 'jsdelivr' | 'unpkg' | 'esmsh'

export const SOURCE_LABEL: Record<Source, string> = {
  jsdelivr: 'jsDelivr',
  unpkg: 'unpkg',
  esmsh: 'esm.sh',
}

const SCOPE = '@hanzi.pro/webfonts-'
// VERSION = the pinned version we recommend users copy (immutable, fast-cached).
// DEMO_TAG = the floating dist-tag the demo itself previews, so it always shows the
// newest publish without a code change. We publish with `--tag rc`, so it must be
// 'rc' (NOT 'latest'/unversioned — those stay frozen at rc.0 after `--tag rc`).
// TODO(0.1.0): when the stable 0.1.0 ships to the `latest` tag, switch DEMO_TAG
// to 'latest' and bump VERSION to '0.1.0'. (mirror in cdn-bench.html)
const VERSION = '0.1.0-rc.1'
const DEMO_TAG = 'rc'

const ORIGIN: Record<Source, string> = {
  jsdelivr: 'https://cdn.jsdelivr.net/npm/',
  unpkg: 'https://unpkg.com/',
  esmsh: 'https://esm.sh/',
}

export const pkgBase = (source: Source, id: string, version: string = DEMO_TAG) =>
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

// the copyable <head> drop-in for a selection — pinned VERSION (best practice for
// users), preconnect warms the connection. weight → the per-weight entry.
export const snippet = (source: Source, id: string, weight?: number) =>
  [
    `<link rel="preconnect" href="${preconnectHost(source)}" crossorigin />`,
    `<link rel="stylesheet" href="${pkgBase(source, id, VERSION)}/${cssEntry(weight)}" />`,
  ].join('\n')
