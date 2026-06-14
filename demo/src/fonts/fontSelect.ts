// Populate the customizable <select> from the font model + degrade gracefully.
// (the populate half of the old inline $$fonts script, now declarative.)
import type { Font, Generic } from './fonts'

const GENERIC_LABEL: Record<Generic, string> = {
  ming: '明體',
  hei: '黑體',
  kai: '楷體',
}

// one row per font, previewing in its own family (value = package id)
const toOption = (font: Font): HTMLOptionElement => {
  const option = new Option(`${font.name}　${font.family}`, font.id)
  option.style.fontFamily = `'${font.family}'`
  return option
}

const genericOf = ($g: HTMLOptGroupElement): Generic =>
  ($g.dataset.generics ?? 'ming') as Generic

// Chrome 130+ keeps the authored <button>/<selectedcontent>/<legend>. Safari/FF
// drop them at parse time (and inject stray text), so rebuild a plain native
// control there — group labels from the attribute, not the discarded <legend>.
const degradeToNative = ($select: HTMLSelectElement): void => {
  const groups = [...$select.querySelectorAll<HTMLOptGroupElement>('optgroup')]
  groups.forEach(($g) => {
    $g.replaceChildren()
    $g.label = GENERIC_LABEL[genericOf($g)]
  })
  const placeholder = Object.assign(
    new Option('請選擇字體', '', true, true),
    {
      disabled: true,
    },
  )
  $select.replaceChildren(placeholder, ...groups)
}

export const mountFontSelect = (
  $select: HTMLSelectElement,
  fonts: readonly Font[],
  onPick: (id: string) => void,
): void => {
  if (!CSS.supports('appearance', 'base-select')) degradeToNative($select)

  // optgroups are matched by the parser-safe data-generics, never by <legend>
  const groupByGeneric = new Map(
    Array.from(
      $select.querySelectorAll<HTMLOptGroupElement>('optgroup'),
      ($g) => [genericOf($g), $g],
    ),
  )
  fonts.forEach((font) => groupByGeneric.get(font.generic)?.append(toOption(font)))

  $select.addEventListener('change', () => onPick($select.value))
}
