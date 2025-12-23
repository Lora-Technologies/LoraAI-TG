from openai import AsyncOpenAI
from typing import AsyncGenerator, Optional
from src.utils import get_logger
from src.utils.helpers import format_search_context

logger = get_logger("ai_service")


class AIService:
    def __init__(self, api_key: str, base_url: str, model: str, max_tokens: int, system_prompt: str):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
    
    async def generate_response(
        self,
        user_message: str,
        conversation_history: list[dict],
        search_results: Optional[list[dict]] = None
    ) -> tuple[str, int]:
        messages = [{"role": "system", "content": self.system_prompt}]
        
        if search_results:
            search_context = format_search_context(search_results)
            messages.append({
                "role": "system",
                "content": f"Kullanıcının sorusuyla ilgili güncel web arama sonuçları:\n\n{search_context}\n\nBu bilgileri kullanarak yanıt ver ve gerekirse kaynaklara atıfta bulun."
            })
        
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            logger.info_ctx(
                "AI response generated",
                action="ai_response",
                extra_data={"model": self.model, "tokens": tokens_used}
            )
            
            return content, tokens_used
            
        except Exception as e:
            logger.error_ctx(f"AI generation error: {str(e)}", action="ai_error")
            raise
    
    async def generate_response_stream(
        self,
        user_message: str,
        conversation_history: list[dict],
        search_results: Optional[list[dict]] = None
    ) -> AsyncGenerator[str, None]:
        messages = [{"role": "system", "content": self.system_prompt}]
        
        if search_results:
            search_context = format_search_context(search_results)
            messages.append({
                "role": "system",
                "content": f"Kullanıcının sorusuyla ilgili güncel web arama sonuçları:\n\n{search_context}\n\nBu bilgileri kullanarak yanıt ver."
            })
        
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=0.7,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error_ctx(f"AI stream error: {str(e)}", action="ai_stream_error")
            raise
    
    async def should_search(self, user_message: str) -> bool:
        search_keywords = [
            "güncel", "bugün", "şu an", "son dakika", "haber",
            "ne zaman", "kaç", "nerede", "kim", "fiyat",
            "current", "today", "latest", "news", "price",
            "weather", "hava durumu", "dolar", "euro", "bitcoin"
        ]
        
        message_lower = user_message.lower()
        return any(keyword in message_lower for keyword in search_keywords)
