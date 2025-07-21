"""
Web Automation Module
Selenium ile temel web otomasyon özellikleri ve AI strateji execution
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException, WebDriverException, NoSuchElementException,
    ElementClickInterceptedException, StaleElementReferenceException,
    ElementNotInteractableException, NoSuchWindowException
)
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
import time
import os
import json
import re
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class ElementSelector:
    """Element selector modeli - multiple selector stratejisi"""
    xpath: Optional[str] = None
    css: Optional[str] = None
    id: Optional[str] = None
    name: Optional[str] = None
    class_name: Optional[str] = None
    tag_name: Optional[str] = None
    link_text: Optional[str] = None
    partial_link_text: Optional[str] = None
    data_testid: Optional[str] = None
    aria_label: Optional[str] = None
    title: Optional[str] = None
    alt: Optional[str] = None

class TestStep:
    """Test adımı modeli"""
    def __init__(self, step_type: str, description: str, **kwargs):
        self.step_type = step_type
        self.description = description
        self.parameters = kwargs
        self.success = False
        self.error_message: Optional[str] = None
        self.duration = 0.0
        self.screenshot_path: Optional[str] = None
        self.element_found = False
        self.element_selector_used: Optional[str] = None
        self.wait_time = 0.0
        self.retry_count = 0
        self.start_time: float = 0.0

class TestResult:
    """Test sonucu modeli"""
    def __init__(self, platform: str, test_type: str):
        self.platform = platform
        self.test_type = test_type
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.total_duration = 0.0
        self.steps: List[TestStep] = []
        self.screenshots: List[str] = []
        self.success = False
        self.error_count = 0
        self.success_count = 0
        self.test_summary: Dict[str, Any] = {}
        self.element_success_rate = 0.0
        self.avg_step_duration = 0.0
        self.total_screenshots = 0

class WebAutomation:
    """Web otomasyon sınıfı - Modern Instagram 2025 desteği"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
        self.wait_timeout = 10  # Comprehensive testing için optimal timeout
        self.short_wait = 5
        self.test_results_dir = "test_results"
        self.screenshots_dir = "test_results/screenshots"
        self.take_screenshots = True  # Her zaman screenshot al
        
        # Dizinleri oluştur
        os.makedirs(self.test_results_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # Modern Instagram 2025 element selectors
        self.platform_selectors = {
            "instagram": {
                # Login form elements (public)
                "login_form": ElementSelector(
                    xpath="//form[contains(@class, 'login') or contains(@class, 'auth')]",
                    css="form[class*='login'], form[class*='auth']",
                    data_testid="login-form"
                ),
                "username_field": ElementSelector(
                    xpath="//input[@name='username' or @aria-label='Phone number, username, or email']",
                    css="input[name='username'], input[aria-label*='username'], input[aria-label*='email']",
                    name="username",
                    data_testid="username"
                ),
                "password_field": ElementSelector(
                    xpath="//input[@name='password' or @aria-label='Password']",
                    css="input[name='password'], input[aria-label*='Password']",
                    name="password",
                    data_testid="password"
                ),
                "login_button": ElementSelector(
                    xpath="//button[@type='submit' or contains(text(), 'Log in') or contains(text(), 'Sign in')]",
                    css="button[type='submit'], button:contains('Log in'), button:contains('Sign in')",
                    data_testid="login-button"
                ),
                
                # Navigation elements (public)
                "instagram_logo": ElementSelector(
                    xpath="//img[@alt='Instagram' or contains(@alt, 'Instagram')]",
                    css="img[alt*='Instagram'], svg[aria-label*='Instagram']",
                    data_testid="instagram-logo"
                ),
                "search_icon": ElementSelector(
                    xpath="//a[@href='/explore/'] or //a[contains(@aria-label, 'Search')]",
                    css="a[href='/explore/'], a[aria-label*='Search']",
                    data_testid="nav-search"
                ),
                "reels_icon": ElementSelector(
                    xpath="//a[@href='/reels/'] or //a[contains(@aria-label, 'Reels')]",
                    css="a[href='/reels/'], a[aria-label*='Reels']",
                    data_testid="nav-reels"
                ),
                "create_icon": ElementSelector(
                    xpath="//a[@href='/create/select/'] or //a[contains(@aria-label, 'New post')]",
                    css="a[href='/create/select/'], a[aria-label*='New post']",
                    data_testid="nav-create"
                ),
                "activity_icon": ElementSelector(
                    xpath="//a[@href='/accounts/activity/'] or //a[contains(@aria-label, 'Activity')]",
                    css="a[href='/accounts/activity/'], a[aria-label*='Activity']",
                    data_testid="nav-activity"
                ),
                "profile_icon": ElementSelector(
                    xpath="//a[@href='/accounts/activity/'] or //a[contains(@aria-label, 'Profile')]",
                    css="a[href='/accounts/activity/'], a[aria-label*='Profile']",
                    data_testid="nav-profile"
                ),
                
                # Content elements (public)
                "feed_posts": ElementSelector(
                    xpath="//article[contains(@class, 'post') or contains(@class, 'feed')]",
                    css="article[class*='post'], article[class*='feed'], div[data-testid='post']",
                    data_testid="post"
                ),
                "stories_container": ElementSelector(
                    xpath="//div[contains(@class, 'stories') or contains(@aria-label, 'Stories')]",
                    css="div[class*='stories'], div[aria-label*='Stories']",
                    data_testid="stories-container"
                ),
                "explore_grid": ElementSelector(
                    xpath="//div[contains(@class, 'explore') or contains(@aria-label, 'Explore')]",
                    css="div[class*='explore'], div[aria-label*='Explore']",
                    data_testid="explore-grid"
                ),
                
                # Footer elements (public)
                "footer_links": ElementSelector(
                    xpath="//footer//a or //div[contains(@class, 'footer')]//a",
                    css="footer a, div[class*='footer'] a",
                    tag_name="a"
                ),
                "language_selector": ElementSelector(
                    xpath="//select[contains(@aria-label, 'Language')] or //button[contains(@aria-label, 'Language')]",
                    css="select[aria-label*='Language'], button[aria-label*='Language']",
                    data_testid="language-selector"
                ),
                
                # Error/Info elements
                "error_message": ElementSelector(
                    xpath="//div[contains(@class, 'error') or contains(text(), 'error')]",
                    css="div[class*='error'], div[data-testid='error']",
                    data_testid="error-message"
                ),
                "info_message": ElementSelector(
                    xpath="//div[contains(@class, 'info') or contains(text(), 'info')]",
                    css="div[class*='info'], div[data-testid='info']",
                    data_testid="info-message"
                ),
                
                # Generic elements
                "any_button": ElementSelector(
                    xpath="//button",
                    css="button",
                    tag_name="button"
                ),
                "any_link": ElementSelector(
                    xpath="//a",
                    css="a",
                    tag_name="a"
                ),
                "any_input": ElementSelector(
                    xpath="//input",
                    css="input",
                    tag_name="input"
                )
            },
            "facebook": {
                "email_field": ElementSelector(id="email", name="email"),
                "password_field": ElementSelector(id="pass", name="pass"),
                "login_button": ElementSelector(name="login", data_testid="login-button"),
                "logo": ElementSelector(xpath="//a[@aria-label='Facebook']", css="a[aria-label='Facebook']")
            },
            "twitter": {
                "username_field": ElementSelector(name="text", data_testid="username"),
                "password_field": ElementSelector(name="password", data_testid="password"),
                "login_button": ElementSelector(xpath="//div[@data-testid='LoginButton']", data_testid="LoginButton"),
                "logo": ElementSelector(xpath="//a[@aria-label='Twitter']", css="a[aria-label='Twitter']")
            }
        }
        
    async def setup_driver(self) -> bool:
        """WebDriver'ı başlat - High Quality Comprehensive Testing"""
        try:
            chrome_options = Options()
            
            # Headless mode (optional)
            if self.headless:
                chrome_options.add_argument("--headless=new")
            
            # High Quality Chrome options - Comprehensive testing için optimize
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--enable-logging")
            chrome_options.add_argument("--v=1")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Experimental options
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0
            })
            
            # ChromeDriver path kontrolü
            if os.path.exists("/usr/bin/chromedriver"):
                service = Service("/usr/bin/chromedriver")
            else:
                service = Service()
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(3)  # Comprehensive testing için optimal wait
            
            # JavaScript ile webdriver özelliğini gizle
            if self.driver:
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
                self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
            
            mode_text = "Headless" if self.headless else "GUI Mode"
            logger.info(f"WebDriver başarıyla başlatıldı (High Quality Mode - {mode_text})")
            return True
            
        except Exception as e:
            logger.error(f"WebDriver başlatma hatası: {e}")
            return False
    
    async def close_driver(self):
        """WebDriver'ı kapat"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver kapatıldı")
            except Exception as e:
                logger.error(f"WebDriver kapatma hatası: {e}")
    
    async def find_element_robust(self, selector: ElementSelector, timeout: Optional[int] = None, step: Optional[TestStep] = None) -> Tuple[Optional[WebElement], str]:
        """Robust element bulma - multiple selector stratejisi"""
        timeout = timeout or self.wait_timeout
        if not self.driver:
            return None, "No driver"
        wait = WebDriverWait(self.driver, timeout)
        
        # Selector öncelik sırası
        selectors_to_try = [
            ("data-testid", selector.data_testid, By.CSS_SELECTOR, f"[data-testid='{selector.data_testid}']"),
            ("xpath", selector.xpath, By.XPATH, selector.xpath),
            ("css", selector.css, By.CSS_SELECTOR, selector.css),
            ("id", selector.id, By.ID, selector.id),
            ("name", selector.name, By.NAME, selector.name),
            ("class_name", selector.class_name, By.CLASS_NAME, selector.class_name),
            ("link_text", selector.link_text, By.LINK_TEXT, selector.link_text),
            ("partial_link_text", selector.partial_link_text, By.PARTIAL_LINK_TEXT, selector.partial_link_text),
            ("tag_name", selector.tag_name, By.TAG_NAME, selector.tag_name),
            ("aria_label", selector.aria_label, By.CSS_SELECTOR, f"[aria-label='{selector.aria_label}']"),
            ("title", selector.title, By.CSS_SELECTOR, f"[title='{selector.title}']"),
            ("alt", selector.alt, By.CSS_SELECTOR, f"[alt='{selector.alt}']")
        ]
        
        for selector_type, selector_value, by_type, selector_string in selectors_to_try:
            if not selector_value:
                continue
                
            try:
                # Explicit wait ile element bekle
                element = wait.until(
                    EC.presence_of_element_located((by_type, selector_string))
                )
                
                # Element görünür ve tıklanabilir mi kontrol et
                if element.is_displayed() and element.is_enabled():
                    if step:
                        step.element_found = True
                        step.element_selector_used = f"{selector_type}: {selector_string}"
                    logger.info(f"Element bulundu: {selector_type} = {selector_string}")
                    return element, f"{selector_type}: {selector_string}"
                    
            except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
                logger.debug(f"Selector başarısız: {selector_type} = {selector_string}, Hata: {e}")
                continue
            except Exception as e:
                logger.warning(f"Beklenmeyen hata: {selector_type} = {selector_string}, Hata: {e}")
                continue
        
        # Hiçbir selector çalışmadı
        if step:
            step.element_found = False
            step.element_selector_used = "None"
        
        logger.warning(f"Hiçbir selector çalışmadı: {selector}")
        return None, "None"
    
    async def wait_for_element_with_retry(self, selector: ElementSelector, timeout: Optional[int] = None, max_retries: int = 3) -> Tuple[Optional[WebElement], str]:
        """Retry mekanizması ile element bekleme"""
        for attempt in range(max_retries):
            try:
                element, selector_used = await self.find_element_robust(selector, timeout)
                if element:
                    return element, selector_used
                
                # Kısa bekleme sonra tekrar dene
                if attempt < max_retries - 1:
                    time.sleep(1)
                    
            except Exception as e:
                logger.warning(f"Retry {attempt + 1}/{max_retries} başarısız: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        return None, "None"
    
    async def take_step_screenshot(self, step: TestStep, step_name: Optional[str] = None) -> str:
        """Her adım için screenshot al - High Quality Comprehensive Testing"""
        try:
            if not self.driver:
                logger.error("Driver bulunamadı, screenshot alınamadı")
                return ""
                
            timestamp = int(time.time())
            step_name = step_name or step.step_type
            filename = f"{step_name}_{timestamp}.png"
            screenshot_path = os.path.join(self.screenshots_dir, filename)
            
            self.driver.save_screenshot(screenshot_path)
            step.screenshot_path = screenshot_path
            
            logger.info(f"High Quality Step screenshot alındı: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Step screenshot hatası: {e}")
            return ""
    
    async def execute_ai_strategy(self, platform: str, test_strategy: Dict[str, Any]) -> TestResult:
        """AI stratejisini Selenium koduna çevir ve çalıştır - Gelişmiş error handling"""
        test_result = TestResult(platform, test_strategy.get("test_type", "functional"))
        
        try:
            logger.info(f"AI stratejisi çalıştırılıyor: {platform}")
            
            # WebDriver'ı başlat
            if not await self.setup_driver():
                raise Exception("WebDriver başlatılamadı")
            
            # Platform-specific automation
            if platform == "instagram":
                await self._execute_instagram_strategy_modern(test_strategy, test_result)
            else:
                await self._execute_generic_strategy(platform, test_strategy, test_result)
            
            # Test sonuçlarını hesapla
            test_result.end_time = datetime.now()
            test_result.total_duration = (test_result.end_time - test_result.start_time).total_seconds()
            test_result.success = test_result.error_count == 0
            test_result.success_count = len([step for step in test_result.steps if step.success])
            
            # Gelişmiş test özeti
            if test_result.steps:
                test_result.avg_step_duration = sum(step.duration for step in test_result.steps) / len(test_result.steps)
                test_result.element_success_rate = len([step for step in test_result.steps if step.element_found]) / len(test_result.steps)
                test_result.total_screenshots = len([step for step in test_result.steps if step.screenshot_path])
            
            test_result.test_summary = {
                "total_steps": len(test_result.steps),
                "successful_steps": test_result.success_count,
                "failed_steps": test_result.error_count,
                "success_rate": test_result.success_count / len(test_result.steps) if test_result.steps else 0,
                "element_success_rate": test_result.element_success_rate,
                "avg_step_duration": test_result.avg_step_duration,
                "total_duration": test_result.total_duration,
                "screenshots_taken": test_result.total_screenshots,
                "platform": platform,
                "test_type": test_result.test_type,
                "webdriver_status": "success" if self.driver else "failed"
            }
            
            logger.info(f"AI stratejisi tamamlandı: {test_result.success}")
            return test_result
            
        except Exception as e:
            logger.error(f"AI stratejisi çalıştırma hatası: {e}")
            test_result.error_count += 1
            test_result.success = False
            return test_result
        finally:
            await self.close_driver()
    
    async def _execute_instagram_strategy_modern(self, test_strategy: Dict[str, Any], test_result: TestResult):
        """Instagram 2025 için modern strateji çalıştır - Public elements only"""
        selectors = self.platform_selectors.get("instagram", {})
        
        # 1. Instagram ana sayfasını aç
        step = TestStep("navigate", "Instagram ana sayfasını aç")
        step.start_time = time.time()
        
        try:
            await self.navigate_to("https://www.instagram.com")
            await self.take_step_screenshot(step, "instagram_homepage")
            step.success = True
            logger.info("Instagram ana sayfası açıldı")
        except Exception as e:
            step.error_message = str(e)
            test_result.error_count += 1
            logger.error(f"Instagram ana sayfası açma hatası: {e}")
        
        step.duration = time.time() - step.start_time
        test_result.steps.append(step)
        
        # 2. Instagram logo kontrolü
        step = TestStep("check_element", "Instagram logo kontrolü")
        step.start_time = time.time()
        
        try:
            logo_element, selector_used = await self.wait_for_element_with_retry(
                selectors["instagram_logo"], 
                timeout=self.short_wait
            )
            
            if logo_element:
                step.success = True
                step.element_found = True
                step.element_selector_used = selector_used
                logger.info("Instagram logo bulundu")
            else:
                step.error_message = "Instagram logo bulunamadı"
                test_result.error_count += 1
                
        except Exception as e:
            step.error_message = str(e)
            test_result.error_count += 1
            logger.error(f"Logo kontrolü hatası: {e}")
        
        await self.take_step_screenshot(step, "logo_check")
        step.duration = time.time() - step.start_time
        test_result.steps.append(step)
        
        # 3. Login form kontrolü (public element)
        step = TestStep("check_element", "Login form kontrolü")
        step.start_time = time.time()
        
        try:
            login_form, selector_used = await self.wait_for_element_with_retry(
                selectors["login_form"], 
                timeout=self.short_wait
            )
            
            if login_form:
                step.success = True
                step.element_found = True
                step.element_selector_used = selector_used
                logger.info("Login form bulundu")
                
                # Form elementlerini kontrol et
                username_field, _ = await self.find_element_robust(selectors["username_field"])
                password_field, _ = await self.find_element_robust(selectors["password_field"])
                login_button, _ = await self.find_element_robust(selectors["login_button"])
                
                if username_field and password_field and login_button:
                    logger.info("Tüm login form elementleri bulundu")
                else:
                    logger.warning("Bazı login form elementleri eksik")
            else:
                step.error_message = "Login form bulunamadı"
                test_result.error_count += 1
                
        except Exception as e:
            step.error_message = str(e)
            test_result.error_count += 1
            logger.error(f"Login form kontrolü hatası: {e}")
        
        await self.take_step_screenshot(step, "login_form_check")
        step.duration = time.time() - step.start_time
        test_result.steps.append(step)
        
        # 4. Navigation elementleri kontrolü (public)
        nav_tests = [
            ("search_icon", "Arama ikonu kontrolü"),
            ("reels_icon", "Reels ikonu kontrolü"),
            ("create_icon", "Post oluşturma ikonu kontrolü"),
            ("activity_icon", "Aktivite ikonu kontrolü"),
            ("profile_icon", "Profil ikonu kontrolü")
        ]
        
        for nav_key, nav_desc in nav_tests:
            if nav_key in selectors:
                step = TestStep("check_element", nav_desc)
                step.start_time = time.time()
                
                try:
                    nav_element, selector_used = await self.wait_for_element_with_retry(
                        selectors[nav_key], 
                        timeout=self.short_wait
                    )
                    
                    if nav_element:
                        step.success = True
                        step.element_found = True
                        step.element_selector_used = selector_used
                        logger.info(f"{nav_desc} başarılı")
                    else:
                        step.error_message = f"{nav_desc} elementi bulunamadı"
                        test_result.error_count += 1
                        
                except Exception as e:
                    step.error_message = str(e)
                    test_result.error_count += 1
                    logger.error(f"{nav_desc} hatası: {e}")
                
                await self.take_step_screenshot(step, nav_key)
                step.duration = time.time() - step.start_time
                test_result.steps.append(step)
        
        # 5. Content elementleri kontrolü (public)
        content_tests = [
            ("feed_posts", "Feed post kontrolü"),
            ("stories_container", "Stories container kontrolü"),
            ("explore_grid", "Explore grid kontrolü")
        ]
        
        for content_key, content_desc in content_tests:
            if content_key in selectors:
                step = TestStep("check_element", content_desc)
                step.start_time = time.time()
                
                try:
                    content_element, selector_used = await self.wait_for_element_with_retry(
                        selectors[content_key], 
                        timeout=self.short_wait
                    )
                    
                    if content_element:
                        step.success = True
                        step.element_found = True
                        step.element_selector_used = selector_used
                        logger.info(f"{content_desc} başarılı")
                    else:
                        step.error_message = f"{content_desc} elementi bulunamadı"
                        test_result.error_count += 1
                        
                except Exception as e:
                    step.error_message = str(e)
                    test_result.error_count += 1
                    logger.error(f"{content_desc} hatası: {e}")
                
                await self.take_step_screenshot(step, content_key)
                step.duration = time.time() - step.start_time
                test_result.steps.append(step)
        
        # 6. Footer elementleri kontrolü (public)
        step = TestStep("check_element", "Footer linkleri kontrolü")
        step.start_time = time.time()
        
        try:
            footer_links, selector_used = await self.find_element_robust(
                selectors["footer_links"], 
                timeout=self.short_wait
            )
            
            if footer_links:
                step.success = True
                step.element_found = True
                step.element_selector_used = selector_used
                logger.info("Footer linkleri bulundu")
            else:
                step.error_message = "Footer linkleri bulunamadı"
                test_result.error_count += 1
                
        except Exception as e:
            step.error_message = str(e)
            test_result.error_count += 1
            logger.error(f"Footer kontrolü hatası: {e}")
        
        await self.take_step_screenshot(step, "footer_check")
        step.duration = time.time() - step.start_time
        test_result.steps.append(step)
        
        # 7. Sayfa scroll testi
        step = TestStep("scroll", "Sayfa scroll testi")
        step.start_time = time.time()
        
        try:
            # Sayfayı aşağı scroll et
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            
            # Sayfayı yukarı scroll et
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            step.success = True
            logger.info("Scroll testi başarılı")
            
        except Exception as e:
            step.error_message = str(e)
            test_result.error_count += 1
            logger.error(f"Scroll testi hatası: {e}")
        
        await self.take_step_screenshot(step, "scroll_test")
        step.duration = time.time() - step.start_time
        test_result.steps.append(step)
        
        # 8. Final screenshot
        step = TestStep("screenshot", "Final ekran görüntüsü")
        step.start_time = time.time()
        
        try:
            screenshot_path = await self.take_screenshot(f"instagram_final_{int(time.time())}.png")
            if screenshot_path:
                test_result.screenshots.append(screenshot_path)
                step.screenshot_path = screenshot_path
                step.success = True
                logger.info("Final screenshot alındı")
            else:
                step.error_message = "Final screenshot alınamadı"
                test_result.error_count += 1
                
        except Exception as e:
            step.error_message = str(e)
            test_result.error_count += 1
            logger.error(f"Final screenshot hatası: {e}")
        
        step.duration = time.time() - step.start_time
        test_result.steps.append(step)
    
    async def _execute_generic_strategy(self, platform: str, test_strategy: Dict[str, Any], test_result: TestResult):
        """Genel platform stratejisi çalıştır"""
        # Platform URL'sini oluştur
        platform_url = f"https://www.{platform}.com"
        
        # 1. Platform ana sayfasını aç
        step = TestStep("navigate", f"{platform} ana sayfasını aç")
        step.start_time = time.time()
        
        try:
            await self.navigate_to(platform_url)
            await self.take_step_screenshot(step, f"{platform}_homepage")
            step.success = True
            logger.info(f"{platform} ana sayfası açıldı")
        except Exception as e:
            step.error_message = str(e)
            test_result.error_count += 1
            logger.error(f"{platform} ana sayfası açma hatası: {e}")
        
        step.duration = time.time() - step.start_time
        test_result.steps.append(step)
        
        # 2. Sayfa başlığını kontrol et
        step = TestStep("check_title", "Sayfa başlığını kontrol et")
        step.start_time = time.time()
        
        try:
            title = await self.get_page_title()
            if title and platform.lower() in title.lower():
                step.success = True
                logger.info(f"Sayfa başlığı doğru: {title}")
            else:
                step.error_message = f"Sayfa başlığı beklenmeyen: {title}"
                test_result.error_count += 1
                
        except Exception as e:
            step.error_message = str(e)
            test_result.error_count += 1
            logger.error(f"Sayfa başlığı kontrolü hatası: {e}")
        
        await self.take_step_screenshot(step, f"{platform}_title_check")
        step.duration = time.time() - step.start_time
        test_result.steps.append(step)
        
        # 3. Temel elementleri kontrol et
        step = TestStep("check_elements", "Temel elementleri kontrol et")
        step.start_time = time.time()
        
        try:
            # Logo, navigation, footer gibi temel elementleri kontrol et
            basic_elements = [
                (By.TAG_NAME, "nav"),
                (By.TAG_NAME, "footer"),
                (By.TAG_NAME, "main")
            ]
            
            found_elements = 0
            for by, value in basic_elements:
                element = await self.find_element(by, value)
                if element:
                    found_elements += 1
            
            if found_elements >= 2:
                step.success = True
                step.element_found = True
                logger.info(f"{found_elements} temel element bulundu")
            else:
                step.error_message = f"Yeterli temel element bulunamadı: {found_elements}"
                test_result.error_count += 1
                
        except Exception as e:
            step.error_message = str(e)
            test_result.error_count += 1
            logger.error(f"Element kontrolü hatası: {e}")
        
        await self.take_step_screenshot(step, f"{platform}_elements_check")
        step.duration = time.time() - step.start_time
        test_result.steps.append(step)
        
        # 4. Final screenshot
        step = TestStep("screenshot", "Final ekran görüntüsü")
        step.start_time = time.time()
        
        try:
            screenshot_path = await self.take_screenshot(f"{platform}_final_{int(time.time())}.png")
            if screenshot_path:
                test_result.screenshots.append(screenshot_path)
                step.screenshot_path = screenshot_path
                step.success = True
                logger.info("Final screenshot alındı")
            else:
                step.error_message = "Final screenshot alınamadı"
                test_result.error_count += 1
                
        except Exception as e:
            step.error_message = str(e)
            test_result.error_count += 1
            logger.error(f"Final screenshot hatası: {e}")
        
        step.duration = time.time() - step.start_time
        test_result.steps.append(step)
    
    async def navigate_to(self, url: str) -> bool:
        """Belirtilen URL'ye git"""
        try:
            if not self.driver:
                if not await self.setup_driver():
                    return False
            
            self.driver.get(url)
            logger.info(f"URL'ye gidildi: {url}")
            return True
            
        except Exception as e:
            logger.error(f"URL navigasyon hatası: {e}")
            return False
    
    async def find_element(self, by: str, value: str, timeout: Optional[int] = None) -> Optional[Any]:
        """Element bul - Legacy method"""
        try:
            if not self.driver:
                logger.error("Driver bulunamadı")
                return None
            wait = WebDriverWait(self.driver, timeout or self.wait_timeout)
            element = wait.until(EC.presence_of_element_located((by, value)))
            return element
        except TimeoutException:
            logger.warning(f"Element bulunamadı: {by}={value}")
            return None
        except Exception as e:
            logger.error(f"Element arama hatası: {e}")
            return None
    
    async def find_elements(self, by: str, value: str, timeout: Optional[int] = None) -> List[Any]:
        """Birden fazla element bul"""
        try:
            if not self.driver:
                logger.error("Driver bulunamadı")
                return []
            wait = WebDriverWait(self.driver, timeout or self.wait_timeout)
            elements = wait.until(EC.presence_of_all_elements_located((by, value)))
            return elements
        except TimeoutException:
            logger.warning(f"Elementler bulunamadı: {by}={value}")
            return []
        except Exception as e:
            logger.error(f"Elementler arama hatası: {e}")
            return []
    
    async def click_element(self, by: str, value: str) -> bool:
        """Elemente tıkla"""
        try:
            element = await self.find_element(by, value)
            if element:
                # JavaScript ile tıklama (daha güvenilir)
                self.driver.execute_script("arguments[0].click();", element)
                logger.info(f"Element tıklandı: {by}={value}")
                return True
            return False
        except Exception as e:
            logger.error(f"Element tıklama hatası: {e}")
            return False
    
    async def input_text(self, by: str, value: str, text: str) -> bool:
        """Elemente metin gir"""
        try:
            element = await self.find_element(by, value)
            if element:
                element.clear()
                element.send_keys(text)
                logger.info(f"Metin girildi: {by}={value}, text={text}")
                return True
            return False
        except Exception as e:
            logger.error(f"Metin girme hatası: {e}")
            return False
    
    async def get_page_title(self) -> str:
        """Sayfa başlığını al"""
        try:
            return self.driver.title
        except Exception as e:
            logger.error(f"Sayfa başlığı alma hatası: {e}")
            return ""
    
    async def get_page_url(self) -> str:
        """Mevcut URL'yi al"""
        try:
            return self.driver.current_url
        except Exception as e:
            logger.error(f"URL alma hatası: {e}")
            return ""
    
    async def take_screenshot(self, filename: str = None) -> str:
        """Ekran görüntüsü al"""
        try:
            if not filename:
                timestamp = int(time.time())
                filename = f"screenshot_{timestamp}.png"
            
            screenshot_path = os.path.join(self.test_results_dir, filename)
            
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Ekran görüntüsü alındı: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Ekran görüntüsü alma hatası: {e}")
            return ""
    
    async def wait_for_element(self, by: str, value: str, timeout: int = None) -> bool:
        """Element için bekle"""
        try:
            wait = WebDriverWait(self.driver, timeout or self.wait_timeout)
            wait.until(EC.presence_of_element_located((by, value)))
            return True
        except TimeoutException:
            logger.warning(f"Element bekleme zaman aşımı: {by}={value}")
            return False
        except Exception as e:
            logger.error(f"Element bekleme hatası: {e}")
            return False
    
    async def scroll_to_element(self, element) -> bool:
        """Elemente scroll yap"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            return True
        except Exception as e:
            logger.error(f"Scroll hatası: {e}")
            return False
    
    async def get_element_text(self, by: str, value: str) -> str:
        """Element metnini al"""
        try:
            element = await self.find_element(by, value)
            if element:
                return element.text
            return ""
        except Exception as e:
            logger.error(f"Element metni alma hatası: {e}")
            return ""
    
    def test_result_to_dict(self, test_result: TestResult) -> Dict[str, Any]:
        """TestResult'ı dictionary'e çevir - Gelişmiş format"""
        return {
            "platform": test_result.platform,
            "test_type": test_result.test_type,
            "start_time": test_result.start_time.isoformat() if test_result.start_time else None,
            "end_time": test_result.end_time.isoformat() if test_result.end_time else None,
            "total_duration": test_result.total_duration,
            "success": test_result.success,
            "error_count": test_result.error_count,
            "success_count": test_result.success_count,
            "element_success_rate": test_result.element_success_rate,
            "avg_step_duration": test_result.avg_step_duration,
            "total_screenshots": test_result.total_screenshots,
            "screenshots": test_result.screenshots,
            "test_summary": test_result.test_summary,
            "steps": [
                {
                    "step_type": step.step_type,
                    "description": step.description,
                    "success": step.success,
                    "error_message": step.error_message,
                    "duration": step.duration,
                    "screenshot_path": step.screenshot_path,
                    "element_found": step.element_found,
                    "element_selector_used": step.element_selector_used,
                    "wait_time": step.wait_time,
                    "retry_count": step.retry_count
                }
                for step in test_result.steps
            ]
        }
    
    async def save_test_report(self, test_result: TestResult, filename: str = None) -> str:
        """Test raporunu JSON formatında kaydet - Gelişmiş format"""
        try:
            if not filename:
                timestamp = int(time.time())
                filename = f"{test_result.platform}_test_report_{timestamp}.json"
            
            report_path = os.path.join(self.test_results_dir, filename)
            
            report_data = self.test_result_to_dict(test_result)
            
            # Custom JSON encoder for datetime objects
            class DateTimeEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    return super().default(obj)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
            
            logger.info(f"Test raporu kaydedildi: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Test raporu kaydetme hatası: {e}")
            return ""
    
    # Legacy methods for backward compatibility
    async def execute_instagram_test(self) -> Dict[str, Any]:
        """Legacy Instagram test - AI stratejisi kullan"""
        test_strategy = {
            "platform": "instagram",
            "test_type": "e2e",
            "steps": [
                "1. Instagram ana sayfasını aç",
                "2. Login formunu kontrol et",
                "3. Navigation elementlerini test et",
                "4. Content elementlerini kontrol et",
                "5. Screenshot al"
            ]
        }
        
        test_result = await self.execute_ai_strategy("instagram", test_strategy)
        return self.test_result_to_dict(test_result)
    
    async def execute_generic_test(self, url: str, test_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Legacy generic test - AI stratejisi kullan"""
        platform = url.split("//")[1].split(".")[1] if "//" in url else "web"
        
        test_strategy = {
            "platform": platform,
            "test_type": "functional",
            "steps": [step.get("description", "Test step") for step in test_steps]
        }
        
        test_result = await self.execute_ai_strategy(platform, test_strategy)
        return self.test_result_to_dict(test_result) 