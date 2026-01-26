#!/usr/bin/env python3
"""
⚡ STRYDA VISION ENGINE
======================
Emergent Integrations wrapper for Gemini Vision API.

Usage:
    from core.vision_engine import extract_page_vision, VisionEngine
"""
import os
import base64
import hashlib
from io import BytesIO
from dotenv import load_dotenv

load_dotenv('/app/backend-minimal/.env')

from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
from pdf2image import convert_from_bytes

from core.config import (
    EMERGENT_LLM_KEY,
    VISION_MODEL_PROVIDER,
    VISION_MODEL_NAME,
    PDF_DPI_STANDARD,
    PDF_DPI_HIGH_COMPLEXITY,
    MAX_PAGES_STANDARD,
    MAX_PAGES_HIGH_COMPLEXITY,
    JPEG_QUALITY
)


class VisionEngine:
    """
    Unified Vision Engine using Emergent Integrations.
    Handles PDF-to-image conversion and LLM vision analysis.
    """
    
    def __init__(self, segment_name='document'):
        self.segment_name = segment_name
        self.api_key = EMERGENT_LLM_KEY
        self.provider = VISION_MODEL_PROVIDER
        self.model = VISION_MODEL_NAME
    
    async def analyze_image(self, image_base64, prompt, context=''):
        """
        Analyze a single image using Gemini Vision via Emergent.
        
        Args:
            image_base64: Base64 encoded JPEG image
            prompt: Analysis prompt
            context: Additional context for the analysis
        
        Returns:
            str: Vision model response
        """
        try:
            session_id = f"vision-{hashlib.md5(prompt[:50].encode()).hexdigest()[:8]}"
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message="You are a technical document parser for construction products."
            ).with_model(self.provider, self.model)
            
            image_content = ImageContent(image_base64=image_base64)
            
            user_message = UserMessage(
                text=f"{context}\n\n{prompt}",
                file_contents=[image_content]
            )
            
            response = await chat.send_message(user_message)
            return response
            
        except Exception as e:
            return f"Vision error: {str(e)[:50]}"
    
    def pdf_to_images(self, pdf_bytes, high_complexity=False):
        """
        Convert PDF to list of base64 encoded JPEG images.
        
        Args:
            pdf_bytes: Raw PDF bytes
            high_complexity: Use higher DPI for complex documents
        
        Returns:
            list: List of base64 encoded images
        """
        dpi = PDF_DPI_HIGH_COMPLEXITY if high_complexity else PDF_DPI_STANDARD
        max_pages = MAX_PAGES_HIGH_COMPLEXITY if high_complexity else MAX_PAGES_STANDARD
        
        images = convert_from_bytes(pdf_bytes, dpi=dpi, fmt='JPEG')
        
        encoded_images = []
        for i, img in enumerate(images[:max_pages]):
            img_buffer = BytesIO()
            img.save(img_buffer, format='JPEG', quality=JPEG_QUALITY)
            img_bytes = img_buffer.getvalue()
            encoded_images.append({
                'page': i + 1,
                'base64': base64.b64encode(img_bytes).decode('utf-8'),
                'size_kb': len(img_bytes) / 1024
            })
        
        return encoded_images, len(images)


async def extract_page_vision(image_base64, page_num, product_name, prompt):
    """
    Convenience function for single page extraction.
    """
    engine = VisionEngine(segment_name=product_name)
    context = f"[Document: {product_name} | Page: {page_num}]"
    return await engine.analyze_image(image_base64, prompt, context)
