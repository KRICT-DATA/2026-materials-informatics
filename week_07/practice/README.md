# 7주차 실습 · 소재 물성 예측을 위한 해석 가능한 구분자 학습

## 데이터 흐름

```
data/primary_feature_blanked.csv   (빈 칸이 있는 원소 물성표)
          │
          ├── 실습 1: 에이전트가 빈 칸을 채움
          ↓
data/primary_feature_filled.csv    (실습 1 결과)
          │
          ├── 조성가중 평균 → 12개 특징
          ↓
data/1_training_data/  (3성분계 112점)  →  TorchSISSO  →  수식
          ↓
data/validation_cbm.csv  (4성분계 30점)  →  예측 검증
```

## Gemini API 키 발급 (무료, 신용카드 불필요)

1. [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey) 에 구글 계정으로 로그인
2. **Create API key** 클릭. 프로젝트를 고르라고 하면 아무거나 선택 (없으면 자동 생성)
3. `AIza…`로 시작하는 문자열이 키입니다. 복사해 둡니다
4. Colab에서 노트북을 연 뒤, 왼쪽 열쇠 아이콘(보안 비밀) → 이름 `GEMINI_API_KEY`, 값에 키를 붙여넣고 **노트북 액세스**를 켭니다

키는 비밀번호와 같습니다. 노트북 셀이나 공개된 곳에 직접 붙여넣지 마세요.

로컬에서 돌릴 때는 이 폴더에 `.env` 파일을 만들고 `GEMINI_API_KEY=AIza...` 한 줄을 넣습니다. `.env.example`을 복사해 쓰면 됩니다.

## Colab에서 실행

1. 아래에 있는 절차에 따라 Gemini API 키를 발급받고 복사해 둡니다 (실습 1만 필요).
2. 노트북 링크를 엽니다. Colab이 GitHub에서 사본을 가져오므로 수정해도 원본은 바뀌지 않습니다.
  - [실습 1](https://colab.research.google.com/github/KRICT-DATA/2026-materials-informatics/blob/main/week_07/practice/notebooks/01_fill_features.ipynb)
  - [실습 2](https://colab.research.google.com/github/KRICT-DATA/2026-materials-informatics/blob/main/week_07/practice/notebooks/02_sisso_predict.ipynb)
3. 왼쪽 열쇠 아이콘(보안 비밀)에 이름 `GEMINI_API_KEY`, 값에 키를 넣고 **노트북 액세스**를 켭니다.
4. 첫 셀을 실행합니다. 패키지 설치와 자료 내려받기를 하며 1분 안팎 걸립니다. "Google에서 작성하지 않았습니다" 경고는 "무시하고 실행"을 누릅니다. 끝에 `준비 완료 · /content/ust/week_07/practice`가 찍히면 됩니다.
5. 두 번째 셀에서 `키 확인: 찾음`이 나오는지 봅니다. "못 찾음"이면 3번의 노트북 액세스 스위치를 확인합니다.
6. 나머지 셀을 위에서부터 순서대로 실행합니다. 실습 1의 3부에서 오답이 나오는 것은 정상이고, 4부에서 값을 하나 바꾸면 정답이 나옵니다.

막히면 런타임 메뉴의 "런타임 다시 시작" 후 첫 셀부터 다시 실행합니다.