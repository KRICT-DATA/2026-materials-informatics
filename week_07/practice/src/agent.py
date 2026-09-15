"""에이전트 루프.

핵심은 아래 run() 안의 for문 하나다. 그 안에서
  - 무엇을 부를지    모델이 정한다
  - 몇 번 부를지     모델이 정한다
  - 언제 끝낼지      모델이 정한다
이 셋을 사람이 정하면 워크플로이고, 모델이 정하면 에이전트다.
"""
import os, pathlib, warnings
warnings.filterwarnings("ignore")
import tools

MODEL = "gemini-3.5-flash-lite"
MAX_STEPS = 8            # 무한루프 방지. 무료 티어 쿼터도 지켜준다.


def _load_key():
    """환경변수 -> .env -> Colab 보안 비밀 순으로 찾는다."""
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    for d in pathlib.Path(__file__).resolve().parents:
        f = d / ".env"
        if f.is_file():
            for line in f.read_text().splitlines():
                if line.strip().startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip().strip("'\"")
    try:
        from google.colab import userdata
        return userdata.get("GEMINI_API_KEY")
    except Exception:
        return None


def run(task, model=MODEL, max_steps=MAX_STEPS, verbose=True):
    """task를 주면 에이전트가 도구를 골라가며 수행한다. (최종답변, 호출기록)을 돌려준다."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=_load_key())
    config = types.GenerateContentConfig(tools=tools.declarations(), temperature=0)
    msgs = [types.Content(role="user", parts=[types.Part(text=task)])]
    trace = []

    for step in range(1, max_steps + 1):
        reply = client.models.generate_content(model=model, config=config, contents=msgs)
        parts = [p for c in reply.candidates for p in c.content.parts]
        calls = [p.function_call for p in parts if p.function_call]

        if not calls:                                  # ← 모델이 끝났다고 판단
            answer = (reply.text or "").strip()
            if verbose:
                print(f"\n[{step}] 종료\n{answer}")
            return answer, trace

        msgs.append(types.Content(role="model", parts=parts))
        for fc in calls:
            args = dict(fc.args)
            fn = tools.REGISTRY.get(fc.name)
            result = fn(**args) if fn else {"error": f"모르는 도구: {fc.name}"}
            trace.append({"step": step, "tool": fc.name, "args": args, "result": result})
            if verbose:
                print(f"[{step}] {fc.name}({args})\n      -> {result}")
            msgs.append(types.Content(role="user", parts=[
                types.Part.from_function_response(name=fc.name, response=result)]))

    if verbose:
        print(f"\n{max_steps}스텝 안에 끝내지 못했다.")
    return None, trace


# 실습에서 쓰는 과제문 ------------------------------------------------
TASK_FILL = """primary_feature.csv의 빈 칸을 채워라.

절차:
1. AR_c, CR, PE, IE, AE 각 물성에서 비어 있는 원소를 확인한다.
2. 채우기 전에 그 열의 단위와 기존 값 범위를 반드시 확인한다.
3. 조회한 값을 CSV 열의 단위로 맞춰 넣는다.

규칙:
- 도구가 돌려준 값만 쓴다. 네 지식으로 숫자를 만들지 않는다.
- 조회 결과가 null이면 채우지 말고 그 사실을 보고한다.
- 채운 값이 그 열의 기존 범위를 벗어나면 단위를 의심한다.

끝나면 채운 항목을 '물성/원소 = 값' 형식으로 한 줄씩 정리해라."""


def demo():
    """키가 있으면 AE 한 칸만 실제로 채워본다."""
    answer, trace = run(
        "AE(Allen 전기음성도) 열에서 비어 있는 원소를 찾아 채워라. "
        "채우기 전에 그 열의 단위와 값 범위를 확인하고, 단위가 다르면 환산해라. "
        "도구가 준 값만 쓴다.")
    used = [t["tool"] for t in trace]
    print(f"\n도구 호출 {len(trace)}회: {' -> '.join(used)}")
    assert "inspect_column" in used, f"열을 확인하지 않았다: {used}"
    assert "lookup_element" in used, f"조회하지 않았다: {used}"


if __name__ == "__main__":
    demo()
