#!/bin/bash

# 리뷰 분석 시스템 실행 스크립트

echo "🔍 리뷰 분석 시스템"
echo "=================="

# Python 환경 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3가 설치되어 있지 않습니다."
    exit 1
fi

# 가상환경 생성 (선택사항)
if [ ! -d "venv" ]; then
    echo "📦 가상환경을 생성합니다..."
    python3 -m venv venv
fi

# 가상환경 활성화
echo "🔧 가상환경을 활성화합니다..."
source venv/bin/activate

# 의존성 설치
echo "📚 필요한 패키지를 설치합니다..."
pip install -r requirements.txt

echo ""
echo "🚀 실행 옵션을 선택하세요:"
echo "1. 웹 인터페이스 실행 (Streamlit)"
echo "2. API 서버 실행 (FastAPI)"
echo "3. 테스트 실행"
echo "4. API 사용 예제 실행"
echo "5. 종료"

read -p "선택하세요 (1-5): " choice

case $choice in
    1)
        echo "🌐 웹 인터페이스를 시작합니다..."
        echo "브라우저에서 http://localhost:8501 을 열어주세요."
        streamlit run app.py
        ;;
    2)
        echo "🔌 API 서버를 시작합니다..."
        echo "API 문서: http://localhost:8000/docs"
        echo "서버 상태: http://localhost:8000/health"
        python api_server.py
        ;;
    3)
        echo "🧪 테스트를 실행합니다..."
        python test_analyzer.py
        ;;
    4)
        echo "📡 API 사용 예제를 실행합니다..."
        echo "먼저 API 서버를 실행해야 합니다 (옵션 2)."
        python example_usage.py
        ;;
    5)
        echo "👋 종료합니다."
        exit 0
        ;;
    *)
        echo "❌ 잘못된 선택입니다."
        exit 1
        ;;
esac 