// The 用法 screen's config generator. An <aside> lets the reader pick one heritage
// font per role (黑體 / 明體 / 楷體), a package manager, and a CDN; the static code
// terminals in the guide are then rewritten to match. Like the playground: one
// immutable-ish state, pure block builders (state → string), an imperative shell that
// pushes them to the DOM and re-runs the syntax highlighter.
import type { Font, Generic } from '../fonts/fonts'
import { byId } from '../fonts/fonts'
import type { Display, PM, Source } from '../cdn/cdn'
import { installCmd, linkLine, npmImport, preconnectLine } from '../cdn/cdn'
import { highlightAll } from '../code/highlight'

const $ = <T extends Element>(sel: string, root: ParentNode = document) =>
  root.querySelector<T>(sel)

// roles ARE the three CSS generics, in the order they appear in the stacks/output
type Role = Generic // 'hei' | 'ming' | 'kai'
const ROLES: readonly Role[] = ['hei', 'ming', 'kai']

// per role: the chosen font id (null = 不使用) + the static weights to load (empty =
// whole-family swap.css; ignored for a variable font, which is one file regardless)
type RoleState = { readonly id: string | null; readonly weights: readonly number[] }
type State = {
  readonly source: Source
  readonly pm: PM
  readonly display: Display
  readonly roles: Record<Role, RoleState>
}

// one CSS entry to load: a package + optional single weight (→ swap/<w>.css)
type Entry = { readonly id: string; readonly weight?: number }

// ── pure: state → the entries / families each block needs ───────
const roleEntries = (rs: RoleState, font: Font): readonly Entry[] => {
  if (!rs.id) return []
  if (font.variable || rs.weights.length === 0) return [{ id: rs.id }]
  return rs.weights.map((weight) => ({ id: rs.id as string, weight }))
}

// ── pure: builders (state → terminal text) ─────────────────────
const cdnBlock = (source: Source, entries: readonly Entry[], display: Display): string =>
  entries.length === 0
    ? '<!-- 請於左側選擇字體 -->'
    : [preconnectLine(source), ...entries.map((e) => linkLine(source, e.id, e.weight, display))].join('\n')

const installBlock = (pm: PM, ids: readonly string[]): string =>
  ids.length === 0 ? '# 請於左側選擇字體' : installCmd(pm, ids)

const importBlock = (entries: readonly Entry[], display: Display): string =>
  entries.length === 0
    ? '// 請於左側選擇字體'
    : entries.map((e) => npmImport(e.id, e.weight, display)).join('\n')

// the full four-layer stacks, one block per enabled role — single source of the stack
// design (the static example block above narrates the layers; this is the real config)
const sansStack = (fam: string, tail: string): string =>
  `    'Avenir Next', 'Segoe UI Variable', 'Segoe UI', Roboto,
    '${fam}',
    'Hiragino Sans', 'Hiragino Sans GB', 'Yu Gothic',
    ${tail}`

const rootBlock = (fam: Record<Role, string | null>): string => {
  const decls: string[] = []
  if (fam.hei) {
    decls.push(`  --font-system-ui:\n${sansStack(fam.hei, 'system-ui, sans-serif')}\n  ;`)
    decls.push(`  --font-sans-serif:\n${sansStack(fam.hei, 'sans-serif')}\n  ;`)
  }
  if (fam.ming)
    decls.push(
      `  --font-serif:
    Palatino, Cambria,
    '${fam.ming}',
    'Hiragino Mincho ProN', 'Yu Mincho',
    serif
  ;`,
    )
  if (fam.kai)
    decls.push(
      `  --font-cursive:
    Palatino, Cambria,
    '${fam.kai}',
    Klee, 'Klee One',
    BiauKai, DFKai-SB, 'Kaiti TC',
    'Hiragino Mincho ProN', 'Yu Mincho',
    cursive, serif
  ;`,
    )
  const uses: string[] = []
  if (fam.hei) uses.push('body         { font-family: var(--font-sans-serif); }  /* 黑體：內文、UI */')
  if (fam.ming) uses.push('h1, .display { font-family: var(--font-serif); }       /* 明體：大標 */')
  if (fam.kai) uses.push('blockquote   { font-family: var(--font-cursive); }     /* 楷體：引文、詩句 */')
  if (decls.length === 0) return '/* 請於左側選擇字體 */'
  return `:root {\n${decls.join('\n')}\n}\n\n${uses.join('\n')}`
}

