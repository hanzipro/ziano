import json
import re
from dataclasses import dataclass

_UR_RE = re.compile(r"unicode-range:\s*([^;]+);", re.IGNORECASE)


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


def parse_css2_unicode_ranges(css: str) -> list[Slice]:
    return [
        Slice(index=i, unicode_range=m.group(1).strip())
        for i, m in enumerate(_UR_RE.finditer(css))
    ]


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
