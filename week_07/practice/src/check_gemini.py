"""Gemini 무료 티어가 이 실습을 버티는지 확인한다.

실행:  python src/check_gemini.py
사전:  pip install google-genai
       export GEMINI_API_KEY="발급받은키"

6단계를 순서대로 확인하고, 마지막에 붙여넣기 좋은 보고서를 찍는다.
어느 단계에서 멈추는지가 곧 진단이다.
"""
import os, sys, time, json, re, pathlib, warnings
warnings.filterwarnings("ignore")   # py3.9 EOL 등 잡음 제거 (Colab은 3.11+라 무관)

REPORT = []
def log(step, ok, detail=""):
    mark = "OK  " if ok else "FAIL"
    line = f"[{mark}] {step}" + (f" — {detail}" if detail else "")
    print(line); REPORT.append(line)
    return ok


# ── 1. SDK ────────────────────────────────────────────────────────────
try:
    from google import genai
    from google.genai import types
    import importlib.metadata as md
    log("1. SDK 임포트", True, f"google-genai {md.version('google-genai')}")
except Exception as e:
    log("1. SDK 임포트", False, f"{type(e).__name__}: {e}")
    print("\n  pip install google-genai"); sys.exit(1)

# ── 2. 키 ─────────────────────────────────────────────────────────────
def load_dotenv():
    """레포 루트의 .env를 환경변수로 올린다. 이미 있는 값은 덮지 않는다."""
    for d in [pathlib.Path(__file__).resolve()] + list(pathlib.Path(__file__).resolve().parents):
        f = (d if d.is_dir() else d.parent) / ".env"
        if f.is_file():
            for line in f.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))
            return f
    return None

_env = load_dotenv()
try:                       # Colab이면 보안 비밀에서 가져온다
    from google.colab import userdata
    os.environ.setdefault("GEMINI_API_KEY", userdata.get("GEMINI_API_KEY"))
except Exception:
    pass

KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
if not log("2. API 키", bool(KEY),
           (f"…{KEY[-4:]}" + (f" ({_env})" if _env else " (환경변수)")) if KEY else "찾지 못함"):
    print("\n  레포 루트에 .env 파일을 만든다:")
    print('    echo \'GEMINI_API_KEY=AIza...\' > .env')
    sys.exit(1)
client = genai.Client(api_key=KEY)

# ── 3. 이 키로 쓸 수 있는 모델 ────────────────────────────────────────
# 문서를 믿지 말고 API에 직접 묻는다. 무료 티어는 계정마다 다르다.
ALL = []
try:
    ALL = sorted(m.name.replace("models/", "") for m in client.models.list())
    log("3. 모델 목록", True, f"{len(ALL)}개")
    for n in ALL:
        print(f"       · {n}")
except Exception as e:
    log("3. 모델 목록", False, f"{type(e).__name__}: {str(e)[:120]}")

# preview·exp·omni·tts·image·embedding 계열은 무료 쿼터가 없거나 용도가 다르다.
BAD = ("preview", "exp", "omni", "thinking", "image", "tts", "audio",
       "embedding", "aqa", "learnlm", "gemma", "vision", "live", "native")
def usable(n):
    return n.startswith("gemini") and not any(b in n for b in BAD)

def rank(n):                      # flash-lite → flash → pro, 버전 높은 순
    fam = 0 if "flash-lite" in n else 1 if "flash" in n else 2
    ver = re.findall(r"\d+\.\d+", n)
    return (fam, -float(ver[0]) if ver else 0, n)

CANDIDATES = sorted([n for n in ALL if usable(n)], key=rank) or ["gemini-2.5-flash"]
REPORT.append(f"       후보 순서: {', '.join(CANDIDATES[:5])}")
print(f"\n       시도할 후보: {', '.join(CANDIDATES[:5])}\n")

# ── 4. 실제로 응답하는 모델 찾기 ──────────────────────────────────────
# 429 RESOURCE_EXHAUSTED = 그 모델에 무료 쿼터가 없다는 뜻. 다음 후보로 넘어간다.
MODEL, tried = None, []
for cand in CANDIDATES[:8]:
    try:
        t0 = time.time()
        r = client.models.generate_content(model=cand, contents="Reply with one word: ready")
        MODEL = cand
        log("4. 기본 생성", True, f"{cand} · {time.time()-t0:.1f}s · {r.text.strip()[:20]!r}")
        break
    except Exception as e:
        code = "429" if "429" in str(e) else type(e).__name__
        tried.append(f"{cand}({code})")
        print(f"       × {cand}: {code}")
if MODEL is None:
    log("4. 기본 생성", False, f"후보 전부 실패 — {', '.join(tried)}")
    print("\n  키 자체의 일일 한도일 수 있다. 24시간 후 재시도하거나 새 키를 발급한다.")
    sys.exit(1)
if tried:
    REPORT.append(f"       건너뛴 모델: {', '.join(tried)}")

