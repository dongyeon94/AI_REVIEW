import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from review_analyzer import ReviewAnalyzer
import tempfile
import os
from PIL import Image
import time

# 페이지 설정
st.set_page_config(
    page_title="리뷰 분석 시스템",
    page_icon="🔍",
    layout="wide"
)

# 제목
st.title("🔍 상품 리뷰 분석 시스템")
st.markdown("---")

# 사이드바 - 모델 초기화
@st.cache_resource
def load_analyzer():
    with st.spinner("AI 모델을 로딩 중입니다..."):
        return ReviewAnalyzer()

analyzer = load_analyzer()

# 메인 컨텐츠
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 리뷰 정보 입력")
    
    # 상품 정보
    product_name = st.text_input("상품명", placeholder="예: 삼성 갤럭시 S23")
    product_description = st.text_area(
        "상품 설명", 
        placeholder="상품에 대한 간단한 설명을 입력하세요...",
        height=100
    )
    
    # 리뷰 텍스트
    review_text = st.text_area(
        "리뷰 텍스트",
        placeholder="리뷰 내용을 입력하세요...",
        height=150
    )
    
    # 이미지 업로드
    uploaded_file = st.file_uploader(
        "리뷰 이미지 업로드",
        type=['png', 'jpg', 'jpeg'],
        help="리뷰와 관련된 이미지를 업로드하세요"
    )

with col2:
    st.subheader("📊 분석 결과")
    
    if st.button("🔍 분석 시작", type="primary", use_container_width=True):
        if not product_name or not review_text:
            st.error("상품명과 리뷰 텍스트를 입력해주세요.")
        else:
            with st.spinner("리뷰를 분석하고 있습니다..."):
                # 임시 파일로 이미지 저장
                if uploaded_file:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        image_path = tmp_file.name
                else:
                    # 이미지가 없는 경우 기본 이미지 사용
                    image_path = "default_image.jpg"
                    if not os.path.exists(image_path):
                        # 기본 이미지 생성
                        default_img = Image.new('RGB', (300, 300), color='lightgray')
                        default_img.save(image_path)
                
                try:
                    # 분석 실행
                    result = analyzer.analyze_review(
                        product_name=product_name,
                        product_description=product_description,
                        review_text=review_text,
                        review_image_path=image_path
                    )
                    
                    # 결과 표시
                    if "error" not in result:
                        display_results(result)
                    else:
                        st.error(f"분석 중 오류가 발생했습니다: {result['error']}")
                        
                except Exception as e:
                    st.error(f"분석 중 오류가 발생했습니다: {str(e)}")
                finally:
                    # 임시 파일 정리
                    if uploaded_file and os.path.exists(image_path):
                        os.unlink(image_path)

def display_results(result):
    """분석 결과를 시각적으로 표시"""
    
    # 전체 평가
    st.markdown("### 📋 전체 평가")
    st.info(result["overall_assessment"])
    
    # 메트릭 표시
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "상품 일치도",
            f"{result['product_match']['score']:.1%}",
            delta="✅ 일치" if result['product_match']['is_matched'] else "❌ 불일치"
        )
        st.caption(result['product_match']['description'])
    
    with col2:
        sentiment_emoji = "😊" if result['sentiment']['label'] == 'positive' else "😞"
        st.metric(
            "감정 분석",
            f"{result['sentiment']['score']:.1%}",
            delta=f"{sentiment_emoji} {result['sentiment']['label']}"
        )
        st.caption(result['sentiment']['description'])
    
    with col3:
        confidence_emoji = "🟢" if result['confidence']['score'] > 0.7 else "🟡" if result['confidence']['score'] > 0.4 else "🔴"
        st.metric(
            "신뢰도",
            f"{result['confidence']['score']:.1%}",
            delta=f"{confidence_emoji} {result['confidence']['level']}"
        )
    
    # 상세 분석 차트
    st.markdown("### 📈 상세 분석")
    
    # 점수 비교 차트
    scores_data = {
        '항목': ['상품 일치도', '감정 점수', '신뢰도'],
        '점수': [
            result['product_match']['score'],
            result['sentiment']['score'],
            result['confidence']['score']
        ]
    }
    
    df_scores = pd.DataFrame(scores_data)
    
    fig = px.bar(
        df_scores, 
        x='항목', 
        y='점수',
        color='점수',
        color_continuous_scale='RdYlGn',
        title="분석 항목별 점수"
    )
    fig.update_layout(yaxis_tickformat='.1%')
    st.plotly_chart(fig, use_container_width=True)
    
    # 레이더 차트
    fig_radar = go.Figure()
    
    fig_radar.add_trace(go.Scatterpolar(
        r=[result['product_match']['score'], result['sentiment']['score'], result['confidence']['score']],
        theta=['상품 일치도', '감정 분석', '신뢰도'],
        fill='toself',
        name='분석 결과'
    ))
    
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        showlegend=False,
        title="종합 분석 결과"
    )
    
    st.plotly_chart(fig_radar, use_container_width=True)
    
    # 권장사항
    st.markdown("### 💡 권장사항")
    
    recommendations = []
    
    if result['product_match']['score'] < 0.6:
        recommendations.append("⚠️ **상품 일치성**: 리뷰 이미지가 상품과 일치하지 않습니다. 이미지 검증이 필요합니다.")
    
    if result['confidence']['score'] < 0.5:
        recommendations.append("⚠️ **신뢰도**: 분석 신뢰도가 낮습니다. 더 자세한 리뷰 텍스트나 명확한 이미지를 제공해주세요.")
    
    if result['sentiment']['score'] < 0.3:
        recommendations.append("📝 **감정 분석**: 부정적인 리뷰로 분류되었습니다. 고객 서비스 팀의 검토가 필요할 수 있습니다.")
    
    if not recommendations:
        recommendations.append("✅ 모든 항목이 양호한 수준입니다.")
    
    for rec in recommendations:
        st.write(rec)

# 하단 정보
st.markdown("---")
st.markdown("""
### 📚 사용 가이드

1. **상품명**: 분석할 상품의 정확한 이름을 입력하세요
2. **상품 설명**: 상품의 주요 특징이나 설명을 입력하세요
3. **리뷰 텍스트**: 고객이 작성한 리뷰 내용을 입력하세요
4. **리뷰 이미지**: 상품과 관련된 이미지를 업로드하세요

### 🔍 분석 항목

- **상품 일치성**: 이미지가 해당 상품과 일치하는지 검증
- **감정 분석**: 리뷰의 긍정/부정 평가
- **신뢰도**: 분석 결과의 신뢰성을 백분율로 표현
""") 