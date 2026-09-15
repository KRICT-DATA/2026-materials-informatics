# 7주차 · 소재 물성 예측을 위한 해석 가능한 구분자 학습

UST 소재정보학 2026-2H / 유수현 (KRICT) / 이론 2h + 실습 1h

## 산출물

| 경로 | 형식 | 용도 |
|---|---|---|
| `slides/deck-v1.pptx` | PPTX 62장 | **주 발표자료.** 0~3부 한 파일. `slides/build_deck.py`로 생성 |
| `slides/render/deck-v1.pdf` | PDF | 위 덱의 렌더본 (장별 PNG는 `slides/render/`) |
| `slides/index.html` | 단일 HTML | 초기 HTML 덱. 현재는 pptx가 정본 |
| `notebooks/01_fill_features.ipynb` | Colab | 실습 1 — 결측 채우기 (에이전트) |
| `notebooks/02_sisso_predict.ipynb` | Colab | 실습 2 — 4성분계 CBM 예측 |
| `homework/` | (비어 있음) | 과제 (평가 50%). 미확정 — `docs/BACKLOG.md` P2 |

## 데이터 흐름

    primary_feature_blanked.csv   (구멍 뚫린 배포본)
              │
              ├── 실습 1: 에이전트가 3개 출처 교차검증으로 채움
              ↓
    primary_feature_filled.csv    (학생 산출물)
              │
              ├── 조성가중 평균 → 12개 특징
              ↓
    train.dat (112점, 3성분계)  →  TorchSISSO  →  수식
              ↓
    validation_cbm.csv (30점, 4성분계)  →  예측 검증

## 실행 환경

- Google Colab 무료 티어 (CPU). GPU 불필요
- `pip install TorchSisso mendeleev pymatgen periodictable google-genai`
- Gemini API 키 (무료 티어, 신용카드 불필요) — 학생 각자 발급

## 검증 완료 사항 (2026-08-12, 2026-09-03 재확인)

- TorchSisso 0.1.8: `n_expansion=3, k=100` → **0.42초**, RMSE 0.067 (CPU)
- 3개 출처 교차검증 성립: AR_c는 pymatgen만 일치, CR은 2곳 일치, IE/AE는 단위 변환 필요
- 학습셋 12특징의 실효 rank = 4 (시리즈당 1 × 4시리즈)
- 노트북 2종 처음부터 끝까지 실행 통과. 실습 1 정답 6/6, 실습 2 학습 RMSE 0.095 → 4성분계 0.340
- 셀별 실행 기록과 검토는 `docs/rehearsal.md` (강사용)
