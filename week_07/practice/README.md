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