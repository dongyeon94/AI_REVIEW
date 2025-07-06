from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import tempfile
import os
from PIL import Image
import json
from review_analyzer import ReviewAnalyzer
from typing import Optional
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="리뷰 분석 API",
    description="상품 리뷰의 이미지와 텍스트를 분석하는 AI API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 분석기 인스턴스
analyzer = None

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 분석기 초기화"""
    global analyzer
    logger.info("리뷰 분석 모델을 로딩 중입니다...")
    analyzer = ReviewAnalyzer()
    logger.info("모델 로딩 완료!")

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "리뷰 분석 API 서버",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/analyze_review",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {
        "status": "healthy",
        "model_loaded": analyzer is not None
    }

@app.post("/analyze_review")
async def analyze_review(
    product_name: str = Form(..., description="상품명"),
    product_description: str = Form("", description="상품 설명"),
    review_text: str = Form(..., description="리뷰 텍스트"),
    image: Optional[UploadFile] = File(None, description="리뷰 이미지")
):
    """
    리뷰 분석 API
    
    - **product_name**: 분석할 상품명
    - **product_description**: 상품 설명 (선택사항)
    - **review_text**: 리뷰 텍스트
    - **image**: 리뷰 이미지 파일 (선택사항)
    
    Returns:
        분석 결과 JSON
    """
    try:
        if not analyzer:
            raise HTTPException(status_code=503, detail="분석 모델이 로딩되지 않았습니다.")
        
        # 이미지 처리
        image_path = None
        if image:
            # 지원하는 이미지 형식 확인
            if not image.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다.")
            
            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                content = await image.read()
                tmp_file.write(content)
                image_path = tmp_file.name
        else:
            # 기본 이미지 생성
            image_path = "default_image.jpg"
            if not os.path.exists(image_path):
                default_img = Image.new('RGB', (300, 300), color='lightgray')
                default_img.save(image_path)
        
        # 분석 실행
        result = analyzer.analyze_review(
            product_name=product_name,
            product_description=product_description,
            review_text=review_text,
            review_image_path=image_path
        )
        
        # 임시 파일 정리
        if image and os.path.exists(image_path):
            os.unlink(image_path)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"분석 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 중 오류가 발생했습니다: {str(e)}")

@app.post("/analyze_review_json")
async def analyze_review_json(
    product_name: str,
    product_description: str = "",
    review_text: str = "",
    image_url: Optional[str] = None
):
    """
    JSON 형태로 리뷰 분석 (이미지 URL 사용)
    
    - **product_name**: 분석할 상품명
    - **product_description**: 상품 설명 (선택사항)
    - **review_text**: 리뷰 텍스트
    - **image_url**: 이미지 URL (선택사항)
    """
    try:
        if not analyzer:
            raise HTTPException(status_code=503, detail="분석 모델이 로딩되지 않았습니다.")
        
        # 이미지 처리 (URL에서 다운로드)
        image_path = None
        if image_url:
            import requests
            try:
                response = requests.get(image_url, timeout=10)
                response.raise_for_status()
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    tmp_file.write(response.content)
                    image_path = tmp_file.name
            except Exception as e:
                logger.warning(f"이미지 다운로드 실패: {str(e)}")
                image_path = None
        
        if not image_path:
            # 기본 이미지 사용
            image_path = "default_image.jpg"
            if not os.path.exists(image_path):
                default_img = Image.new('RGB', (300, 300), color='lightgray')
                default_img.save(image_path)
        
        # 분석 실행
        result = analyzer.analyze_review(
            product_name=product_name,
            product_description=product_description,
            review_text=review_text,
            review_image_path=image_path
        )
        
        # 임시 파일 정리
        if image_url and os.path.exists(image_path):
            os.unlink(image_path)
        
        return result
        
    except Exception as e:
        logger.error(f"분석 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 중 오류가 발생했습니다: {str(e)}")

@app.get("/model_info")
async def get_model_info():
    """모델 정보 조회"""
    return {
        "model_name": "Review Analyzer v1.0",
        "features": [
            "이미지-텍스트 일치성 검증",
            "감정 분석",
            "신뢰도 점수 계산"
        ],
        "supported_languages": ["한국어", "영어"],
        "image_formats": ["JPEG", "PNG", "JPG"]
    }

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 