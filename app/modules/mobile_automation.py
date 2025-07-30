"""
Mobile Automation Module
Appium-based mobile testing for iOS and Android platforms
"""

import asyncio
import logging
import json
import time
import os
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from app.core.performance import monitor_function, PerformanceContext

logger = logging.getLogger(__name__)

class MobilePlatform(str, Enum):
    """Supported mobile platforms"""
    ANDROID = "android"
    IOS = "ios"

class DeviceOrientation(str, Enum):
    """Device orientation options"""
    PORTRAIT = "PORTRAIT"
    LANDSCAPE = "LANDSCAPE"

@dataclass
class MobileDevice:
    """Mobile device configuration"""
    platform: MobilePlatform
    device_name: str
    platform_version: str
    app_package: Optional[str] = None
    app_activity: Optional[str] = None
    bundle_id: Optional[str] = None
    udid: Optional[str] = None
    automation_name: Optional[str] = None
    
    def to_capabilities(self) -> Dict[str, Any]:
        """Convert to Appium capabilities"""
        caps = {
            "platformName": self.platform.value.capitalize(),
            "deviceName": self.device_name,
            "platformVersion": self.platform_version,
        }
        
        if self.platform == MobilePlatform.ANDROID:
            caps["automationName"] = self.automation_name or "UiAutomator2"
            if self.app_package:
                caps["appPackage"] = self.app_package
            if self.app_activity:
                caps["appActivity"] = self.app_activity
        elif self.platform == MobilePlatform.IOS:
            caps["automationName"] = self.automation_name or "XCUITest"
            if self.bundle_id:
                caps["bundleId"] = self.bundle_id
        
        if self.udid:
            caps["udid"] = self.udid
            
        return caps

@dataclass
class MobileTestResult:
    """Mobile test execution result"""
    success: bool
    device: MobileDevice
    platform: str
    test_duration: float
    steps_executed: List[Dict[str, Any]]
    errors: List[str]
    screenshots: List[str]
    performance_metrics: Dict[str, Any]
    app_info: Dict[str, Any]
    network_logs: List[Dict[str, Any]]
    test_metadata: Dict[str, Any]
    timestamp: datetime

