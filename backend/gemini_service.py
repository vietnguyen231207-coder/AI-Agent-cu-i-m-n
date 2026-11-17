"""
Module: backend/gemini_service.py
Dịch vụ tích hợp Gemini API (Google AI Studio) với API Key của người dùng.
Sử dụng model gemini-3.5-flash tốc độ cao và suy luận chuẩn xác cho:
1. Phân tích tài liệu RFQ / Bóc tách điều kiện kỹ thuật tiềm ẩn
2. Đánh giá rủi ro thương mại & đề xuất giải pháp
3. Trợ lý AI hỏi đáp trực tiếp (Interactive Chatbot)
"""

import os
import json
import urllib.request
import urllib.error

# API Key do người dùng cung cấp
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AQ.Ab8RN6LmjIXtF_uRbPlk66sAsIRMRg6wJUIJ297Jk2BCpo_ixQ')
DEFAULT_MODEL = 'gemini-3.5-flash'

class GeminiService:
    def __init__(self, api_key=None, model=DEFAULT_MODEL):
        self.api_key = api_key or GEMINI_API_KEY
        self.model = model
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

    def generate_text(self, prompt, system_instruction=None, temperature=0.3):
        """
        Gọi Gemini API để sinh nội dung văn bản.
        """
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 1500
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        try:
            req = urllib.request.Request(
                self.endpoint,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_data = json.loads(resp.read().decode('utf-8'))
                candidates = res_data.get('candidates', [])
                if candidates and 'content' in candidates[0]:
                    parts = candidates[0]['content'].get('parts', [])
                    if parts:
                        return parts[0].get('text', '')
                return "Không nhận được phản hồi từ mô hình."
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='ignore')
            return f"[Gemini API HTTP {e.code}]: {err_body[:200]}"
        except Exception as e:
            return f"[Lỗi kết nối Gemini]: {str(e)}"

    def analyze_rfq_deep(self, rfq_text, catalog_summary=""):
        """
        AI Phân tích sâu hồ sơ RFQ, nhận diện rủi ro tiềm ẩn và đề xuất chiến lược.
        """
        sys_prompt = (
            "Bạn là Giám đốc Giải pháp Kỹ thuật & Quản trị Rủi ro của Công ty Thiết bị Mạng Thiên Minh Networks. "
            "Nhiệm vụ của bạn là đọc hồ sơ mời chào giá (RFQ), phát hiện các điều kiện ngầm (SLA, phạt trễ hạn, tính năng bắt buộc) "
            "và đưa ra nhận định kinh doanh chính xác, súc tích bằng tiếng Việt."
        )
        prompt = f"""
Hãy phân tích tài liệu RFQ sau đây:
---
{rfq_text[:3000]}
---
Danh mục thiết bị khả dụng của Thiên Minh:
{catalog_summary[:1500]}

Hãy trả về kết quả theo cấu trúc:
1. Nhận định trọng tâm & phân loại dự án.
2. Các điều kiện kỹ thuật deal-breaker (bắt buộc phải có, nếu thiếu sẽ bị loại).
3. Đánh giá tính khả thi về tiến độ & rủi ro phạt hợp đồng.
4. Đề xuất chiến lược thương mại (tỷ lệ chiết khấu và phương án chào giá).
"""
        return self.generate_text(prompt, system_instruction=sys_prompt)

    def chat_about_project(self, message, project_state_json):
        """
        Trò chuyện tương tác với người dùng về dự án hiện tại.
        """
        sys_prompt = (
            "Bạn là Trợ lý AI Thiên Minh Networks. Bạn nắm rõ toàn bộ dữ liệu dự án hiện tại "
            "(đối chiếu giải pháp, chiết khấu, tiến độ, điểm chuyển duyệt). Hãy trả lời câu hỏi của người dùng "
            "ngắn gọn, chuyên nghiệp, hỗ trợ ra quyết định kinh doanh."
        )
        prompt = f"""
Dữ liệu dự án hiện tại:
{json.dumps(project_state_json, ensure_ascii=False)[:3000]}

Câu hỏi của người dùng: {message}
"""
        return self.generate_text(prompt, system_instruction=sys_prompt, temperature=0.5)

# Khởi tạo singleton
gemini_agent = GeminiService()

