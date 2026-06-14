// The font roster model — lifted from the <dl> cards in <main>, the single source
// of truth on this page. Reads explicit data-* only (no positional <dd>, no
// id-guessed script): data-name / data-font-family / data-script / data-generics /
// data-weights / data-variable.

export type Generic = 'ming' | 'hei' | 'kai'
export type Script = 'tc' | 'sc' | 'jp'

export type Font = {
  readonly id: string
  readonly generic: Generic
  readonly name: string // 中文 name (e.g. 尚古宋)
  readonly family: string // CSS font-family (e.g. Shanggu Serif)
  readonly variable: boolean
  readonly weights: readonly number[]
  readonly script: Script
}

const parseFont = ($dl: HTMLElement): Font => ({
  id: $dl.dataset.fontName ?? '',
  generic: ($dl.dataset.generics ?? 'ming') as Generic,
  name: $dl.dataset.name ?? '',
  family: $dl.dataset.fontFamily ?? '',
  variable: $dl.dataset.variable === 'true',
  weights: ($dl.dataset.weights ?? '').split(/[-,]/).map(Number),
  script: ($dl.dataset.script ?? 'tc') as Script,
})

export const readFonts = (root: ParentNode = document): readonly Font[] =>
  Array.from(root.querySelectorAll<HTMLElement>('main article dl'), parseFont)

export const byId = (fonts: readonly Font[], id: string): Font | undefined =>
  fonts.find((f) => f.id === id)

// Progressive enhancement: make each roster <dl> a button that picks its font.
// The cards are semantic <dl>s, so we add the button affordances (role/tabindex/
// keyboard) from script rather than wrapping the markup.
export const mountRoster = (
  onPick: (id: string) => void,
  root: ParentNode = document,
): void => {
  root.querySelectorAll<HTMLElement>('main article dl').forEach(($dl) => {
    const id = $dl.dataset.fontName
    if (!id) return
    $dl.tabIndex = 0
    $dl.setAttribute('role', 'button')
    $dl.addEventListener('click', () => onPick(id))
    $dl.addEventListener(
      'keydown',
      (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onPick(id)
        }
      },
    )
  })
}