class MobileAutomation:
    """Advanced mobile automation with Appium"""
    
    def __init__(self, appium_server_url: str = "http://localhost:4723"):
        self.appium_server_url = appium_server_url
        self.driver = None
        self.wait_timeout = 30
        self.current_device = None
        self.test_results_dir = "mobile_test_results"
        self.screenshots_dir = "mobile_screenshots"
        
        # Create directories
        os.makedirs(self.test_results_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # Mobile app selectors for popular apps
        self.mobile_app_selectors = {
            "instagram": {
                "android": {
                    "login_email": "com.instagram.android:id/login_username",
                    "login_password": "com.instagram.android:id/password",
                    "login_button": "com.instagram.android:id/button_text",
                    "search_tab": "com.instagram.android:id/tab_search",
                    "search_input": "com.instagram.android:id/action_bar_search_edit_text",
                    "profile_tab": "com.instagram.android:id/tab_avatar",
                    "post_button": "com.instagram.android:id/camera_tab",
                    "story_camera": "com.instagram.android:id/stories_camera_tab"
                },
                "ios": {
                    "login_email": "//XCUIElementTypeTextField[@name='Email or phone number']",
                    "login_password": "//XCUIElementTypeSecureTextField[@name='Password']",
                    "login_button": "//XCUIElementTypeButton[@name='Log In']",
                    "search_tab": "//XCUIElementTypeButton[@name='Search and Explore']",
                    "search_input": "//XCUIElementTypeSearchField[@name='Search']",
                    "profile_tab": "//XCUIElementTypeButton[@name='Profile']",
                    "post_button": "//XCUIElementTypeButton[@name='Plus']",
                    "story_camera": "//XCUIElementTypeButton[@name='Your Story']"
                }
            },
            "whatsapp": {
                "android": {
                    "chat_list": "com.whatsapp:id/conversations_recycler_view",
                    "new_chat": "com.whatsapp:id/fab",
                    "search_chat": "com.whatsapp:id/search",
                    "message_input": "com.whatsapp:id/entry",
                    "send_button": "com.whatsapp:id/send",
                    "attach_button": "com.whatsapp:id/input_attach_button"
                },
                "ios": {
                    "chat_list": "//XCUIElementTypeTable[@name='ChatListTableView']",
                    "new_chat": "//XCUIElementTypeButton[@name='Compose']",
                    "search_chat": "//XCUIElementTypeSearchField[@name='Search']",
                    "message_input": "//XCUIElementTypeTextView[@name='Message']",
                    "send_button": "//XCUIElementTypeButton[@name='Send']",
                    "attach_button": "//XCUIElementTypeButton[@name='Attach']"
                }
            },
            "facebook": {
                "android": {
                    "news_feed": "com.facebook.katana:id/news_feed_recycler_view",
                    "post_status": "com.facebook.katana:id/status_text",
                    "notifications": "com.facebook.katana:id/notifications_jewel",
                    "menu": "com.facebook.katana:id/bookmarks_jewel",
                    "search": "com.facebook.katana:id/search",
                    "profile": "com.facebook.katana:id/profile_jewel"
                },
                "ios": {
                    "news_feed": "//XCUIElementTypeTable[@name='News Feed']",
                    "post_status": "//XCUIElementTypeButton[@name='What\\'s on your mind?']",
                    "notifications": "//XCUIElementTypeButton[@name='Notifications']",
                    "menu": "//XCUIElementTypeButton[@name='Menu']",
                    "search": "//XCUIElementTypeButton[@name='Search']",
                    "profile": "//XCUIElementTypeButton[@name='Profile']"
                }
            }
        }
    
    @monitor_function
    async def setup_driver(self, device: MobileDevice) -> bool:
        """Setup Appium WebDriver for mobile device"""
        try:
            self.current_device = device
            
            # Create appropriate options based on platform
            if device.platform == MobilePlatform.ANDROID:
                options = UiAutomator2Options()
            else:
                options = XCUITestOptions()
            
            # Load capabilities
            capabilities = device.to_capabilities()
            for key, value in capabilities.items():
                options.set_capability(key, value)
            
            # Additional common capabilities
            options.set_capability("newCommandTimeout", 300)
            options.set_capability("noReset", True)
            options.set_capability("fullReset", False)
            options.set_capability("autoGrantPermissions", True)
            
            # Performance and logging capabilities
            options.set_capability("enablePerformanceLogging", True)
            options.set_capability("printPageSourceOnFindFailure", True)
            
            # Create driver
            self.driver = webdriver.Remote(self.appium_server_url, options=options)
            self.driver.implicitly_wait(10)
            
            logger.info(f"Mobile driver setup successful for {device.device_name} ({device.platform})")
            return True
            
        except Exception as e:
            logger.error(f"Mobile driver setup failed: {e}")
            return False
    
    @monitor_function
    async def close_driver(self):
        """Close mobile WebDriver"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.current_device = None
                logger.info("Mobile driver closed successfully")
        except Exception as e:
            logger.error(f"Error closing mobile driver: {e}")
    
    @monitor_function
    async def take_screenshot(self, filename: str = None) -> str:
        """Take mobile screenshot"""
        try:
            if not self.driver:
                raise Exception("Driver not initialized")
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"mobile_screenshot_{timestamp}.png"
            
            screenshot_path = os.path.join(self.screenshots_dir, filename)
            self.driver.save_screenshot(screenshot_path)
            
            logger.info(f"Mobile screenshot saved: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Error taking mobile screenshot: {e}")
            return ""
    
    @monitor_function
    async def find_element_by_selector(self, selector: str, timeout: int = None) -> Any:
        """Find mobile element by selector"""
        try:
            wait_time = timeout or self.wait_timeout
            wait = WebDriverWait(self.driver, wait_time)
            
            # Determine selector type
            if selector.startswith("//"):
                # XPath
                element = wait.until(EC.presence_of_element_located((AppiumBy.XPATH, selector)))
            elif ":" in selector:
                # Resource ID (Android)
                element = wait.until(EC.presence_of_element_located((AppiumBy.ID, selector)))
            else:
                # Accessibility ID
                element = wait.until(EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, selector)))
            
            return element
            
        except TimeoutException:
            logger.warning(f"Mobile element not found with selector: {selector}")
            return None
        except Exception as e:
            logger.error(f"Error finding mobile element: {e}")
            return None
    
    @monitor_function
    async def tap_element(self, selector: str, timeout: int = None) -> bool:
        """Tap mobile element"""
        try:
            element = await self.find_element_by_selector(selector, timeout)
            if element:
                element.click()
                await asyncio.sleep(1)  # Brief wait after tap
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error tapping mobile element: {e}")
            return False
    
    @monitor_function
    async def send_text(self, selector: str, text: str, timeout: int = None) -> bool:
        """Send text to mobile element"""
        try:
            element = await self.find_element_by_selector(selector, timeout)
            if element:
                element.clear()
                element.send_keys(text)
                await asyncio.sleep(0.5)
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error sending text to mobile element: {e}")
            return False
    
    @monitor_function
    async def swipe_screen(self, direction: str, duration: int = 1000) -> bool:
        """Swipe screen in specified direction"""
        try:
            if not self.driver:
                return False
            
            size = self.driver.get_window_size()
            width = size['width']
            height = size['height']
            
            # Calculate swipe coordinates
            if direction.lower() == "up":
                start_x, start_y = width // 2, height * 0.8
                end_x, end_y = width // 2, height * 0.2
            elif direction.lower() == "down":
                start_x, start_y = width // 2, height * 0.2
                end_x, end_y = width // 2, height * 0.8
            elif direction.lower() == "left":
                start_x, start_y = width * 0.8, height // 2
                end_x, end_y = width * 0.2, height // 2
            elif direction.lower() == "right":
                start_x, start_y = width * 0.2, height // 2
                end_x, end_y = width * 0.8, height // 2
            else:
                logger.error(f"Invalid swipe direction: {direction}")
                return False
            
            # Perform swipe
            self.driver.swipe(start_x, start_y, end_x, end_y, duration)
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"Error swiping screen: {e}")
            return False
    
    @monitor_function
    async def rotate_device(self, orientation: DeviceOrientation) -> bool:
        """Rotate device to specified orientation"""
        try:
            if not self.driver:
                return False
            
            self.driver.orientation = orientation.value
            await asyncio.sleep(2)  # Wait for rotation to complete
            return True
            
        except Exception as e:
            logger.error(f"Error rotating device: {e}")
            return False
    
    @monitor_function
    async def get_app_info(self) -> Dict[str, Any]:
        """Get current app information"""
        try:
            if not self.driver:
                return {}
            
            app_info = {
                "current_activity": getattr(self.driver, 'current_activity', 'unknown'),
                "current_package": getattr(self.driver, 'current_package', 'unknown'),
                "orientation": getattr(self.driver, 'orientation', 'unknown'),
                "window_size": self.driver.get_window_size(),
                "platform_version": self.current_device.platform_version if self.current_device else 'unknown',
                "device_name": self.current_device.device_name if self.current_device else 'unknown'
            }
            
            return app_info
            
        except Exception as e:
            logger.error(f"Error getting app info: {e}")
            return {}
    
    @monitor_function
    async def execute_mobile_strategy(self, app_name: str, test_strategy: Dict[str, Any]) -> MobileTestResult:
        """Execute mobile test strategy for specified app"""
        start_time = time.time()
        steps_executed = []
        errors = []
        screenshots = []
        
        try:
            if not self.driver or not self.current_device:
                raise Exception("Mobile driver not initialized")
            
            # Take initial screenshot
            initial_screenshot = await self.take_screenshot(f"{app_name}_initial.png")
            if initial_screenshot:
                screenshots.append(initial_screenshot)
            
            # Get app selectors
            platform_key = self.current_device.platform.value
            app_selectors = self.mobile_app_selectors.get(app_name, {}).get(platform_key, {})
            
            if not app_selectors:
                raise Exception(f"No selectors found for {app_name} on {platform_key}")
            
            # Execute test steps
            test_steps = test_strategy.get("steps", [])
            
            for i, step in enumerate(test_steps):
                step_start_time = time.time()
                step_success = False
                step_error = None
                
                try:
                    with PerformanceContext(f"mobile_test_step_{i}", {"step": step, "app": app_name}):
                        step_success = await self._execute_mobile_step(step, app_selectors)
                    
                    if step_success:
                        # Take screenshot after successful step
                        step_screenshot = await self.take_screenshot(f"{app_name}_step_{i}.png")
                        if step_screenshot:
                            screenshots.append(step_screenshot)
                    
                except Exception as e:
                    step_error = str(e)
                    errors.append(f"Step {i+1}: {step_error}")
                    logger.error(f"Mobile test step {i+1} failed: {e}")
                
                step_duration = time.time() - step_start_time
                steps_executed.append({
                    "step_number": i + 1,
                    "step_description": step,
                    "duration": step_duration,
                    "success": step_success,
                    "error": step_error
                })
                
                # Brief pause between steps
                await asyncio.sleep(1)
            
            # Get final app info and performance metrics
            app_info = await self.get_app_info()
            performance_metrics = self._calculate_mobile_performance_metrics(steps_executed)
            
            test_duration = time.time() - start_time
            success = len(errors) == 0
            
            # Take final screenshot
            final_screenshot = await self.take_screenshot(f"{app_name}_final.png")
            if final_screenshot:
                screenshots.append(final_screenshot)
            
            result = MobileTestResult(
                success=success,
                device=self.current_device,
                platform=platform_key,
                test_duration=test_duration,
                steps_executed=steps_executed,
                errors=errors,
                screenshots=screenshots,
                performance_metrics=performance_metrics,
                app_info=app_info,
                network_logs=[],  # Would require additional setup
                test_metadata={
                    "app_name": app_name,
                    "strategy": test_strategy,
                    "appium_server": self.appium_server_url
                },
                timestamp=datetime.now()
            )
            
            logger.info(f"Mobile test completed for {app_name}: {success}")
            return result
            
        except Exception as e:
            test_duration = time.time() - start_time
            errors.append(f"Mobile test execution error: {str(e)}")
            logger.error(f"Mobile test execution failed: {e}")
            
            return MobileTestResult(
                success=False,
                device=self.current_device or MobileDevice(MobilePlatform.ANDROID, "unknown", "unknown"),
                platform=platform_key if self.current_device else "unknown",
                test_duration=test_duration,
                steps_executed=steps_executed,
                errors=errors,
                screenshots=screenshots,
                performance_metrics={},
                app_info={},
                network_logs=[],
                test_metadata={"app_name": app_name, "strategy": test_strategy},
                timestamp=datetime.now()
            )
    
    async def _execute_mobile_step(self, step: str, selectors: Dict[str, str]) -> bool:
        """Execute individual mobile test step"""
        step_lower = step.lower()
        
        try:
            if "tap" in step_lower or "click" in step_lower:
                # Extract element to tap
                for key, selector in selectors.items():
                    if key in step_lower:
                        return await self.tap_element(selector)
                return False
                
            elif "type" in step_lower or "enter" in step_lower:
                # Extract text to type and element
                parts = step.split('"')
                if len(parts) >= 2:
                    text = parts[1]
                    for key, selector in selectors.items():
                        if key in step_lower:
                            return await self.send_text(selector, text)
                return False
                
            elif "swipe" in step_lower:
                # Extract swipe direction
                directions = ["up", "down", "left", "right"]
                for direction in directions:
                    if direction in step_lower:
                        return await self.swipe_screen(direction)
                return False
                
            elif "rotate" in step_lower:
                # Extract rotation
                if "landscape" in step_lower:
                    return await self.rotate_device(DeviceOrientation.LANDSCAPE)
                elif "portrait" in step_lower:
                    return await self.rotate_device(DeviceOrientation.PORTRAIT)
                return False
                
            elif "wait" in step_lower:
                # Extract wait time
                import re
                numbers = re.findall(r'\d+', step)
                wait_time = int(numbers[0]) if numbers else 2
                await asyncio.sleep(wait_time)
                return True
                
            else:
                logger.warning(f"Unknown mobile step: {step}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing mobile step '{step}': {e}")
            return False
    
    def _calculate_mobile_performance_metrics(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate mobile test performance metrics"""
        total_steps = len(steps)
        successful_steps = sum(1 for step in steps if step['success'])
        failed_steps = total_steps - successful_steps
        
        step_durations = [step['duration'] for step in steps]
        avg_step_duration = sum(step_durations) / len(step_durations) if step_durations else 0
        max_step_duration = max(step_durations) if step_durations else 0
        min_step_duration = min(step_durations) if step_durations else 0
        
        return {
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "failed_steps": failed_steps,
            "success_rate": (successful_steps / total_steps * 100) if total_steps > 0 else 0,
            "average_step_duration": avg_step_duration,
            "max_step_duration": max_step_duration,
            "min_step_duration": min_step_duration,
            "total_test_duration": sum(step_durations)
        }
    
    @monitor_function
    async def save_mobile_test_report(self, result: MobileTestResult, filename: str) -> str:
        """Save mobile test results to JSON file"""
        try:
            report_path = os.path.join(self.test_results_dir, filename)
            
            # Convert result to dict
            report_data = {
                "success": result.success,
                "device_info": {
                    "platform": result.device.platform.value,
                    "device_name": result.device.device_name,
                    "platform_version": result.device.platform_version,
                    "app_package": result.device.app_package,
                    "app_activity": result.device.app_activity,
                    "bundle_id": result.device.bundle_id
                },
                "test_duration": result.test_duration,
                "steps_executed": result.steps_executed,
                "errors": result.errors,
                "screenshots": result.screenshots,
                "performance_metrics": result.performance_metrics,
                "app_info": result.app_info,
                "network_logs": result.network_logs,
                "test_metadata": result.test_metadata,
                "timestamp": result.timestamp.isoformat()
            }
            
            # Save to file
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Mobile test report saved: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Error saving mobile test report: {e}")
            return ""
    
    def mobile_test_result_to_dict(self, result: MobileTestResult) -> Dict[str, Any]:
        """Convert MobileTestResult to dictionary"""
        return {
            "success": result.success,
            "device": {
                "platform": result.device.platform.value,
                "device_name": result.device.device_name,
                "platform_version": result.device.platform_version
            },
            "platform": result.platform,
            "test_duration": result.test_duration,
            "steps_executed": result.steps_executed,
            "errors": result.errors,
            "screenshots": result.screenshots,
            "performance_metrics": result.performance_metrics,
            "app_info": result.app_info,
            "timestamp": result.timestamp.isoformat()
        }
    
    @monitor_function
    async def get_available_devices(self) -> List[Dict[str, Any]]:
        """Get list of available mobile devices"""
        try:
            # This would typically query ADB for Android devices
            # and ios-deploy or similar for iOS devices
            # For now, return example devices
            
            available_devices = [
                {
                    "platform": "android",
                    "device_name": "Android Emulator",
                    "platform_version": "11.0",
                    "udid": "emulator-5554",
                    "status": "available"
                },
                {
                    "platform": "ios", 
                    "device_name": "iPhone Simulator",
                    "platform_version": "15.0",
                    "udid": "simulator-id",
                    "status": "available"
                }
            ]
            
            return available_devices
            
        except Exception as e:
            logger.error(f"Error getting available devices: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Check mobile automation system health"""
        try:
            health_status = {
                "appium_server": self.appium_server_url,
                "driver_status": "connected" if self.driver else "disconnected",
                "current_device": self.current_device.device_name if self.current_device else None,
                "test_results_dir": self.test_results_dir,
                "screenshots_dir": self.screenshots_dir,
                "available_apps": list(self.mobile_app_selectors.keys())
            }
            
            # Try to get available devices
            try:
                devices = await self.get_available_devices()
                health_status["available_devices"] = len(devices)
                health_status["device_list"] = devices
            except:
                health_status["available_devices"] = 0
                health_status["device_list"] = []
            
            return {
                "status": "healthy",
                "mobile_automation": health_status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }