# 리뷰 분석 모델.

상품 리뷰의 이미지와 텍스트를 분석하여 다음 항목들을 검증하는 AI 모델입니다.

## 주요 기능

1. **상품 일치성 검증**: 리뷰 이미지가 해당 상품과 일치하는지 확인
2. **신뢰도 점수**: 분석 결과의 신뢰성을 백분율로 표현
3. **감정 분석**: 리뷰의 긍정/부정 평가 판단

## 설치 방법

```bash
pip install -r requirements.txt
```

## 사용 방법

### 웹 인터페이스 실행
```bash
streamlit run app.py
```

### API 서버 실행
```bash
python api_server.py
```

## 모델 구조

- **Vision-Language Model**: CLIP 기반 이미지-텍스트 매칭
- **감정 분석**: BERT 기반 텍스트 감정 분석
- **신뢰도 계산**: 다양한 지표를 종합한 신뢰도 점수

## API 엔드포인트

- `POST /analyze_review`: 리뷰 분석
- `GET /health`: 서버 상태 확인 