"""외부 레퍼런스 3종 어댑터.

물성별로 조회할 출처를 하나씩 고정한다. 값이 없으면 None을 반환한다 (지어내지 않는다).
CSV 단위에 맞추는 변환은 여기서 끝낸다.
"""
EV_TO_KJMOL_E2 = 0.96485   # eV -> kJ/mol x 1e-2
ALLEN_EV_TO_PAULING = 0.169

# (출처, 설명, CSV 단위)
SPEC = {
    "AR_c": ("pymatgen",      "atomic_radius_calculated",  "ang"),
    "CR":   ("periodictable", "covalent_radius",           "ang"),
    "PE":   ("mendeleev",     "en_pauling",                "Pauling Units"),
    "IE":   ("mendeleev",     "ionenergies[1]",            "kJ/mol*1e-2"),
    "AE":   ("mendeleev",     "en_allen",                  "Pauling Units"),
}


def lookup(symbol, prop):
    """원소 기호와 물성 약어를 받아 (값, 출처, 단위)를 돌려준다. 없으면 (None, 출처, 단위)."""
    if prop not in SPEC:
        raise KeyError(f"모르는 물성: {prop}. 가능한 값: {list(SPEC)}")
    source, attr, unit = SPEC[prop]
    value = _FETCH[prop](symbol)
    return value, f"{source}.{attr}", unit


def _pymatgen_ar_c(sym):
    from pymatgen.core import Element
    v = Element(sym).atomic_radius_calculated
    return None if v is None else round(float(v), 3)


def _periodictable_cr(sym):
    import periodictable
    v = getattr(getattr(periodictable, sym), "covalent_radius", None)
    return None if v is None else round(float(v), 3)


def _mendeleev_pe(sym):
    from mendeleev import element
    v = element(sym).en_pauling
    return None if v is None else round(float(v), 3)


def _mendeleev_ie(sym):
    from mendeleev import element
    v = element(sym).ionenergies.get(1)          # eV
    return None if v is None else round(float(v) * EV_TO_KJMOL_E2, 4)


def _mendeleev_ae(sym):
    from mendeleev import element
    v = element(sym).en_allen                    # eV
    return None if v is None else round(float(v) * ALLEN_EV_TO_PAULING, 3)


_FETCH = {"AR_c": _pymatgen_ar_c, "CR": _periodictable_cr,
          "PE": _mendeleev_pe, "IE": _mendeleev_ie, "AE": _mendeleev_ae}


def demo():
    """CSV 원본값과 대조. 어긋나면 단위 변환이 틀린 것."""
    import csv, pathlib
    csv_path = (pathlib.Path(__file__).parents[2]
                / "reference_data/practice_notebooks/2_primary_feature/primary_feature.csv")
    with open(csv_path, encoding="utf-8-sig") as fh:
        table = {r["Abriv."]: r for r in csv.DictReader(fh)}

    bad = []
    for prop in SPEC:
        for sym in ["Zn", "Te", "Mg", "S", "Se", "Ca"]:
            got, src, unit = lookup(sym, prop)
            want = table[prop][sym].strip()
            if want == "-":
                print(f"  {prop:5s} {sym:3s} CSV=비어있음   조회={got}  ({src})")
                continue
            ok = got is not None and abs(got - float(want)) < 0.02
            print(f"  {prop:5s} {sym:3s} CSV={want:>9s}  조회={got}  {'OK' if ok else '<-- 불일치'}")
            if not ok:
                bad.append((prop, sym, want, got))
    assert not bad, f"단위 변환 오류: {bad}"
    print("\n전부 일치.")


if __name__ == "__main__":
    demo()
