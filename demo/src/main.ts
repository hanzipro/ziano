// Entry point for the ziano page. Bun/Vite bundles from here; it wires the split
// modules: persist the dark-mode toggle (its initial state is restored by the inline
// pre-paint script next to the checkbox in index.html), read the font roster, mount
// the playground controls, mount the slice piano (subscribing to its hit set for the
// KB readout), then make the roster cards pick a font + jump to the playground.
import { mountCarousel } from './hero/carousel'
import { mountRoster, readFonts } from './fonts/fonts'
import { mountPlayground } from './playground/playground'
import { mountPiano } from './playground/piano'
import { mountTheme } from './theme/theme'

mountTheme(document.querySelector<HTMLInputElement>('input[name="dark-mode"]'))

mountCarousel('figure ul')

const playground = mountPlayground(readFonts())
mountPiano('.Piano', playground.onHits)

mountRoster((id) => {
  playground.selectFont(id)
  playground.showPreview() // a hero card picks a font to look at → show the preview tab
  document.querySelector('#playground')?.scrollIntoView({ behavior: 'smooth' })
})
