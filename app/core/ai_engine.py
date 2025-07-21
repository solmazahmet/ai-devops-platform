"""
AI Engine - OpenAI GPT-3.5-turbo Integration
Natural Language Processing ve Command Parsing
"""

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import json
import re

logger = logging.getLogger(__name__)

class TestStrategy(BaseModel):
    """Test stratejisi modeli"""
    platform: str
    test_type: str
    steps: List[str]
    automation_script: str
    priority: str = "medium"
    estimated_time: str = "5-10 minutes"
    test_scenarios: List[Dict[str, Any]] = []

class AICommand(BaseModel):
    """AI komut modeli"""
    original_command: str
    parsed_intent: str
    platform: Optional[str] = None
    test_type: Optional[str] = None
    parameters: Dict[str, Any] = {}
    confidence: float = 0.0

class AIEngine:
    """AI Engine - OpenAI GPT-3.5-turbo entegrasyonu"""
    
    def __init__(self, openai_client):
        self.openai_client = openai_client
        self.supported_platforms = ["instagram", "facebook", "twitter", "linkedin", "youtube", "tiktok"]
        self.test_types = ["ui", "functional", "performance", "security", "accessibility", "e2e"]
        
        # Platform-specific keywords
        self.platform_keywords = {
            "instagram": ["instagram", "ig", "insta", "gram", "story", "reel", "post"],
            "facebook": ["facebook", "fb", "meta", "wall", "timeline"],
            "twitter": ["twitter", "x", "tweet", "thread"],
            "linkedin": ["linkedin", "professional", "network"],
            "youtube": ["youtube", "yt", "video", "channel"],
            "tiktok": ["tiktok", "tt", "short", "video"]
        }
    
    async def process_command(self, command: str, context: Dict[str, Any] = {}) -> AICommand:
        """Doğal dil komutunu işle ve yapılandırılmış komuta dönüştür"""
        try:
            # OpenAI ile komut analizi
            analysis = await self._analyze_command_with_openai(command, context)
            
            # Sonucu AICommand modeline dönüştür
            ai_command = AICommand(
                original_command=command,
                parsed_intent=analysis.get("intent", "unknown"),
                platform=analysis.get("platform"),
                test_type=analysis.get("test_type"),
                parameters=analysis.get("parameters", {}),
                confidence=analysis.get("confidence", 0.0)
            )
            
            logger.info(f"Command processed: {ai_command}")
            return ai_command
            
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            # Fallback parsing
            return self._fallback_parsing(command)
    
    async def generate_test_strategy(self, ai_command: AICommand) -> TestStrategy:
        """AI komutuna göre test stratejisi oluştur"""
        try:
            # Platform-specific test stratejisi
            if ai_command.platform == "instagram":
                return await self._generate_instagram_strategy(ai_command)
            
            # OpenAI ile genel test stratejisi oluştur
            strategy_data = await self._generate_strategy_with_openai(ai_command)
            
            test_strategy = TestStrategy(
                platform=ai_command.platform or "web",
                test_type=ai_command.test_type or "functional",
                steps=strategy_data.get("steps", []),
                automation_script=strategy_data.get("automation_script", ""),
                priority=strategy_data.get("priority", "medium"),
                estimated_time=strategy_data.get("estimated_time", "5-10 minutes"),
                test_scenarios=strategy_data.get("test_scenarios", [])
            )
            
            logger.info(f"Test strategy generated: {test_strategy}")
            return test_strategy
            
        except Exception as e:
            logger.error(f"Error generating test strategy: {e}")
            return self._default_test_strategy(ai_command)
    
    async def _generate_instagram_strategy(self, ai_command: AICommand) -> TestStrategy:
        """Instagram için özel test stratejisi"""
        steps = [
            "1. Instagram ana sayfasını aç ve sayfa yüklenmesini kontrol et",
            "2. Login formunu bul ve form elemanlarını doğrula",
            "3. Test kullanıcı bilgileri ile login formunu doldur",
            "4. Login butonuna tıkla ve sonucu kontrol et",
            "5. Ana feed sayfasının yüklenmesini bekle",
            "6. Navigasyon menüsünü kontrol et (Home, Search, Reels, etc.)",
            "7. Profil sayfasına git ve profil bilgilerini kontrol et",
            "8. Post oluşturma butonunu bul ve tıkla",
            "9. Story oluşturma özelliğini kontrol et",
            "10. Arama fonksiyonunu test et",
            "11. Ekran görüntüleri al ve test raporu oluştur"
        ]
        
        automation_script = """
# Instagram Comprehensive Test Automation
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=chrome_options)

def test_instagram():
    driver = setup_driver()
    wait = WebDriverWait(driver, 10)
    
    try:
        # 1. Ana sayfa
        driver.get("https://www.instagram.com")
        time.sleep(2)
        
        # 2. Login form kontrolü
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        
        # 3. Test verileri gir
        username_field.send_keys("test_user")
        password_field.send_keys("test_password")
        
        # 4. Login butonu
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        
        # 5. Feed sayfası bekleme
        time.sleep(3)
        
        # 6. Navigasyon testi
        nav_elements = driver.find_elements(By.XPATH, "//nav//a")
        
        # 7. Profil sayfası
        profile_link = driver.find_element(By.XPATH, "//a[contains(@href, '/accounts/activity/')]")
        profile_link.click()
        
        # 8. Ekran görüntüsü
        driver.save_screenshot("instagram_test_result.png")
        
        return True
        
    except Exception as e:
        print(f"Test hatası: {e}")
        return False
    finally:
        driver.quit()

if __name__ == "__main__":
    test_instagram()
        """
        
        return TestStrategy(
            platform="instagram",
            test_type=ai_command.test_type or "e2e",
            steps=steps,
            automation_script=automation_script,
            priority="high",
            estimated_time="10-15 minutes",
            test_scenarios=[
                {
                    "name": "Login Test",
                    "description": "Instagram login formunun çalışmasını test et",
                    "priority": "high"
                },
                {
                    "name": "Navigation Test", 
                    "description": "Ana navigasyon menüsünün çalışmasını test et",
                    "priority": "medium"
                },
                {
                    "name": "Profile Test",
                    "description": "Profil sayfasının yüklenmesini test et", 
                    "priority": "medium"
                }
            ]
        )
    
    async def _analyze_command_with_openai(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """OpenAI ile komut analizi - basit prompt"""
        try:
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
            
            response = await self.openai_client.chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=200
            )
            
            # JSON parse et
            try:
                result = json.loads(response)
                # Confidence değerini kontrol et
                if "confidence" not in result:
                    result["confidence"] = self._calculate_confidence(command, result.get("platform"))
                return result
            except json.JSONDecodeError:
                logger.warning("OpenAI response is not valid JSON, using fallback")
                fallback_result = self._fallback_parsing(command)
                return {
                    "intent": fallback_result.parsed_intent,
                    "platform": fallback_result.platform,
                    "test_type": fallback_result.test_type,
                    "confidence": fallback_result.confidence,
                    "parameters": fallback_result.parameters
                }
                
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            fallback_result = self._fallback_parsing(command)
            return {
                "intent": fallback_result.parsed_intent,
                "platform": fallback_result.platform,
                "test_type": fallback_result.test_type,
                "confidence": fallback_result.confidence,
                "parameters": fallback_result.parameters
            }
    
    def _calculate_confidence(self, command: str, platform: str) -> float:
        """Komut analizi güven skorunu hesapla"""
        confidence = 0.0
        command_lower = command.lower()
        
        # Platform keyword matching
        if platform and platform in self.platform_keywords:
            for keyword in self.platform_keywords[platform]:
                if keyword in command_lower:
                    confidence += 0.3
                    break
        
        # Test keywords
        test_keywords = ["test", "test et", "kontrol et", "doğrula", "verify"]
        for keyword in test_keywords:
            if keyword in command_lower:
                confidence += 0.4
                break
        
        # Command clarity
        if len(command.split()) >= 2:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    async def _generate_strategy_with_openai(self, ai_command: AICommand) -> Dict[str, Any]:
        """OpenAI ile test stratejisi oluştur - basit prompt"""
        try:
            system_prompt = """
            Sen bir test uzmanısın. Platform için test stratejisi oluştur.
            
            Sadece JSON formatında yanıt ver:
            {
                "steps": ["1. Login test", "2. Navigation test", "3. Feature test"],
                "priority": "medium",
                "estimated_time": "5-10 minutes"
            }
            """
            
            user_prompt = f"Platform: {ai_command.platform}, Test Type: {ai_command.test_type}"
            
            response = await self.openai_client.chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=300
            )
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                logger.warning("OpenAI strategy response is not valid JSON, using default")
                return self._default_strategy_data(ai_command)
                
        except Exception as e:
            logger.error(f"OpenAI strategy generation failed: {e}")
            return self._default_strategy_data(ai_command)
    
    def _fallback_parsing(self, command: str) -> AICommand:
        """Basit keyword-based parsing (fallback)"""
        command_lower = command.lower()
        
        # Platform tespiti
        platform = None
        confidence = 0.0
        
        for p, keywords in self.platform_keywords.items():
            for keyword in keywords:
                if keyword in command_lower:
                    platform = p
                    confidence += 0.3
                    break
            if platform:
                break
        
        # Test türü tespiti
        test_type = "functional"  # default
        if "ui" in command_lower or "görsel" in command_lower:
            test_type = "ui"
        elif "performans" in command_lower or "hız" in command_lower:
            test_type = "performance"
        elif "güvenlik" in command_lower or "security" in command_lower:
            test_type = "security"
        elif "e2e" in command_lower or "end-to-end" in command_lower:
            test_type = "e2e"
        
        # Confidence hesapla
        if "test" in command_lower or "test et" in command_lower:
            confidence += 0.4
        
        return AICommand(
            original_command=command,
            parsed_intent="test_platform",
            platform=platform,
            test_type=test_type,
            parameters={},
            confidence=min(confidence, 1.0)
        )
    
    def _default_test_strategy(self, ai_command: AICommand) -> TestStrategy:
        """Varsayılan test stratejisi"""
        platform = ai_command.platform or "web"
        
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
        
        return TestStrategy(
            platform=platform,
            test_type=ai_command.test_type or "functional",
            steps=steps,
            automation_script=automation_script,
            priority="medium",
            estimated_time="5-10 minutes",
            test_scenarios=[
                {
                    "name": "Basic Functionality Test",
                    "description": "Platform temel özelliklerini test et",
                    "priority": "high"
                }
            ]
        )
    
    def _default_strategy_data(self, ai_command: AICommand) -> Dict[str, Any]:
        """Varsayılan strateji verisi"""
        return {
            "steps": ["1. Platform test", "2. Feature test", "3. Validation"],
            "automation_script": "# Default automation script",
            "priority": "medium",
            "estimated_time": "5-10 minutes",
            "test_scenarios": [
                {
                    "name": "Default Test",
                    "description": "Varsayılan test senaryosu",
                    "priority": "medium"
                }
            ]
        } 