// Dark mode is CSS-driven (variables.css flips on
// :root:has(input[name='dark-mode']:checked)). The checkbox's initial state is
// restored by a tiny inline script next to it in the markup — it must tick :checked
// before first paint, which a deferred module can't. This module owns only the other
// half: persist the user's toggle so that inline script can restore it next load.
const KEY = 'ziano-theme'

export const mountTheme = ($box: HTMLInputElement | null): void => {
  $box?.addEventListener(
    'change',
    () => {
      try {
        localStorage.setItem(KEY, $box.checked ? 'dark' : 'light')
      } catch {
        /* ignore */
      }
    },
  )
}
