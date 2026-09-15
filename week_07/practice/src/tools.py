"""에이전트가 부를 수 있는 도구 5개.

이 파일이 에이전트의 '능력의 한계'다. 여기 없는 일은 모델이 아무리 똑똑해도 못 한다.
각 함수는 평범한 파이썬 함수이고, 아래 declarations()가 그것을 모델에게 설명한다.
"""
import csv, io, pathlib, contextlib, shutil
import refs

DATA = pathlib.Path(__file__).parents[1] / "data"
BLANKED  = DATA / "primary_feature_blanked.csv"   # 원본. 읽기만 한다
CSV_PATH = DATA / "primary_feature_work.csv"      # 작업본. 원본은 건드리지 않는다


def reset():
    """작업본을 원본에서 다시 뜬다. 노트북을 처음부터 다시 돌릴 때 부른다."""
    shutil.copy(BLANKED, CSV_PATH)


reset()   # import 시점에도 한 번. 새 커널은 항상 빈 표로 시작한다

# 도구 응답에 단위 환산 규칙을 넣을지. 실습에서 False -> True로 한 번 바꿔본다.
GIVE_CONVERSION_HINT = False

PROP_NAMES = {
    "AR_c": "계산 원자반지름",   "CR": "공유결합 반지름",
    "PE":   "Pauling 전기음성도", "IE": "1차 이온화에너지",
    "AE":   "Allen 전기음성도",
}
# CSV 열이 쓰는 단위와 도구가 돌려주는 원시 단위가 다를 때의 환산법
CONVERSIONS = {
    "IE": "도구 값은 eV다. CSV 열 단위(kJ/mol x 1e-2)로 넣으려면 0.96485를 곱한다.",
    "AE": "도구 값은 eV다. CSV 열 단위(Pauling 척도)로 넣으려면 0.169를 곱한다.",
}
TARGETS = ["Zn", "Te", "Mg", "S", "Se", "Ca"]      # 이 실습이 쓰는 원소


def _read():
    rows = list(csv.reader(open(CSV_PATH, encoding="utf-8-sig")))
    return rows[0], rows[1:]


def _row(body, prop):
    return next((r for r in body if r[1] == prop), None)


def _is_blank(v):
    return str(v).strip() in ("", "-")


# ── 1 ────────────────────────────────────────────────────────────────
def check_missing(prop: str) -> dict:
    """어떤 물성의 어느 원소가 비어 있는지 알려준다."""
    hdr, body = _read()
    row = _row(body, prop)
    if row is None:
        return {"error": f"모르는 물성: {prop}"}
    missing = [e for e in TARGETS if _is_blank(row[hdr.index(e)])]
    return {"property": prop, "name": PROP_NAMES.get(prop),
            "missing_elements": missing, "count": len(missing)}


# ── 2 ────────────────────────────────────────────────────────────────
def inspect_column(prop: str) -> dict:
    """그 물성 열의 단위와 기존 값 범위를 보여준다. 새 값이 말이 되는지 판단하는 근거."""
    hdr, body = _read()
    row = _row(body, prop)
    if row is None:
        return {"error": f"모르는 물성: {prop}"}
    vals = []
    for c in hdr[3:]:
        v = row[hdr.index(c)]
        if _is_blank(v):
            continue
        try:
            vals.append(float(v))
        except ValueError:
            pass
    return {"property": prop, "name": PROP_NAMES.get(prop),
            "unit_in_csv": row[2], "n_filled": len(vals),
            "min": round(min(vals), 4) if vals else None,
            "max": round(max(vals), 4) if vals else None,
            "example_values": [round(v, 4) for v in vals[:8]]}


# ── 3 ────────────────────────────────────────────────────────────────
def lookup_element(symbol: str, prop: str) -> dict:
    """외부 레퍼런스에서 조회한다. 값이 없으면 null을 돌려준다 (지어내지 않는다)."""
    try:
        value, source, csv_unit = refs.lookup(symbol, prop)
    except KeyError as e:
        return {"error": str(e)}
    if value is None:
        return {"symbol": symbol, "property": prop, "value": None,
                "note": "이 출처에 값이 없다. 다른 값으로 대체하지 말 것."}

    # refs.py는 CSV 단위로 이미 환산해 준다. 실습에서는 일부러 원시 단위로 되돌린다.
    raw, raw_unit = value, csv_unit
    if prop == "IE":
        raw, raw_unit = round(value / refs.EV_TO_KJMOL_E2, 4), "eV"
    elif prop == "AE":
        raw, raw_unit = round(value / refs.ALLEN_EV_TO_PAULING, 4), "eV"

    out = {"symbol": symbol, "property": prop, "value": raw,
           "unit": raw_unit, "source": source}
    if GIVE_CONVERSION_HINT and prop in CONVERSIONS:
        out["conversion_note"] = CONVERSIONS[prop]
    return out