# ── 5. 함수 호출 1회 (실습의 최소 조건) ───────────────────────────────
# 실제 실습에서 쓸 도구와 같은 모양으로 시험한다.
LOOKUP = types.FunctionDeclaration(
    name="lookup_element",
    description="원소의 물성값을 외부 레퍼런스에서 조회한다. 없으면 null을 반환한다.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "symbol": types.Schema(type=types.Type.STRING, description="원소기호 (예: Zn)"),
            "prop":   types.Schema(type=types.Type.STRING, enum=["AR_c", "CR", "PE", "IE", "AE"],
                description=("물성 약어. AR_c=계산 원자반지름, CR=공유결합반지름, "
                             "PE=Pauling 전기음성도, IE=1차 이온화에너지, "
                             "AE=Allen 전기음성도. PE와 AE는 서로 다른 물성이다.")),
        },
        required=["symbol", "prop"],
    ),
)
TOOLS = [types.Tool(function_declarations=[LOOKUP])]
CFG = types.GenerateContentConfig(tools=TOOLS, temperature=0)

try:
    t0 = time.time()
    r = client.models.generate_content(
        model=MODEL, config=CFG,
        contents="primary_feature.csv에서 Zn의 AR_c가 비어 있다. 값을 조회해라.")
    calls = [p.function_call for c in r.candidates for p in c.content.parts if p.function_call]
    ok = bool(calls) and calls[0].name == "lookup_element"
    log("5. 함수 호출 1회", ok,
        f"{time.time()-t0:.1f}s · {calls[0].name}({dict(calls[0].args)})" if calls else "도구를 부르지 않음")
except Exception as e:
    log("5. 함수 호출 1회", False, f"{type(e).__name__}: {str(e)[:150]}")

# ── 6. 다단계 루프 (에이전트의 실체) ──────────────────────────────────
# 값을 raw 단위로 돌려줘서, 모델이 단위 불일치를 알아채고 재조회하는지 본다. ← (B)안
FAKE_DB = {("Zn", "AE"): {"value": 9.395, "unit": "eV", "source": "mendeleev.en_allen"},
           ("Te", "AE"): {"value": 12.76, "unit": "eV", "source": "mendeleev.en_allen"}}

def run_tool(name, args):
    if name == "lookup_element":
        hit = FAKE_DB.get((args.get("symbol"), args.get("prop")))
        return hit or {"value": None, "note": "이 출처에 값이 없다"}
    return {"error": f"모르는 도구: {name}"}

msgs = [types.Content(role="user", parts=[types.Part(text=(
    "CSV의 AE 열(Allen 전기음성도)에 Zn 값이 비어 있다. 이 열의 기존 값들은 "
    "1.0~2.6 범위이고 Pauling 척도로 환산되어 있다. AE를 조회해서 이 열에 넣을 숫자를 정해라. "
    "규칙: 도구가 돌려준 값만 쓴다. 네 지식으로 숫자를 만들지 않는다. "
    "도구 값의 단위가 열의 척도와 다르면 환산한 뒤 넣는다. 마지막 줄에 "
    "'최종값: <숫자>' 형식으로만 답해라."))]) ]
steps = 0
try:
    t0 = time.time()
    for steps in range(1, 7):
        r = client.models.generate_content(model=MODEL, config=CFG, contents=msgs)
        parts = [p for c in r.candidates for p in c.content.parts]
        calls = [p.function_call for p in parts if p.function_call]
        if not calls:
            final = (r.text or "").strip().replace("\n", " ")
            m = re.search(r"최종값\s*[:：]\s*(-?\d+\.?\d*)", final)   # 결론만 본다
            nums = [float(m.group(1))] if m else []
            correct = any(abs(v - 1.588) < 0.02 for v in nums)      # 9.395 eV x 0.169
            raw     = any(abs(v - 9.395) < 0.02 for v in nums)      # 환산 안 함
            log("6. 다단계 루프", correct,
                f"{steps}스텝 · {time.time()-t0:.1f}s · " +
                ("정답 1.588 도달" if correct else
                 "환산 누락 (9.395 그대로)" if raw else "엉뚱한 값"))
            REPORT.append(f"       최종 응답: {final[:150]!r}")
            break
        msgs.append(types.Content(role="model", parts=parts))
        for fc in calls:
            out = run_tool(fc.name, dict(fc.args))
            print(f"       └ {fc.name}({dict(fc.args)}) -> {out}")
            msgs.append(types.Content(role="user", parts=[types.Part.from_function_response(
                name=fc.name, response=out)]))
    else:
        log("6. 다단계 루프", False, "6스텝 내 종료 안 됨 (무한루프 경향)")
except Exception as e:
    log("6. 다단계 루프", False, f"{type(e).__name__}: {str(e)[:150]}")

# ── 보고서 ────────────────────────────────────────────────────────────
print("\n" + "=" * 68)
print("붙여넣기용 보고서")
print("=" * 68)
print(f"확인일시 : (실행 시각 기록)")
print(f"모델     : {MODEL}")
for line in REPORT:
    print(line)
print("=" * 68)
