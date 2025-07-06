#!/usr/bin/env python3
"""
리뷰 분석 모델 테스트 스크립트
"""

import os
import tempfile
from PIL import Image
import numpy as np
from review_analyzer import ReviewAnalyzer

def create_test_image(text="Test Product", size=(300, 300)):
    """테스트용 이미지 생성"""
    img = Image.new('RGB', size, color='white')
    return img

def test_analyzer():
    """분석기 테스트"""
    print("🔍 리뷰 분석 모델 테스트 시작")
    print("=" * 50)
    
    # 분석기 초기화
    print("📦 모델 로딩 중...")
    analyzer = ReviewAnalyzer()
    print("✅ 모델 로딩 완료!")
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "긍정적인 스마트폰 리뷰",
            "product_name": "삼성 갤럭시 S23",
            "product_description": "삼성의 최신 스마트폰, 고성능 카메라와 긴 배터리 수명",
            "review_text": "정말 만족스러운 구매였습니다! 카메라 품질이 정말 좋고 배터리도 오래갑니다. 디자인도 예쁘고 사용하기 편해요.",
            "expected_sentiment": "positive"
        },
        {
            "name": "부정적인 전자제품 리뷰",
            "product_name": "LG 냉장고",
            "product_description": "LG 스마트 냉장고, 에너지 효율적이고 실용적",
            "review_text": "배송이 너무 늦었고 제품에 흠집이 있었습니다. 소음도 심하고 전반적으로 실망스러워요.",
            "expected_sentiment": "negative"
        },
        {
            "name": "중립적인 의류 리뷰",
            "product_name": "나이키 운동화",
            "product_description": "나이키 에어맥스 운동화, 편안한 착용감",
            "review_text": "사이즈가 예상보다 작게 나왔지만 착용감은 괜찮습니다. 가격 대비 만족도는 보통이에요.",
            "expected_sentiment": "neutral"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 테스트 케이스 {i}: {test_case['name']}")
        print("-" * 30)
        
        # 테스트 이미지 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            test_img = create_test_image(test_case['product_name'])
            test_img.save(tmp_file.name)
            image_path = tmp_file.name
        
        try:
            # 분석 실행
            result = analyzer.analyze_review(
                product_name=test_case['product_name'],
                product_description=test_case['product_description'],
                review_text=test_case['review_text'],
                review_image_path=image_path
            )
            
            # 결과 출력
            print(f"📱 상품: {test_case['product_name']}")
            print(f"📝 리뷰: {test_case['review_text'][:50]}...")
            print(f"🎯 상품 일치도: {result['product_match']['score']:.1%}")
            print(f"😊 감정 분석: {result['sentiment']['label']} ({result['sentiment']['score']:.1%})")
            print(f"🔍 신뢰도: {result['confidence']['score']:.1%} ({result['confidence']['level']})")
            print(f"📋 전체 평가: {result['overall_assessment']}")
            
            # 예상 결과와 비교
            if result['sentiment']['label'] == test_case['expected_sentiment']:
                print("✅ 감정 분석 결과 일치!")
            else:
                print(f"⚠️ 감정 분석 결과 불일치 (예상: {test_case['expected_sentiment']})")
                
        except Exception as e:
            print(f"❌ 테스트 실패: {str(e)}")
        finally:
            # 임시 파일 정리
            if os.path.exists(image_path):
                os.unlink(image_path)
    
    print("\n" + "=" * 50)
    print("🎉 테스트 완료!")

def test_batch_analysis():
    """배치 분석 테스트"""
    print("\n📊 배치 분석 테스트")
    print("=" * 30)
    
    analyzer = ReviewAnalyzer()
    
    # 여러 리뷰 데이터
    reviews = [
        {
            "product": "애플 아이폰 15",
            "text": "카메라가 정말 좋아요! 배터리도 오래가고 전반적으로 만족합니다.",
            "sentiment": "positive"
        },
        {
            "product": "다이슨 공기청정기",
            "text": "가격이 비싸지만 성능은 좋습니다. 소음이 조금 있지만 효과는 확실해요.",
            "sentiment": "positive"
        },
        {
            "product": "삼성 TV",
            "text": "화질은 좋은데 리모컨이 복잡하고 설정이 어려워요. 사용법을 익히기 힘들어요.",
            "sentiment": "negative"
        }
    ]
    
    results = []
    
    for review in reviews:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            test_img = create_test_image(review['product'])
            test_img.save(tmp_file.name)
            
            try:
                result = analyzer.analyze_review(
                    product_name=review['product'],
                    product_description=f"{review['product']} 제품",
                    review_text=review['text'],
                    review_image_path=tmp_file.name
                )
                
                results.append({
                    "product": review['product'],
                    "expected": review['sentiment'],
                    "actual": result['sentiment']['label'],
                    "confidence": result['confidence']['score'],
                    "match_score": result['product_match']['score']
                })
                
            finally:
                os.unlink(tmp_file.name)
    
    # 결과 요약
    print("\n📈 배치 분석 결과:")
    print("-" * 20)
    
    correct_predictions = 0
    total_confidence = 0
    
    for result in results:
        print(f"📱 {result['product']}")
        print(f"   예상: {result['expected']}, 실제: {result['actual']}")
        print(f"   신뢰도: {result['confidence']:.1%}, 일치도: {result['match_score']:.1%}")
        
        if result['expected'] == result['actual']:
            correct_predictions += 1
            print("   ✅ 정확")
        else:
            print("   ❌ 오류")
        
        total_confidence += result['confidence']
        print()
    
    accuracy = correct_predictions / len(results)
    avg_confidence = total_confidence / len(results)
    
    print(f"🎯 정확도: {accuracy:.1%} ({correct_predictions}/{len(results)})")
    print(f"🔍 평균 신뢰도: {avg_confidence:.1%}")

if __name__ == "__main__":
    test_analyzer()
    test_batch_analysis() 