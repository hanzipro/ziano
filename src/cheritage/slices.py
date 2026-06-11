import json
from dataclasses import dataclass


@dataclass(frozen=True)
class Slice:
    index: int
    unicode_range: str  # raw CSS token list, e.g. "U+41-43, U+4e00"

    def codepoints(self) -> set[int]:
        cps: set[int] = set()
        for tok in self.unicode_range.split(","):
            tok = tok.strip().removeprefix("U+").removeprefix("u+")
            if "-" in tok:
                lo, hi = tok.split("-")
                cps.update(range(int(lo, 16), int(hi, 16) + 1))
            elif tok:
                cps.add(int(tok, 16))
        return cps


def format_unicode_range(cps: set[int]) -> str:
    """Collapse a set of codepoints into a compact CSS unicode-range token list."""
    out: list[str] = []
    s = sorted(cps)
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[j] + 1:
            j += 1
        out.append(f"U+{s[i]:x}" if i == j else f"U+{s[i]:x}-{s[j]:x}")
        i = j + 1
    return ", ".join(out)


def parse_slicing_strategy(text: str) -> list[Slice]:
    """Parse a Google Fonts nam-files slicing-strategy text-proto into slices.

    The proto is a sequence of `subsets { codepoints: N ... }` blocks (Apache-2.0,
    googlefonts/nam-files). Block order is preserved as the slice index.
    """
    slices: list[Slice] = []
    cur: set[int] | None = None
    idx = 0
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("subsets"):
            cur = set()
        elif line.startswith("}"):
            if cur is not None:
                slices.append(Slice(index=idx, unicode_range=format_unicode_range(cur)))
                idx += 1
                cur = None
        elif line.startswith("codepoints:") and cur is not None:
            cur.add(int(line[len("codepoints:"):].split("#", 1)[0].strip()))
    return slices


def save_slices(slices: list[Slice], path: str) -> None:
    with open(path, "w") as fh:
        json.dump(
            [{"index": s.index, "unicode_range": s.unicode_range} for s in slices],
            fh,
            ensure_ascii=False,
            indent=0,
        )


def load_slices(path: str) -> list[Slice]:
    with open(path) as fh:
        return [Slice(**row) for row in json.load(fh)]
