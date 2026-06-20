// Syntax highlighting for the 用法 code terminals, via the CSS Custom Highlight API
// (Baseline 2025: Chrome 105 / Safari 17.2 / Firefox 140). No DOM mutation — each
// <code> stays a single pure-text node; we register a Range per token under one
// Highlight per category and colour them with ::highlight(code-*) in usage.css.
// Feature-detected: where the API is missing, the code just stays plain light-on-dark
// text — still perfectly readable, just uncoloured.
//
// The lexer is deliberately tiny: a per-language ordered list of [category, sticky
// RegExp] rules, scanned left-to-right (first rule that matches at the cursor wins,
// else advance one char as plain). Enough to colour these snippets — not a parser.

type Lang = 'html' | 'css' | 'js' | 'bash'
type Cat = 'comment' | 'string' | 'keyword' | 'attr' | 'number' | 'punct'
type Rule = readonly [Cat, RegExp]
type Token = { readonly cat: Cat; readonly start: number; readonly end: number }

const $$ = <T extends Element>(sel: string) => [...document.querySelectorAll<T>(sel)]

const STRING = /'[^']*'|"[^"]*"/y

// Ordered per language — earlier rules win, so comments/strings come before the
// patterns that might otherwise eat into them.
const RULES: Record<Lang, readonly Rule[]> = {
  css: [
    ['comment', /\/\*[\s\S]*?\*\//y],
    ['string', STRING],
    ['keyword', /[\w-]+(?=\s*:)/y], // property names, incl. --custom-properties
    ['number', /-?\.?\d[\d\w.%]*/y], // 250 · .25rem · 75% · 16px
    ['punct', /[{}():;,]/y],
  ],
  html: [
    ['comment', /<!--[\s\S]*?-->/y],
    ['keyword', /<\/?[\w-]+|\/?>/y], // tag open/close brackets + name
    ['attr', /[\w-]+(?==)/y], // attribute name before =
    ['string', STRING],
  ],
  js: [
    ['comment', /\/\/.*/y],
    ['keyword', /\b(?:import|from|export|default|const|let|return)\b/y],
    ['string', STRING],
  ],
  bash: [
    ['comment', /#.*/y],
    ['keyword', /\b(?:npm|npx|yarn|pnpm|i|install|add)\b/y],
    ['string', STRING],
  ],
}

const CATS = ['comment', 'string', 'keyword', 'attr', 'number', 'punct'] as const

// pure: source → non-overlapping tokens
const tokenize = (lang: Lang, src: string): Token[] => {
  const rules = RULES[lang]
  const out: Token[] = []
  let i = 0
  while (i < src.length) {
    const hit = rules.find(([, re]) => {
      re.lastIndex = i
      return re.test(src) && re.lastIndex > i
    })
    if (hit) {
      const [cat, re] = hit
      out.push({ cat, start: i, end: re.lastIndex })
      i = re.lastIndex
    } else {
      i += 1
    }
  }
  return out
}

// One Highlight per category, registered once and reused. Lazily created on first
// highlightAll() so the feature-detect can bail cleanly before touching CSS.highlights.
let reg: Record<Cat, Highlight> | null = null
const ensureReg = (): Record<Cat, Highlight> | null => {
  if (reg) return reg
  // Custom Highlight API — feature-detect via globalThis (so TS doesn't narrow the
  // constructor away), degrade to plain text when absent.
  if (!('Highlight' in globalThis) || !('highlights' in CSS)) return null
  reg = Object.fromEntries(CATS.map((c) => [c, new Highlight()])) as Record<Cat, Highlight>
  CATS.forEach((c) => CSS.highlights.set(`code-${c}`, reg![c]))
  return reg
}

// (Re)highlight every matching <code>. Ranges live in the shared Highlight registries,
// so we clear them first — the dynamic 用法 blocks rewrite their text on each selection,
// which invalidates the old ranges; clearing + re-tokenising keeps them in sync.
export const highlightAll = (selector = 'pre[data-lang] > code'): void => {
  const r = ensureReg()
  if (!r) return
  CATS.forEach((c) => r[c].clear())
  $$<HTMLElement>(selector).forEach(($code) => {
    const text = $code.firstChild
    if (!(text instanceof Text)) return // expect one pure-text node per <code>
    const lang = $code.parentElement?.dataset.lang
    if (!lang || !(lang in RULES)) return
    tokenize(lang as Lang, text.data).forEach(({ cat, start, end }) => {
      const range = new Range()
      range.setStart(text, start)
      range.setEnd(text, end)
      r[cat].add(range)
    })
  })
}

export const mountCodeHighlight = (selector?: string): void => highlightAll(selector)
