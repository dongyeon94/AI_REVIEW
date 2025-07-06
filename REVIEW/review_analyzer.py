import torch
import torch.nn.functional as F
from transformers import CLIPProcessor, CLIPModel, pipeline
from PIL import Image
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from rembg import remove
import imagehash
from skimage.metrics import structural_similarity as ssim
import cv2

class ReviewAnalyzer:
    """
    상품 리뷰 분석 모델
    - 이미지-텍스트 일치성 검증
    - 감정 분석
    - 신뢰도 점수 계산
    """
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # CLIP 모델 로드 (이미지-텍스트 매칭용)
        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_model.to(self.device)
        
        # 감정 분석 모델 로드
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="klue/bert-base",
            tokenizer="klue/bert-base",
            device=0 if torch.cuda.is_available() else -1
        )
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def analyze_review(self, 
                      product_name: str, 
                      product_description: str,
                      review_text: str, 
                      review_image_path: str,
                      product_image_path: str,
                      sentiment_text: str = None) -> dict:
        """
        상품 이미지와 리뷰 이미지의 유사도 (CLIP + pHash + SSIM) + 텍스트 감정분석(긍/부정)
        """
        try:
            # 리뷰 이미지 배경 제거 전처리
            review_image_path = self._preprocess_review_image(review_image_path)
            product_image_path = self._preprocess_review_image(product_image_path)
            # 1. CLIP 의미적 유사도
            clip_sim = self._compare_images_clip(product_image_path, review_image_path)
            # 2. pHash 구조적 유사도
            phash_sim = self._compare_images_phash(product_image_path, review_image_path)
            # 3. SSIM 구조적 유사도
            ssim_sim = self._compare_images_ssim(product_image_path, review_image_path)
            # 가중 평균 (CLIP 0.2, pHash 0.4, SSIM 0.4)
            final_score = 0.2 * clip_sim + 0.4 * phash_sim + 0.4 * ssim_sim
            confidence_score = final_score
            # 텍스트 감정분석(긍/부정)
            sentiment = None
            if sentiment_text:
                sentiment = self._simple_sentiment(sentiment_text)
            return {
                "clip_similarity": clip_sim,
                "phash_similarity": phash_sim,
                "ssim_similarity": ssim_sim,
                "final_similarity": final_score,
                "image_similarity": {
                    "score": final_score,
                    "is_matched": final_score > 0.7,
                    "description": self._get_match_description(final_score)
                },
                "confidence": {
                    "score": confidence_score,
                    "level": self._get_confidence_level(confidence_score)
                },
                "sentiment": sentiment,
                "overall_assessment": self._get_overall_assessment_img(final_score, confidence_score, sentiment)
            }
        except Exception as e:
            self.logger.error(f"분석 중 오류 발생: {str(e)}")
            return {
                "error": str(e),
                "clip_similarity": 0.0,
                "phash_similarity": 0.0,
                "ssim_similarity": 0.0,
                "final_similarity": 0.0,
                "image_similarity": {"score": 0.0, "is_matched": False, "description": "분석 실패"},
                "confidence": {"score": 0.0, "level": "낮음"},
                "sentiment": None,
                "overall_assessment": "분석을 완료할 수 없습니다."
            }

    def _compare_images_clip(self, img_path1: str, img_path2: str) -> float:
        """
        CLIP 임베딩 코사인 유사도 (0~1)
        """
        try:
            image1 = Image.open(img_path1).convert('RGB')
            image2 = Image.open(img_path2).convert('RGB')
            inputs1 = self.clip_processor(images=image1, return_tensors="pt").to(self.device)
            inputs2 = self.clip_processor(images=image2, return_tensors="pt").to(self.device)
            with torch.no_grad():
                emb1 = self.clip_model.get_image_features(**inputs1)
                emb2 = self.clip_model.get_image_features(**inputs2)
                emb1 = emb1 / emb1.norm(dim=-1, keepdim=True)
                emb2 = emb2 / emb2.norm(dim=-1, keepdim=True)
                sim = torch.nn.functional.cosine_similarity(emb1, emb2).item()
            return max(0.0, min((sim + 1) / 2, 1.0))
        except Exception as e:
            self.logger.error(f"CLIP 유사도 계산 실패: {str(e)}")
            return 0.0

    def _compare_images_phash(self, img_path1: str, img_path2: str) -> float:
        """
        Perceptual Hash(pHash) 기반 유사도 (0~1)
        """
        try:
            img1 = Image.open(img_path1).convert('RGB')
            img2 = Image.open(img_path2).convert('RGB')
            hash1 = imagehash.phash(img1)
            hash2 = imagehash.phash(img2)
            # 해밍거리 → 유사도(1-정규화)
            sim = 1 - (hash1 - hash2) / len(hash1.hash) ** 2
            return float(sim)
        except Exception as e:
            self.logger.error(f"pHash 유사도 계산 실패: {str(e)}")
            return 0.0

    def _compare_images_ssim(self, img_path1: str, img_path2: str) -> float:
        """
        SSIM(Structural Similarity) 기반 유사도 (0~1)
        """
        try:
            img1 = cv2.imread(img_path1)
            img2 = cv2.imread(img_path2)
            if img1 is None or img2 is None:
                return 0.0
            img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            img1 = cv2.resize(img1, (256, 256))
            img2 = cv2.resize(img2, (256, 256))
            sim, _ = ssim(img1, img2, full=True)
            return float(sim)
        except Exception as e:
            self.logger.error(f"SSIM 유사도 계산 실패: {str(e)}")
            return 0.0

    def _get_match_description(self, score: float) -> str:
        if score >= 0.8:
            return "상품과 이미지가 매우 잘 일치합니다."
        elif score >= 0.6:
            return "상품과 이미지가 대체로 일치합니다."
        elif score >= 0.4:
            return "상품과 이미지의 일치성이 낮습니다."
        else:
            return "상품과 이미지가 일치하지 않거나 확인할 수 없습니다."

    def _get_confidence_level(self, confidence: float) -> str:
        if confidence >= 0.8:
            return "매우 높음"
        elif confidence >= 0.6:
            return "높음"
        elif confidence >= 0.4:
            return "보통"
        else:
            return "낮음"

    def _get_overall_assessment_img(self, image_similarity: float, confidence_score: float, sentiment: dict = None) -> str:
        if image_similarity < 0.4:
            return "⚠️ 상품과 이미지가 일치하지 않습니다. 리뷰 검증이 필요합니다."
        msg = ""
        if image_similarity >= 0.7:
            msg = f"✅ 상품과 이미지가 잘 일치합니다! | 신뢰도: {confidence_score:.1%}"
        else:
            msg = f"상품과 이미지가 어느 정도 유사합니다. | 신뢰도: {confidence_score:.1%}"
        if sentiment:
            if sentiment["label"] == "positive":
                msg += " | 😊 긍정적 리뷰"
            elif sentiment["label"] == "negative":
                msg += " | 😞 부정적 리뷰"
        return msg
    
    def _preprocess_review_image(self, image_path: str) -> str:
        """
        리뷰 이미지에서 배경 제거 (PNG로 저장)
        """
        try:
            img = Image.open(image_path)
            out = remove(img)
            temp_path = image_path.rsplit('.', 1)[0] + '_nobg.png'
            out.save(temp_path)
            return temp_path
        except Exception as e:
            self.logger.warning(f"배경 제거 실패: {str(e)}")
            return image_path

    def _simple_sentiment(self, text: str) -> dict:
        """
        텍스트 감정분석(긍정/부정) - huggingface pipeline 사용, 점수 포함
        """
        try:
            result = self.sentiment_analyzer(text)[0]
            label = result["label"].lower()
            score = float(result["score"])
            if "pos" in label or "긍정" in label:
                return {"label": "positive", "description": "긍정적인 리뷰", "score": score}
            else:
                return {"label": "negative", "description": "부정적인 리뷰", "score": 1-score}
        except Exception as e:
            self.logger.warning(f"감정분석 실패: {str(e)}")
            return {"label": "unknown", "description": "감정분석 실패", "score": 0.5} 