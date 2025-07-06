#!/usr/bin/env python3
"""
리뷰 분석 API 사용 예제
"""

import requests
import json
import time
from PIL import Image
import io

# API 서버 URL
API_BASE_URL = "http://localhost:8000"

def test_api_health():
    """API 서버 상태 확인"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API 서버가 정상적으로 실행 중입니다.")
            return True
        else:
            print("❌ API 서버에 연결할 수 없습니다.")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        return False

def test_json_api():
    """JSON API 테스트"""
    print("\n📡 JSON API 테스트")
    print("-" * 30)
    
    # 테스트 데이터
    test_data = {
        "product_name": "애플 맥북 프로",
        "product_description": "애플의 최신 노트북, M2 칩 탑재로 고성능",
        "review_text": "정말 빠르고 안정적입니다! 배터리도 오래가고 디자인도 예뻐요. 개발 작업에 최적화되어 있어서 만족합니다.",
        "image_url": None  # 이미지 없이 테스트
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyze_review_json",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 분석 완료!")
            print(f"📱 상품: {test_data['product_name']}")
            print(f"🎯 상품 일치도: {result['product_match']['score']:.1%}")
            print(f"😊 감정 분석: {result['sentiment']['label']} ({result['sentiment']['score']:.1%})")
            print(f"🔍 신뢰도: {result['confidence']['score']:.1%}")
            print(f"📋 전체 평가: {result['overall_assessment']}")
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

def test_form_api():
    """Form API 테스트 (이미지 업로드)"""
    print("\n📤 Form API 테스트 (이미지 업로드)")
    print("-" * 40)
    
    # 테스트 이미지 생성
    test_image = Image.new('RGB', (300, 300), color='lightblue')
    img_byte_arr = io.BytesIO()
    test_image.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    
    # Form 데이터 준비
    files = {
        'image': ('test_image.jpg', img_byte_arr, 'image/jpeg')
    }
    
    data = {
        'product_name': '삼성 갤럭시 워치',
        'product_description': '삼성 스마트워치, 건강 모니터링 기능',
        'review_text': '배터리가 생각보다 오래가고 운동 추적 기능이 정확해요. 하지만 가격이 조금 비싸네요.'
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyze_review",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 분석 완료!")
            print(f"📱 상품: {data['product_name']}")
            print(f"🎯 상품 일치도: {result['product_match']['score']:.1%}")
            print(f"😊 감정 분석: {result['sentiment']['label']} ({result['sentiment']['score']:.1%})")
            print(f"🔍 신뢰도: {result['confidence']['score']:.1%}")
            print(f"📋 전체 평가: {result['overall_assessment']}")
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

def batch_analysis_example():
    """배치 분석 예제"""
    print("\n📊 배치 분석 예제")
    print("-" * 25)
    
    # 여러 리뷰 데이터
    reviews = [
        {
            "product_name": "다이슨 공기청정기",
            "product_description": "다이슨 퓨리파이어 공기청정기",
            "review_text": "공기질이 확실히 좋아졌어요! 소음은 조금 있지만 효과는 만족스럽습니다.",
            "expected": "positive"
        },
        {
            "product_name": "LG 냉장고",
            "product_description": "LG 스마트 냉장고",
            "review_text": "배송이 늦었고 제품에 흠집이 있었습니다. 고객서비스도 별로예요.",
            "expected": "negative"
        },
        {
            "product_name": "나이키 운동화",
            "product_description": "나이키 에어맥스 운동화",
            "review_text": "사이즈가 예상보다 작게 나왔지만 착용감은 괜찮습니다. 가격 대비는 보통이에요.",
            "expected": "neutral"
        }
    ]
    
    results = []
    
    for i, review in enumerate(reviews, 1):
        print(f"\n🔍 분석 {i}/{len(reviews)}: {review['product_name']}")
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/analyze_review_json",
                json=review
            )
            
            if response.status_code == 200:
                result = response.json()
                results.append({
                    "product": review['product_name'],
                    "expected": review['expected'],
                    "actual": result['sentiment']['label'],
                    "confidence": result['confidence']['score'],
                    "match_score": result['product_match']['score']
                })
                
                print(f"   감정: {result['sentiment']['label']} (예상: {review['expected']})")
                print(f"   신뢰도: {result['confidence']['score']:.1%}")
                
            else:
                print(f"   ❌ 분석 실패: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 오류: {str(e)}")
        
        # API 호출 간격 조절
        time.sleep(1)
    
    # 결과 요약
    print(f"\n📈 배치 분석 결과 요약:")
    print("-" * 30)
    
    correct = sum(1 for r in results if r['expected'] == r['actual'])
    accuracy = correct / len(results) if results else 0
    
    print(f"정확도: {accuracy:.1%} ({correct}/{len(results)})")
    
    for result in results:
        status = "✅" if result['expected'] == result['actual'] else "❌"
        print(f"{status} {result['product']}: {result['actual']} (예상: {result['expected']})")

def get_model_info():
    """모델 정보 조회"""
    print("\nℹ️ 모델 정보")
    print("-" * 15)
    
    try:
        response = requests.get(f"{API_BASE_URL}/model_info")
        if response.status_code == 200:
            info = response.json()
            print(f"모델명: {info['model_name']}")
            print(f"지원 언어: {', '.join(info['supported_languages'])}")
            print(f"이미지 형식: {', '.join(info['image_formats'])}")
            print("기능:")
            for feature in info['features']:
                print(f"  - {feature}")
        else:
            print("❌ 모델 정보 조회 실패")
            
    except Exception as e:
        print(f"❌ 오류: {str(e)}")

def main():
    """메인 함수"""
    print("🚀 리뷰 분석 API 사용 예제")
    print("=" * 40)
    
    # API 서버 상태 확인
    if not test_api_health():
        print("\n💡 API 서버를 시작하려면 다음 명령어를 실행하세요:")
        print("python api_server.py")
        return
    
    # 다양한 테스트 실행
    test_json_api()
    test_form_api()
    batch_analysis_example()
    get_model_info()
    
    print("\n🎉 모든 테스트 완료!")

if __name__ == "__main__":
    main() 