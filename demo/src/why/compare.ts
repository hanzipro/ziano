// The heritage compare figure: the Songti TC cells for 漢/骨/育/北 are blanked
// because Songti TC betrays the MOE standard there (it leans heritage), which
// would exonerate the standard. But that only holds where Songti TC actually
// renders — on systems without it the .standard-ming stack falls back to
// PMingLiU / Noto Serif TC, both faithful to the standard, so the specimens
// must show. Feature-detected with the Font Loading API (document.fonts.check
// matches installed system fonts; Baseline widely available) — no UA sniffing.
export const mountCompare = (): void => {
  const $compare = document.querySelector<HTMLElement>('.compare')
  if (!$compare) return
  $compare.classList.toggle(
    'songti-tc',
    document.fonts.check('1em "Songti TC"'),
  )
}
