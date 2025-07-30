"""
Multi-AI Engine Methods
Extended methods for multi-model AI support
"""

import logging
import json
from typing import Dict, Any, Optional
from app.integrations.multi_ai_client import multi_ai_manager, AIResponse

logger = logging.getLogger(__name__)

class MultiAIEngineMixin:
    """Mixin class for multi-AI functionality"""
    
    async def _analyze_command_with_multi_ai(self, command: str, context: Dict[str, Any] = {}, model: Optional[str] = None) -> Dict[str, Any]:
        """Multi-AI ile komut analizi - Enhanced with multiple models"""
        
        # Command analysis prompt - optimized for multiple AI models
        analysis_prompt = f"""
        Analyze the following test automation command and extract structured information.
        
        Command: "{command}"
        Context: {json.dumps(context, indent=2)}
        
        Please analyze this command and return a JSON response with the following structure:
        {{
            "intent": "test_platform|create_test|run_automation|analyze_results",
            "platform": "instagram|facebook|twitter|linkedin|youtube|tiktok|web|mobile|api",
            "test_type": "ui|functional|performance|security|accessibility|e2e|smoke|regression",
            "parameters": {{
                "browser": "chrome|firefox|safari|edge",
                "headless": true|false,
                "timeout": 30,
                "environment": "development|staging|production",
                "priority": "low|medium|high|critical",
                "tags": ["tag1", "tag2"]
            }},
            "confidence": 0.0-1.0,
            "reasoning": "Brief explanation of the analysis",
            "suggested_improvements": ["improvement1", "improvement2"]
        }}
        
        Platform Detection Rules:
        - Instagram: instagram, ig, insta, gram, story, reel, post
        - Facebook: facebook, fb, meta, wall, timeline
        - Twitter: twitter, x, tweet, thread
        - LinkedIn: linkedin, professional, network
        - YouTube: youtube, yt, video, channel
        - TikTok: tiktok, tt, short video
        - Web: general web, website, browser
        
        Test Type Detection:
        - UI: interface, button, form, visual, element, click
        - Functional: login, register, submit, process, workflow
        - Performance: speed, load, response, benchmark
        - Security: auth, permission, vulnerability, security
        - Accessibility: a11y, screen reader, keyboard, aria
        - E2E: end-to-end, complete flow, user journey
        
        Return only valid JSON without any additional text or markdown formatting.
        """
        
        try:
            # Use multi-AI manager to get response
            ai_response: AIResponse = await multi_ai_manager.generate_response(
                prompt=analysis_prompt,
                model=model,
                max_tokens=1000,
                temperature=0.3
            )
            
            logger.info(f"AI Analysis completed with {ai_response.model} (Provider: {ai_response.provider})")
            logger.info(f"Tokens used: {ai_response.tokens_used}, Cost: ${ai_response.cost:.4f}")
            
            # Parse JSON response
            try:
                analysis_data = json.loads(ai_response.content)
                
                # Add metadata from AI response
                analysis_data["ai_metadata"] = {
                    "model": ai_response.model,
                    "provider": ai_response.provider,
                    "tokens_used": ai_response.tokens_used,
                    "cost": ai_response.cost,
                    "timestamp": ai_response.timestamp.isoformat()
                }
                
                # Validate and clean data
                analysis_data = self._validate_analysis_data(analysis_data)
                
                return analysis_data
                
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed, attempting to extract JSON from response")
                return self._extract_json_from_text(ai_response.content)
                
        except Exception as e:
            logger.error(f"Multi-AI command analysis failed: {e}")
            raise
    
    async def _generate_strategy_with_multi_ai(self, ai_command, model: Optional[str] = None) -> Dict[str, Any]:
        """Multi-AI ile test stratejisi oluştur"""
        
        strategy_prompt = f"""
        Generate a comprehensive test automation strategy based on the following analysis:
        
        Command: "{ai_command.original_command}"
        Platform: {ai_command.platform}
        Test Type: {ai_command.test_type}
        Intent: {ai_command.parsed_intent}
        Parameters: {json.dumps(ai_command.parameters, indent=2)}
        
        Create a detailed test strategy in JSON format:
        {{
            "steps": [
                "Step 1: Clear, actionable test step",
                "Step 2: Include verification points",
                "Step 3: Handle error scenarios"
            ],
            "automation_script": "Complete Python/Selenium automation script",
            "priority": "low|medium|high|critical",
            "estimated_time": "5-10 minutes",
            "test_scenarios": [
                {{
                    "name": "Happy Path Test",
                    "description": "Test normal user flow",
                    "steps": ["step1", "step2"],
                    "expected_result": "Expected outcome"
                }},
                {{
                    "name": "Error Handling Test", 
                    "description": "Test error scenarios",
                    "steps": ["step1", "step2"],
                    "expected_result": "Error handling"
                }}
            ],
            "preconditions": ["Condition 1", "Condition 2"],
            "postconditions": ["Result 1", "Result 2"],
            "test_data": {{
                "valid_inputs": ["input1", "input2"],
                "invalid_inputs": ["bad_input1", "bad_input2"]
            }},
            "verification_points": [
                "Verify element exists",
                "Verify correct navigation",
                "Verify data persistence"
            ],
            "risk_analysis": {{
                "high_risk_areas": ["login", "payment", "data_submission"],
                "mitigation_strategies": ["retry_logic", "error_logging", "rollback"]
            }}
        }}
        
        Platform-Specific Guidelines:
        
        Instagram:
        - Focus on social media interactions (like, follow, post)
        - Include story and reel testing
        - Test mobile-responsive design
        - Verify image/video upload functionality
        
        Facebook:
        - Test timeline interactions
        - Include messaging features
        - Verify privacy settings
        - Test group and page functionality
        
        Twitter:
        - Focus on tweet composition and publishing
        - Test thread creation
        - Verify hashtag and mention functionality
        - Include retweet and like actions
        
        General Web:
        - Include cross-browser compatibility
        - Test responsive design
        - Verify form submissions
        - Include accessibility checks
        
        Generate comprehensive, production-ready automation code using Selenium WebDriver.
        Include proper error handling, waits, and logging.
        
        Return only valid JSON without any additional text or markdown formatting.
        """
        
        try:
            # Use multi-AI for strategy generation
            ai_response: AIResponse = await multi_ai_manager.generate_response(
                prompt=strategy_prompt,
                model=model,
                max_tokens=2500,
                temperature=0.4
            )
            
            logger.info(f"Strategy generated with {ai_response.model}")
            logger.info(f"Tokens used: {ai_response.tokens_used}, Cost: ${ai_response.cost:.4f}")
            
            # Parse JSON response
            try:
                strategy_data = json.loads(ai_response.content)
                
                # Add AI metadata
                strategy_data["ai_metadata"] = {
                    "model": ai_response.model,
                    "provider": ai_response.provider,
                    "tokens_used": ai_response.tokens_used,
                    "cost": ai_response.cost,
                    "confidence": ai_response.confidence
                }
                
                return strategy_data
                
            except json.JSONDecodeError as e:
                logger.warning(f"Strategy JSON parsing failed: {e}")
                return self._extract_strategy_from_text(ai_response.content)
                
        except Exception as e:
            logger.error(f"Multi-AI strategy generation failed: {e}")
            raise
    
    async def generate_ai_insights(self, test_results: Dict[str, Any], model: Optional[str] = None) -> Dict[str, Any]:
        """AI ile test sonuçlarından insights üret"""
        
        insights_prompt = f"""
        Analyze the following test execution results and provide intelligent insights:
        
        Test Results: {json.dumps(test_results, indent=2)}
        
        Generate insights in JSON format:
        {{
            "summary": {{
                "overall_health": "excellent|good|fair|poor",
                "success_rate": 0.0-100.0,
                "performance_grade": "A|B|C|D|F",
                "main_issues": ["issue1", "issue2"]
            }},
            "insights": [
                {{
                    "type": "performance|reliability|usability|security",
                    "title": "Insight title",
                    "description": "Detailed insight description",
                    "severity": "low|medium|high|critical",
                    "impact": "Impact description",
                    "recommendation": "Actionable recommendation"
                }}
            ],
            "trends": {{
                "performance_trend": "improving|stable|degrading",
                "reliability_trend": "improving|stable|degrading",
                "failure_patterns": ["pattern1", "pattern2"]
            }},
            "recommendations": [
                {{
                    "priority": "high|medium|low",
                    "action": "Specific action to take",
                    "expected_benefit": "Expected improvement",
                    "effort_estimate": "hours|days|weeks"
                }}
            ],
            "predictions": {{
                "likely_failures": ["potential_failure1", "potential_failure2"],
                "optimization_opportunities": ["opportunity1", "opportunity2"],
                "resource_requirements": "Resource needs assessment"
            }}
        }}
        
        Focus on:
        1. Performance bottlenecks and optimization opportunities
        2. Reliability issues and failure patterns
        3. User experience improvements
        4. Security vulnerabilities or concerns
        5. Scalability considerations
        6. Cost optimization possibilities
        
        Return only valid JSON without any additional text.
        """
        
        try:
            ai_response: AIResponse = await multi_ai_manager.generate_response(
                prompt=insights_prompt,
                model=model,
                max_tokens=1500,
                temperature=0.5
            )
            
            insights_data = json.loads(ai_response.content)
            
            # Add metadata
            insights_data["ai_metadata"] = {
                "model": ai_response.model,
                "provider": ai_response.provider,
                "analysis_timestamp": ai_response.timestamp.isoformat(),
                "confidence": ai_response.confidence
            }
            
            return insights_data
            
        except Exception as e:
            logger.error(f"AI insights generation failed: {e}")
            return self._default_insights()
    
    async def optimize_test_suite(self, test_suite_data: Dict[str, Any], model: Optional[str] = None) -> Dict[str, Any]:
        """AI ile test suite optimizasyonu"""
        
        optimization_prompt = f"""
        Analyze this test suite and provide optimization recommendations:
        
        Test Suite Data: {json.dumps(test_suite_data, indent=2)}
        
        Provide optimization suggestions in JSON format:
        {{
            "current_analysis": {{
                "total_tests": 0,
                "execution_time": "00:00:00",
                "redundancy_score": 0.0-1.0,
                "coverage_gaps": ["gap1", "gap2"],
                "efficiency_score": 0.0-1.0
            }},
            "optimizations": [
                {{
                    "type": "parallelization|deduplication|prioritization|refactoring",
                    "description": "What to optimize",
                    "impact": "Expected improvement",
                    "effort": "Implementation effort",
                    "time_savings": "Expected time reduction"
                }}
            ],
            "test_prioritization": [
                {{
                    "test_name": "Test name",
                    "priority": "critical|high|medium|low",
                    "reasoning": "Why this priority",
                    "frequency": "every_commit|daily|weekly|monthly"
                }}
            ],
            "parallel_execution_plan": {{
                "parallel_groups": [
                    {{
                        "group_name": "Group 1",
                        "tests": ["test1", "test2"],
                        "estimated_time": "00:05:00",
                        "dependencies": []
                    }}
                ],
                "max_parallelism": 4,
                "resource_requirements": "Resource needs"
            }},
            "cost_optimization": {{
                "current_cost": 0.0,
                "optimized_cost": 0.0,
                "savings": 0.0,
                "recommendations": ["rec1", "rec2"]
            }}
        }}
        
        Return only valid JSON.
        """
        
        try:
            ai_response: AIResponse = await multi_ai_manager.generate_response(
                prompt=optimization_prompt,
                model=model,
                max_tokens=2000,
                temperature=0.3
            )
            
            return json.loads(ai_response.content)
            
        except Exception as e:
            logger.error(f"Test suite optimization failed: {e}")
            return self._default_optimization()
    
    def _validate_analysis_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean analysis data"""
        # Set defaults for missing fields
        defaults = {
            "intent": "unknown",
            "platform": None,
            "test_type": "functional",
            "parameters": {},
            "confidence": 0.7,
            "reasoning": "AI analysis completed",
            "suggested_improvements": []
        }
        
        for key, default_value in defaults.items():
            if key not in data:
                data[key] = default_value
        
        # Validate enum values
        valid_platforms = ["instagram", "facebook", "twitter", "linkedin", "youtube", "tiktok", "web", "mobile", "api"]
        if data["platform"] and data["platform"] not in valid_platforms:
            data["platform"] = None
        
        valid_test_types = ["ui", "functional", "performance", "security", "accessibility", "e2e", "smoke", "regression"]
        if data["test_type"] not in valid_test_types:
            data["test_type"] = "functional"
        
        # Ensure confidence is in valid range
        if not isinstance(data["confidence"], (int, float)) or data["confidence"] < 0 or data["confidence"] > 1:
            data["confidence"] = 0.7
        
        return data
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text response when direct parsing fails"""
        try:
            # Try to find JSON in text
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Return fallback data
        return {
            "intent": "test_platform",
            "platform": None,
            "test_type": "functional",
            "parameters": {},
            "confidence": 0.5,
            "reasoning": "Fallback analysis due to parsing error"
        }
    
    def _extract_strategy_from_text(self, text: str) -> Dict[str, Any]:
        """Extract strategy from text when JSON parsing fails"""
        return {
            "steps": [
                "1. Navigate to target platform",
                "2. Verify page loading",
                "3. Perform test actions",
                "4. Validate results"
            ],
            "automation_script": "# Fallback automation script\nprint('Test execution')",
            "priority": "medium",
            "estimated_time": "5-10 minutes",
            "test_scenarios": [
                {
                    "name": "Basic Test",
                    "description": "Basic functionality test",
                    "steps": ["Navigate", "Test", "Verify"],
                    "expected_result": "Success"
                }
            ]
        }
    
    def _default_insights(self) -> Dict[str, Any]:
        """Default insights when AI generation fails"""
        return {
            "summary": {
                "overall_health": "fair",
                "success_rate": 50.0,
                "performance_grade": "C",
                "main_issues": ["Insufficient data for analysis"]
            },
            "insights": [
                {
                    "type": "reliability",
                    "title": "Data Collection Needed",
                    "description": "More test data needed for meaningful insights",
                    "severity": "medium",
                    "impact": "Limited insight generation",
                    "recommendation": "Execute more tests to gather data"
                }
            ],
            "recommendations": [
                {
                    "priority": "medium",
                    "action": "Increase test execution frequency",
                    "expected_benefit": "Better insights and analysis",
                    "effort_estimate": "days"
                }
            ]
        }
    
    def _default_optimization(self) -> Dict[str, Any]:
        """Default optimization when AI generation fails"""
        return {
            "current_analysis": {
                "total_tests": 0,
                "execution_time": "00:00:00",
                "redundancy_score": 0.0,
                "coverage_gaps": ["Unknown"],
                "efficiency_score": 0.5
            },
            "optimizations": [
                {
                    "type": "analysis",
                    "description": "Analyze test suite structure",
                    "impact": "Baseline understanding",
                    "effort": "Low",
                    "time_savings": "TBD"
                }
            ]
        }
    
    async def get_ai_health_status(self) -> Dict[str, Any]:
        """Get health status of all AI providers"""
        return await multi_ai_manager.health_check_all()
    
    def get_available_ai_models(self) -> Dict[str, Any]:
        """Get list of available AI models"""
        models = multi_ai_manager.get_available_models()
        return {
            "available_models": models,
            "total_models": len(models),
            "providers": list(set(model.get("provider", "unknown") for model in models)),
            "fallback_order": multi_ai_manager.fallback_order,
            "load_balancing_enabled": multi_ai_manager.load_balancing
        }