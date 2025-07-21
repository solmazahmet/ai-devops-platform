"""
OpenAI Client Integration
OpenAI API entegrasyonu ve environment variables desteği
"""

import logging
import os
import aiohttp
import json
import asyncio
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Environment variables yükle
load_dotenv()

logger = logging.getLogger(__name__)

class OpenAIClient:
    """OpenAI API client"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # GPT-3.5-turbo kullan
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "500"))  # Daha az token
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))  # Daha düşük temperature
        self.max_retries = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
        self.retry_delay = float(os.getenv("OPENAI_RETRY_DELAY", "1.0"))
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY environment variable bulunamadı!")
    
    async def chat_completion(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        retries: Optional[int] = None
    ) -> str:
        """OpenAI Chat Completion API çağrısı (retry mekanizması ile)"""
        retries = retries or self.max_retries
        
        for attempt in range(retries + 1):
            try:
                if not self.api_key:
                    logger.error("OpenAI API key bulunamadı")
                    return self._fallback_response(user_prompt)
                
                url = f"{self.api_base}/chat/completions"
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": max_tokens or self.max_tokens,
                    "temperature": temperature or self.temperature
                }
                
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            content = result["choices"][0]["message"]["content"]
                            logger.info(f"OpenAI API çağrısı başarılı (attempt {attempt + 1})")
                            return content
                        elif response.status == 429:  # Rate limit
                            if attempt < retries:
                                wait_time = self.retry_delay * (2 ** attempt)
                                logger.warning(f"Rate limit, {wait_time}s bekleniyor...")
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                logger.error("Rate limit aşıldı, fallback kullanılıyor")
                                return self._fallback_response(user_prompt)
                        elif response.status == 400:  # Bad request
                            error_text = await response.text()
                            logger.error(f"OpenAI API bad request: {error_text}")
                            if "model" in error_text.lower():
                                logger.error("Model hatası - fallback kullanılıyor")
                                return self._fallback_response(user_prompt)
                            return self._fallback_response(user_prompt)
                        else:
                            error_text = await response.text()
                            logger.error(f"OpenAI API hatası: {response.status} - {error_text}")
                            if attempt < retries:
                                await asyncio.sleep(self.retry_delay)
                                continue
                            else:
                                return self._fallback_response(user_prompt)
                            
            except asyncio.TimeoutError:
                logger.warning(f"OpenAI API timeout (attempt {attempt + 1})")
                if attempt < retries:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    return self._fallback_response(user_prompt)
            except Exception as e:
                logger.error(f"OpenAI API çağrısı hatası (attempt {attempt + 1}): {e}")
                if attempt < retries:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    return self._fallback_response(user_prompt)
        
        return self._fallback_response(user_prompt)
    
    async def analyze_command(self, command: str, context: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Komut analizi için özel metod - basit prompt"""
        system_prompt = """
        Sen bir test uzmanısın. Kullanıcının komutunu analiz et.
        
        Desteklenen platformlar: instagram, facebook, twitter, linkedin, youtube, tiktok
        Test türleri: ui, functional, performance, security, accessibility, e2e
        
        Sadece JSON formatında yanıt ver:
        {
            "intent": "test_platform",
            "platform": "instagram",
            "test_type": "functional",
            "confidence": 0.8
        }
        """
        
        user_prompt = f"Komut: {command}"
        
        try:
            response = await self.chat_completion(system_prompt, user_prompt, max_tokens=200)
            
            # JSON parse et
            result = json.loads(response)
            if "confidence" not in result:
                result["confidence"] = self._calculate_confidence(command, result.get("platform"))
            return result
        except json.JSONDecodeError:
            logger.warning("OpenAI response JSON parse edilemedi, fallback kullanılıyor")
            return self._fallback_command_analysis(command)
        except Exception as e:
            logger.error(f"Komut analizi hatası: {e}")
            return self._fallback_command_analysis(command)
    
    async def generate_test_strategy(self, platform: str, test_type: str, command: str) -> Dict[str, Any]:
        """Test stratejisi oluşturma için özel metod - basit prompt"""
        system_prompt = """
        Sen bir test uzmanısın. Platform için test stratejisi oluştur.
        
        Sadece JSON formatında yanıt ver:
        {
            "steps": ["1. Login test", "2. Navigation test", "3. Feature test"],
            "priority": "medium",
            "estimated_time": "5-10 minutes"
        }
        """
        
        user_prompt = f"Platform: {platform}, Test Type: {test_type}"
        
        try:
            response = await self.chat_completion(system_prompt, user_prompt, max_tokens=300)
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("OpenAI strategy response JSON parse edilemedi, fallback kullanılıyor")
            return self._fallback_test_strategy(platform, test_type)
        except Exception as e:
            logger.error(f"Test stratejisi oluşturma hatası: {e}")
            return self._fallback_test_strategy(platform, test_type)
    
    async def generate_automation_script(self, platform: str, test_steps: List[str]) -> str:
        """Platform için otomasyon scripti oluştur - basit prompt"""
        system_prompt = """
        Sen bir Selenium uzmanısın. Platform için basit test kodu oluştur.
        
        Sadece Python kodu döndür, açıklama ekleme.
        """
        
        user_prompt = f"Platform: {platform}, Steps: {test_steps[:3]}"  # İlk 3 adımı al
        
        try:
            response = await self.chat_completion(system_prompt, user_prompt, max_tokens=400)
            return response
        except Exception as e:
            logger.error(f"Otomasyon scripti oluşturma hatası: {e}")
            return "# Basic automation script"
    
    def _calculate_confidence(self, command: str, platform: str) -> float:
        """Komut analizi güven skorunu hesapla"""
        confidence = 0.0
        command_lower = command.lower()
        
        # Platform keyword matching
        platform_keywords = {
            "instagram": ["instagram", "ig", "insta", "gram", "story", "reel", "post"],
            "facebook": ["facebook", "fb", "meta", "wall", "timeline"],
            "twitter": ["twitter", "x", "tweet", "thread"],
            "linkedin": ["linkedin", "professional", "network"],
            "youtube": ["youtube", "yt", "video", "channel"],
            "tiktok": ["tiktok", "tt", "short", "video"]
        }
        
        if platform and platform in platform_keywords:
            for keyword in platform_keywords[platform]:
                if keyword in command_lower:
                    confidence += 0.3
                    break
        
        # Test keywords
        test_keywords = ["test", "test et", "kontrol et", "doğrula", "verify", "check"]
        for keyword in test_keywords:
            if keyword in command_lower:
                confidence += 0.4
                break
        
        # Command clarity
        if len(command.split()) >= 2:
            confidence += 0.2
        
        # Specific platform mentions
        if platform and platform in command_lower:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _fallback_response(self, user_prompt: str) -> str:
        """API key olmadığında fallback yanıt"""
        return f"OpenAI API kullanılamıyor. Komut: {user_prompt}"
    
    def _fallback_command_analysis(self, command: str) -> Dict[str, Any]:
        """Fallback komut analizi"""
        command_lower = command.lower()
        
        # Basit keyword-based parsing
        platform = None
        platforms = ["instagram", "facebook", "twitter", "linkedin", "youtube", "tiktok"]
        for p in platforms:
            if p in command_lower:
                platform = p
                break
        
        test_type = "functional"
        if "ui" in command_lower or "görsel" in command_lower:
            test_type = "ui"
        elif "performans" in command_lower or "hız" in command_lower:
            test_type = "performance"
        elif "güvenlik" in command_lower or "security" in command_lower:
            test_type = "security"
        elif "e2e" in command_lower or "end-to-end" in command_lower:
            test_type = "e2e"
        
        confidence = self._calculate_confidence(command, platform or "")
        
        return {
            "intent": "test_platform",
            "platform": platform,
            "test_type": test_type,
            "confidence": confidence,
            "parameters": {
                "scope": "basic",
                "browser": "chrome",
                "headless": True
            }
        }
    
    def _fallback_test_strategy(self, platform: str, test_type: str) -> Dict[str, Any]:
        """Fallback test stratejisi"""
        if platform == "instagram":
            steps = [
                "1. Instagram ana sayfasını aç",
                "2. Login formunu kontrol et",
                "3. Feed sayfasını test et",
                "4. Navigasyon menüsünü test et",
                "5. Profil sayfasını kontrol et"
            ]
            automation_script = """
# Instagram Test
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get("https://www.instagram.com")

# Login test
username_field = driver.find_element(By.NAME, "username")
password_field = driver.find_element(By.NAME, "password")
username_field.send_keys("test_user")
password_field.send_keys("test_password")

driver.quit()
            """
        else:
            steps = [
                "1. Platform ana sayfasını aç",
                "2. Temel navigasyonu test et",
                "3. Ana özellikleri kontrol et"
            ]
            automation_script = "# Basic web automation script"
        
        return {
            "steps": steps,
            "automation_script": automation_script,
            "priority": "medium",
            "estimated_time": "5-10 minutes",
            "test_scenarios": [
                {
                    "name": "Basic Functionality Test",
                    "description": "Platform temel özelliklerini test et",
                    "priority": "high"
                }
            ]
        }
    
    def is_available(self) -> bool:
        """OpenAI API'nin kullanılabilir olup olmadığını kontrol et"""
        return bool(self.api_key)
    
    def get_config(self) -> Dict[str, Any]:
        """Mevcut konfigürasyonu döndür"""
        return {
            "api_base": self.api_base,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "available": self.is_available()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """OpenAI API sağlık kontrolü"""
        try:
            if not self.api_key:
                return {
                    "status": "error",
                    "message": "API key bulunamadı",
                    "available": False
                }
            
            # Basit bir test çağrısı yap
            response = await self.chat_completion(
                "Sen bir test botusun. Sadece 'OK' yanıt ver.",
                "Test mesajı",
                max_tokens=10
            )
            
            if response and "OK" in response:
                return {
                    "status": "healthy",
                    "message": "OpenAI API çalışıyor",
                    "available": True,
                    "response_time": "normal",
                    "model": self.model
                }
            else:
                return {
                    "status": "warning",
                    "message": "OpenAI API yanıt veriyor ama beklenmeyen format",
                    "available": True,
                    "response_time": "normal",
                    "model": self.model
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"OpenAI API hatası: {str(e)}",
                "available": False,
                "error": str(e),
                "model": self.model
            } 