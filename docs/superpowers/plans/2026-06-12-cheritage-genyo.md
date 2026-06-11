# cheritage Plan 2 — GenYo neutral-alt families (static per-weight)

**Goal:** Add the two neutral-alt families from spec §3 as installable packages —
`@cheritage/genyo-min` (源樣明體, serif) and `@cheritage/genyo-gothic` (源樣黑體,
sans) — built from **static per-weight** OTFs (all ~7 Source Han weights), reusing
the Plan 1 pipeline and filling in its untested `format = "static"` branch.

**Spec:** `docs/superpowers/specs/2026-06-12-cheritage-design.md` §3 (roster),
§4 (static = one slice-set per weight), §6 (consumption / override vars).

**Builds on:** Plan 1 (`feat/plan1-core-pipeline`). cssgen already accepts a
`weight=` arg and `woff2_name` already emits `<id>.<weight>.<slice>.woff2`;
acquire.extract_member already handles `.zip`. What's missing: a roster schema
for per-weight members, a static branch in `build.py`, and the per-weight CSS +
`index.css` layout.

---

## Investigation results (resolved against the live ButTaiwan releases)

- **Edition (spec "月版/TW"):** README confirms **TW = 月版**, the *milder/modern*
  Taiwan cut (e.g. 者 without dot) — exactly the spec's "neutral, milder than
  Shanggu's full 舊字形" intent. (TC = 丹版 is the *more* traditional letterpress
  cut; noted as a future heritage-leaning drop-in, not built here.)
- **Series:** **GenYo (源樣, original Source Han strokes)**, not Genki (源起,
  broken-stroke) — per spec.
- **Assets:** per-region OTF zips. Serif `GenYoMin2TW-otf.zip`, sans
  `GenYoGothic2TW-otf.zip`. OFL inside is `SIL_Open_Font_License_1.1.txt`.
- **Format:** static OTF (CFF) → woff2. CFF-flavoured woff2 is broadly supported;
  `desubroutinize=True` (already set) keeps it small.
- **Weights (authoritative `usWeightClass`; serif and sans differ — real Source Han):**
  - serif: 250 EL · 300 L · 400 R · 500 M · 600 SB · 700 B · 900 H
  - sans:  250 EL · 300 L · 350 N · 400 R · 500 M · 700 B · 900 H
- **RFN gate:** no `with Reserved Font Name` in the OFL → keep names
  `GenYo Min` / `GenYo Gothic`.
- **Coverage:** GenYoMin Regular covers 24/24 common-hard chars (35,349 glyphs).
- **sha256:** Min `64ed21a2…9718`, Gothic `616be26e…5d7c` (filled in roster).

---

## Task 1: Roster schema for per-weight static families

- Add `Weight(weight:int, member:str)` dataclass to `roster.py`.
- `FamilyConfig`: `member: str = ""` (now optional — vf only), add
  `weights: tuple[Weight,...] = ()` (static only).
- `load_roster`: convert `raw["weights"]` (list of tables) → `tuple[Weight]`.
  Validate: vf ⇒ non-empty `member`; static ⇒ non-empty `weights`.
- Add `genyo-min` + `genyo-gothic` `[[family]]` blocks with `[[family.weights]]`
  sub-tables (real members + usWeightClass values above) and real sha256.
- Test: load roster → genyo-min has 7 weights, weight 600 → `GenYoMin2TW-SB.otf`;
  genyo-gothic has weight 350 → `GenYoGothic2TW-N.otf`; static-without-weights and
  vf-without-member both raise ValueError. Shanggu vf still loads (member kept).

## Task 2: CSS — per-weight files + index.css

- `cssgen.generate_index_css(fam) -> str`: `@import url("./<weight>.css");` per
  weight, in ascending order.
- (generate_css already emits per-weight faces via `weight=`.)
- Test: index.css imports `./250.css`…`./900.css`; a weight css has
  `font-weight: 600;` and `src: …/genyo-min.600.<i>.woff2`.

## Task 3: Packager — static layout

- `package_json`: static ⇒ entry `index.css`, `files` glob `*.css` (+ files/,
  LICENSE, README.md), exports `./index.css` + `./files/*`.
- `write_package_skeleton`: add `extra_css: dict[str,str] = {}` → write each
  extra `<name>.css` at package root (the per-weight files).
- Test: static skeleton writes index.css + each `<weight>.css`; package_json name
  `@cheritage/genyo-min`, entry index.css. vf path unchanged (regression test).

## Task 4: Build — static branch

- `build_family`: branch on `fam.format`.
  - static: extract each weight member once; write `index.css` (entry) +
    `<weight>.css` (extra_css); subset every (weight × slice) →
    `files/<id>.<weight>.<slice>.woff2` with `keep_variations=False`.
- Add optional `only_weights: list[int] | None = None` (dev/test: subset a subset
  of weights; CLI/default = all). Keeps the integration test ~1 min.
- Test (integration): `build_family("genyo-gothic", only_weights=[400])` →
  index.css imports all 7 `./<w>.css`; `400.css` has `font-weight: 400`; every
  `genyo-gothic.400.*.woff2` is real woff2 and referenced; OFL bundled.

## Task 5: Real build + size report + visual

- Build both full families (CLI) — note: 7 weights × ~105 slices is a multi-minute
  build per family.
- `npm pack --dry-run` both; record per-package size + a per-weight woff2 size
  sample.
- Extend `tests/visual/index.html` with a GenYo serif+sans row at two weights
  (e.g. 400 vs 700) so the neutral cut can be eyeballed next to Shanggu; refresh
  `smoke.png`.

## Task 6: Coverage confirmation (serif-vs-serif, spec §9.1)

- Run coverage on GenYoMin-R vs `common-hard-tc.txt`; append a line to spec §9.1
  comparing Shanggu serif vs GenYo serif on the curated set (the comparison the
  Plan 1 verdict deferred).

---

## Deferred (unchanged from Plan 1's list)
Plan 3 meta-package · Plan 4 CI/publish · Plan 5 demo site · Plan 6 han.css
integration. Possible future: GenYo **TC (丹版)** as a heritage-leaning variant;
Genki series; other regions (HK/JP).