# ── 4 ────────────────────────────────────────────────────────────────
def fill_value(symbol: str, prop: str, value: float, source: str = "") -> dict:
    """CSV의 빈 칸을 채운다. 이미 값이 있으면 덮지 않는다."""
    hdr, body = _read()
    if symbol not in hdr:
        return {"error": f"모르는 원소: {symbol}"}
    row = _row(body, prop)
    if row is None:
        return {"error": f"모르는 물성: {prop}"}
    i = hdr.index(symbol)
    if not _is_blank(row[i]):
        return {"ok": False, "reason": f"이미 값이 있다: {row[i]}"}
    row[i] = str(value)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(hdr); w.writerows(body)
    return {"ok": True, "filled": f"{prop}/{symbol} = {value}", "source": source}


# ── 5 ────────────────────────────────────────────────────────────────
def run_sisso(n_expansion: int = 2, n_term: int = 2, k: int = 20) -> dict:
    """완성된 특징표로 SISSO를 돌려 수식과 오차를 돌려준다."""
    import pandas as pd
    from TorchSisso import SissoModel
    tr = pd.read_csv(DATA / "train.dat", sep=r"\s+")
    feats = [c for c in tr.columns if c not in ("material", "property")]
    df = pd.concat([tr.property.rename("Target"), tr[feats]], axis=1)
    with contextlib.redirect_stdout(io.StringIO()):        # 라이브러리 로그 억제
        m = SissoModel(data=df,
                       operators=["+", "-", "*", "/", "exp", "ln", "pow(2)", "sqrt"],
                       n_expansion=n_expansion, n_term=n_term, k=k, device="cpu")
        rmse, eq, r2, _ = m.fit()
    return {"rmse": round(float(rmse), 4), "r2": round(float(r2), 4),
            "equation": str(eq),
            "settings": {"n_expansion": n_expansion, "n_term": n_term, "k": k}}


REGISTRY = {f.__name__: f for f in
            (check_missing, inspect_column, lookup_element, fill_value, run_sisso)}


# ── 모델에게 도구를 설명하는 부분 ─────────────────────────────────────
def declarations():
    """Gemini 함수 선언. 이 설명이 곧 에이전트의 성능이다."""
    from google.genai import types as t
    OBJ, NUM, INT, STRT = t.Type.OBJECT, t.Type.NUMBER, t.Type.INTEGER, t.Type.STRING
    P = lambda **kw: t.Schema(type=OBJ, properties=kw, required=list(kw))
    STR = lambda d, **kw: t.Schema(type=STRT, description=d, **kw)
    prop = STR("물성 약어. " + ", ".join(f"{k}={v}" for k, v in PROP_NAMES.items())
               + ". PE와 AE는 서로 다른 물성이다.", enum=list(PROP_NAMES))

    return [t.Tool(function_declarations=[
        t.FunctionDeclaration(
            name="check_missing",
            description="어떤 물성에서 값이 비어 있는 원소 목록을 얻는다.",
            parameters=P(prop=prop)),
        t.FunctionDeclaration(
            name="inspect_column",
            description=("그 물성 열의 단위와 기존 값 범위를 본다. "
                         "새로 넣을 값이 이 범위와 맞는지 반드시 확인할 것."),
            parameters=P(prop=prop)),
        t.FunctionDeclaration(
            name="lookup_element",
            description="외부 레퍼런스에서 원소 물성을 조회한다. 없으면 null을 돌려준다.",
            parameters=P(symbol=STR("원소기호 (예: Zn)"), prop=prop)),
        t.FunctionDeclaration(
            name="fill_value",
            description="CSV의 빈 칸에 값을 기록한다. CSV 열의 단위로 환산한 뒤 넣을 것.",
            parameters=P(symbol=STR("원소기호"), prop=prop,
                         value=t.Schema(type=NUM, description="CSV 열 단위로 환산된 값"),
                         source=STR("어느 도구에서 얻었는지"))),
        t.FunctionDeclaration(
            name="run_sisso",
            description="완성된 특징표로 SISSO를 돌려 수식과 오차를 얻는다.",
            parameters=t.Schema(type=OBJ, properties={
                "n_expansion": t.Schema(type=INT, description="rung (1~3)"),
                "n_term": t.Schema(type=INT, description="수식 항 개수 (1~3)"),
                "k": t.Schema(type=INT, description="SIS로 남길 후보 수")})),
    ])]


def demo():
    """모델 없이 도구만 돌려본다."""
    m = check_missing("AR_c")
    assert m["missing_elements"] == ["Zn", "Ca"], m
    col = inspect_column("AE")
    assert col["unit_in_csv"] == "Pauling Units" and col["max"] < 5, col
    hit = lookup_element("Zn", "AE")
    assert hit["unit"] == "eV" and abs(hit["value"] - 9.395) < 0.01, hit
    assert lookup_element("Zn", "AR_c")["value"] == 1.42
    assert lookup_element("Zn", "AR_c")["unit"] == "ang"
    print("조회 계열 OK")
    for k, v in [("check_missing('AR_c')", m), ("inspect_column('AE')", col),
                 ("lookup_element('Zn','AE')", hit)]:
        print(f"  {k:28s} -> {v}")


if __name__ == "__main__":
    demo()