const rootAdvBlock = (fam: Record<Role, string | null>): string => {
  const lines: string[] = []
  if (fam.hei) lines.push("  --fallback-hei:    'Hiragino Sans', 'Hiragino Sans GB', 'Yu Gothic', sans-serif;")
  if (fam.ming) lines.push("  --fallback-ming:   'Hiragino Mincho ProN', 'Yu Mincho', serif;")
  if (fam.hei)
    lines.push(`  --font-sans-serif: 'Avenir Next', 'Segoe UI Variable', 'Segoe UI', '${fam.hei}', var(--fallback-hei);`)
  if (fam.ming) lines.push(`  --font-serif:       Palatino, Cambria, '${fam.ming}', var(--fallback-ming);`)
  if (lines.length === 0) return '/* 請於左側選擇字體 */'
  return `:root {\n${lines.join('\n')}\n}`
}

// ── element factories ──────────────────────────────────────────
const opt = (label: string, value: string): HTMLOptionElement =>
  Object.assign(document.createElement('option'), { textContent: label, value })

const LS = 'ziano-usage'

export const mountUsage = (fonts: readonly Font[]): void => {
  const $usage = $<HTMLElement>('#usage')
  if (!$usage || fonts.length === 0) return

  const byGeneric = (g: Generic) => fonts.filter((f) => f.generic === g)
  // default each role to the first font of its generic in roster order
  const firstId = (g: Generic): string | null => byGeneric(g)[0]?.id ?? null

  const saved = ((): Partial<State> => {
    try {
      return JSON.parse(localStorage.getItem(LS) ?? '{}') as Partial<State>
    } catch {
      return {}
    }
  })()
  let state: State = {
    source: 'jsdelivr',
    pm: 'npm',
    display: 'swap',
    roles: {
      hei: { id: firstId('hei'), weights: [] },
      ming: { id: firstId('ming'), weights: [] },
      kai: { id: firstId('kai'), weights: [] },
    },
    ...saved,
  }

  const out = {
    cdn: $<HTMLElement>('.out-cdn', $usage),
    install: $<HTMLElement>('.out-install', $usage),
    import: $<HTMLElement>('.out-import', $usage),
    root: $<HTMLElement>('.out-root', $usage),
    rootAdv: $<HTMLElement>('.out-root-adv', $usage),
  }

  const fontOf = (role: Role): Font | undefined => {
    const id = state.roles[role].id
    return id ? byId(fonts, id) : undefined
  }
  const familyOf = (role: Role): string | null => fontOf(role)?.family ?? null
  const families = (): Record<Role, string | null> => ({
    hei: familyOf('hei'),
    ming: familyOf('ming'),
    kai: familyOf('kai'),
  })
  const allEntries = (): readonly Entry[] =>
    ROLES.flatMap((r) => {
      const f = fontOf(r)
      return f ? roleEntries(state.roles[r], f) : []
    })
  const enabledIds = (): readonly string[] =>
    ROLES.map((r) => state.roles[r].id).filter((id): id is string => id !== null)

  const save = () => {
    try {
      localStorage.setItem(LS, JSON.stringify(state))
    } catch {
      /* ignore */
    }
  }

  const setText = ($el: HTMLElement | null, text: string) => {
    if ($el) $el.textContent = text
  }

  // ── apply (state → DOM) ──────────────────────────────────────
  const render = () => {
    const entries = allEntries()
    setText(out.cdn, cdnBlock(state.source, entries, state.display))
    setText(out.install, installBlock(state.pm, enabledIds()))
    setText(out.import, importBlock(entries, state.display))
    const fam = families()
    setText(out.root, rootBlock(fam))
    setText(out.rootAdv, rootAdvBlock(fam))
    highlightAll()
  }

  // a pressed-toggle pill (mirrors the playground's static-weight chips)
  const chip = (label: string, pressed: boolean, onClick: () => void): HTMLButtonElement => {
    const $b = document.createElement('button')
    $b.type = 'button'
    $b.textContent = label
    $b.setAttribute('aria-pressed', String(pressed))
    $b.addEventListener('click', onClick)
    return $b
  }

  // a static font's weight picker: 「全選」loads the whole-family swap.css (one bundled
  // file, every weight); each weight chip loads just that weight's swap/<w>.css. They're
  // mutually exclusive — 全選 ⟺ no individual weight chosen (weights === []); picking any
  // weight turns 全選 off. Variable font / 不使用 → no picker (one file covers the axis).
  const buildWeights = (role: Role) => {
    const $wrap = $<HTMLElement>(`.role[data-role="${role}"] .weights`, $usage)
    if (!$wrap) return
    const f = fontOf(role)
    if (!f || f.variable) {
      $wrap.hidden = true
      $wrap.replaceChildren()
      return
    }
    $wrap.hidden = false
    const chosen = state.roles[role].weights
    const $hint = document.createElement('span')
    $hint.className = 'weights-hint'
    $hint.textContent = '字重'
    $wrap.replaceChildren(
      $hint,
      chip('全選', chosen.length === 0, () => setWeights(role, [])),
      ...f.weights.map((w) =>
        chip(String(w), chosen.includes(w), () => toggleWeight(role, w, !chosen.includes(w))),
      ),
    )
  }

  // ── intents (events → state) ─────────────────────────────────
  const setRole = (role: Role, id: string) => {
    state = { ...state, roles: { ...state.roles, [role]: { id: id || null, weights: [] } } }
    buildWeights(role)
    render()
    save()
  }
  const setWeights = (role: Role, weights: readonly number[]) => {
    state = { ...state, roles: { ...state.roles, [role]: { ...state.roles[role], weights } } }
    buildWeights(role) // re-sync the chips' pressed state (incl. 全選)
    render()
    save()
  }
  const toggleWeight = (role: Role, w: number, on: boolean) => {
    const cur = state.roles[role].weights
    setWeights(role, (on ? [...cur, w] : cur.filter((x) => x !== w)).sort((a, b) => a - b))
  }
  const setPM = (pm: PM) => {
    state = { ...state, pm }
    render()
    save()
  }
  const setSource = (source: Source) => {
    state = { ...state, source }
    render()
    save()
  }
  const setDisplay = (display: Display) => {
    state = { ...state, display }
    render()
    save()
  }

  // ── wire ─────────────────────────────────────────────────────
  ROLES.forEach((role) => {
    const $sel = $<HTMLSelectElement>(`select[name="role-${role}"]`, $usage)
    if (!$sel) return
    $sel.append(opt('不使用', ''), ...byGeneric(role).map((f) => opt(f.name, f.id)))
    $sel.value = state.roles[role].id ?? ''
    $sel.addEventListener('change', () => setRole(role, $sel.value))
    buildWeights(role)
  })

  $usage.querySelectorAll<HTMLInputElement>('input[name="pm"]').forEach(($r) => {
    $r.checked = $r.value === state.pm
    $r.addEventListener('change', () => setPM($r.value as PM))
  })
  $usage.querySelectorAll<HTMLInputElement>('input[name="usage-cdn"]').forEach(($r) => {
    $r.checked = $r.value === state.source
    $r.addEventListener('change', () => setSource($r.value as Source))
  })
  $usage.querySelectorAll<HTMLInputElement>('input[name="usage-display"]').forEach(($r) => {
    $r.checked = $r.value === state.display
    $r.addEventListener('change', () => setDisplay($r.value as Display))
  })

  render()
}
