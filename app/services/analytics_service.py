"""
Analytics Service
Advanced test analytics and metrics calculation
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload
import logging
from collections import defaultdict

from app.core.database import get_db_session
from app.models.analytics import TestExecution, TestSuite, Analytics, DashboardMetrics, TestStatus
from app.models.analytics import TestExecutionResponse, AnalyticsResponse

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Advanced analytics service for test metrics"""
    
    def __init__(self):
        self.cache_duration = 300  # 5 minutes cache
        self._cache = {}
    
    async def get_dashboard_metrics(self) -> DashboardMetrics:
        """Get comprehensive dashboard metrics"""
        cache_key = "dashboard_metrics"
        
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_duration):
                return cached_data
        
        try:
            async with get_db_session() as session:
                # Get date ranges
                today = datetime.now().date()
                week_ago = today - timedelta(days=7)
                yesterday = today - timedelta(days=1)
                
                # Overview metrics
                overview_metrics = await self._get_overview_metrics(session, today, week_ago)
                
                # Performance metrics
                performance_metrics = await self._get_performance_metrics(session, today)
                
                # Distribution metrics
                distribution_metrics = await self._get_distribution_metrics(session, today)
                
                # Trend data
                trend_data = await self._get_trend_data(session, week_ago)
                
                # Recent activities
                recent_data = await self._get_recent_activities(session)
                
                # AI insights
                ai_insights = await self._get_ai_insights(session, today)
                
                # Combine metrics
                dashboard_metrics = DashboardMetrics(
                    **overview_metrics,
                    **performance_metrics,
                    **distribution_metrics,
                    **trend_data,
                    **recent_data,
                    **ai_insights
                )
                
                # Cache result
                self._cache[cache_key] = (dashboard_metrics, datetime.now())
                
                return dashboard_metrics
                
        except Exception as e:
            logger.error(f"Error getting dashboard metrics: {e}")
            return DashboardMetrics()
    
    async def _get_overview_metrics(self, session: AsyncSession, today: datetime.date, week_ago: datetime.date) -> Dict[str, Any]:
        """Get overview metrics (totals, success rates)"""
        
        # Today's tests
        today_query = select(
            func.count(TestExecution.id).label('total'),
            func.count(TestExecution.id).filter(TestExecution.status == TestStatus.PASSED).label('passed')
        ).where(func.date(TestExecution.start_time) == today)
        
        today_result = await session.execute(today_query)
        today_data = today_result.first()
        
        # Week's tests
        week_query = select(
            func.count(TestExecution.id).label('total'),
            func.count(TestExecution.id).filter(TestExecution.status == TestStatus.PASSED).label('passed')
        ).where(func.date(TestExecution.start_time) >= week_ago)
        
        week_result = await session.execute(week_query)
        week_data = week_result.first()
        
        return {
            'total_tests_today': today_data.total or 0,
            'total_tests_week': week_data.total or 0,
            'success_rate_today': (today_data.passed / today_data.total * 100) if today_data.total > 0 else 0.0,
            'success_rate_week': (week_data.passed / week_data.total * 100) if week_data.total > 0 else 0.0,
        }
    
    async def _get_performance_metrics(self, session: AsyncSession, today: datetime.date) -> Dict[str, Any]:
        """Get performance metrics (duration, speed)"""
        
        performance_query = select(
            func.avg(TestExecution.duration).label('avg_duration'),
            func.min(TestExecution.duration).label('min_duration'),
            func.max(TestExecution.duration).label('max_duration')
        ).where(
            and_(
                func.date(TestExecution.start_time) == today,
                TestExecution.duration.isnot(None)
            )
        )
        
        result = await session.execute(performance_query)
        data = result.first()
        
        return {
            'average_duration_today': round(data.avg_duration, 2) if data.avg_duration else None,
            'fastest_test_today': round(data.min_duration, 2) if data.min_duration else None,
            'slowest_test_today': round(data.max_duration, 2) if data.max_duration else None,
        }
    
    async def _get_distribution_metrics(self, session: AsyncSession, today: datetime.date) -> Dict[str, Any]:
        """Get distribution metrics (platforms, test types)"""
        
        # Platform distribution
        platform_query = select(
            TestExecution.platform,
            func.count(TestExecution.id).label('count')
        ).where(
            func.date(TestExecution.start_time) == today
        ).group_by(TestExecution.platform)
        
        platform_result = await session.execute(platform_query)
        platform_distribution = {row.platform or 'unknown': row.count for row in platform_result}
        
        # Test type distribution
        type_query = select(
            TestExecution.test_type,
            func.count(TestExecution.id).label('count')
        ).where(
            func.date(TestExecution.start_time) == today
        ).group_by(TestExecution.test_type)
        
        type_result = await session.execute(type_query)
        test_type_distribution = {row.test_type: row.count for row in type_result}
        
        return {
            'platform_distribution': platform_distribution,
            'test_type_distribution': test_type_distribution,
        }
    
    async def _get_trend_data(self, session: AsyncSession, week_ago: datetime.date) -> Dict[str, Any]:
        """Get trend data (daily, hourly)"""
        
        # Daily trend (last 7 days)
        daily_query = select(
            func.date(TestExecution.start_time).label('date'),
            func.count(TestExecution.id).label('total'),
            func.count(TestExecution.id).filter(TestExecution.status == TestStatus.PASSED).label('passed'),
            func.avg(TestExecution.duration).label('avg_duration')
        ).where(
            func.date(TestExecution.start_time) >= week_ago
        ).group_by(func.date(TestExecution.start_time)).order_by('date')
        
        daily_result = await session.execute(daily_query)
        daily_trend = []
        for row in daily_result:
            daily_trend.append({
                'date': row.date.isoformat(),
                'total': row.total,
                'passed': row.passed,
                'success_rate': (row.passed / row.total * 100) if row.total > 0 else 0,
                'avg_duration': round(row.avg_duration, 2) if row.avg_duration else 0
            })
        
        # Hourly trend (last 24 hours)
        yesterday = datetime.now() - timedelta(hours=24)
        hourly_query = select(
            func.extract('hour', TestExecution.start_time).label('hour'),
            func.count(TestExecution.id).label('total'),
            func.count(TestExecution.id).filter(TestExecution.status == TestStatus.PASSED).label('passed')
        ).where(
            TestExecution.start_time >= yesterday
        ).group_by(func.extract('hour', TestExecution.start_time)).order_by('hour')
        
        hourly_result = await session.execute(hourly_query)
        hourly_trend = []
        for row in hourly_result:
            hourly_trend.append({
                'hour': int(row.hour),
                'total': row.total,
                'passed': row.passed,
                'success_rate': (row.passed / row.total * 100) if row.total > 0 else 0
            })
        
        return {
            'daily_trend': daily_trend,
            'hourly_trend': hourly_trend,
        }
    
    async def _get_recent_activities(self, session: AsyncSession) -> Dict[str, Any]:
        """Get recent test activities"""
        
        # Recent executions (last 10)
        recent_executions_query = select(TestExecution).order_by(
            desc(TestExecution.start_time)
        ).limit(10)
        
        recent_executions_result = await session.execute(recent_executions_query)
        recent_executions = [
            TestExecutionResponse.from_orm(execution) 
            for execution in recent_executions_result.scalars()
        ]
        
        # Recent failures (last 10)
        recent_failures_query = select(TestExecution).where(
            TestExecution.status == TestStatus.FAILED
        ).order_by(desc(TestExecution.start_time)).limit(10)
        
        recent_failures_result = await session.execute(recent_failures_query)
        recent_failures = [
            TestExecutionResponse.from_orm(execution) 
            for execution in recent_failures_result.scalars()
        ]
        
        return {
            'recent_executions': recent_executions,
            'recent_failures': recent_failures,
        }
    
    async def _get_ai_insights(self, session: AsyncSession, today: datetime.date) -> Dict[str, Any]:
        """Get AI-powered insights"""
        
        # Get AI confidence averages and suggestions
        ai_query = select(
            func.avg(TestExecution.ai_confidence).label('avg_confidence'),
            func.count(TestExecution.ai_suggestions).filter(TestExecution.ai_suggestions.isnot(None)).label('suggestions_count')
        ).where(func.date(TestExecution.start_time) == today)
        
        ai_result = await session.execute(ai_query)
        ai_data = ai_result.first()
        
        # Generate insights
        ai_insights = []
        improvement_suggestions = []
        
        if ai_data.avg_confidence:
            if ai_data.avg_confidence < 0.7:
                ai_insights.append({
                    'type': 'warning',
                    'title': 'Low AI Confidence',
                    'message': f'Average AI confidence is {ai_data.avg_confidence:.1%}. Consider reviewing test strategies.',
                    'action': 'Review failing tests and optimize AI prompts'
                })
                improvement_suggestions.append('Review and optimize AI test prompts for better accuracy')
        
        # Get error patterns
        error_query = select(
            TestExecution.error_category,
            func.count(TestExecution.id).label('count')
        ).where(
            and_(
                func.date(TestExecution.start_time) == today,
                TestExecution.status == TestStatus.FAILED,
                TestExecution.error_category.isnot(None)
            )
        ).group_by(TestExecution.error_category)
        
        error_result = await session.execute(error_query)
        error_patterns = {row.error_category: row.count for row in error_result}
        
        if error_patterns:
            most_common_error = max(error_patterns, key=error_patterns.get)
            ai_insights.append({
                'type': 'info',
                'title': 'Common Error Pattern',
                'message': f'Most common error today: {most_common_error} ({error_patterns[most_common_error]} occurrences)',
                'action': f'Focus on fixing {most_common_error} errors'
            })
            improvement_suggestions.append(f'Address {most_common_error} errors to improve success rate')
        
        return {
            'ai_insights': ai_insights,
            'improvement_suggestions': improvement_suggestions,
        }
    
    async def record_test_execution(self, test_data: Dict[str, Any]) -> TestExecution:
        """Record a new test execution"""
        try:
            async with get_db_session() as session:
                execution = TestExecution(**test_data)
                session.add(execution)
                await session.commit()
                await session.refresh(execution)
                
                # Clear cache to force refresh
                if 'dashboard_metrics' in self._cache:
                    del self._cache['dashboard_metrics']
                
                return execution
                
        except Exception as e:
            logger.error(f"Error recording test execution: {e}")
            raise
    
    async def update_test_execution(self, execution_id: int, update_data: Dict[str, Any]) -> Optional[TestExecution]:
        """Update test execution with results"""
        try:
            async with get_db_session() as session:
                query = select(TestExecution).where(TestExecution.id == execution_id)
                result = await session.execute(query)
                execution = result.scalar_one_or_none()
                
                if execution:
                    for key, value in update_data.items():
                        setattr(execution, key, value)
                    
                    await session.commit()
                    await session.refresh(execution)
                    
                    # Clear cache
                    if 'dashboard_metrics' in self._cache:
                        del self._cache['dashboard_metrics']
                    
                    return execution
                
        except Exception as e:
            logger.error(f"Error updating test execution: {e}")
            raise
        
        return None
    
    async def get_analytics_data(self, date_from: datetime, date_to: datetime, metric_type: str = "daily") -> List[AnalyticsResponse]:
        """Get analytics data for date range"""
        try:
            async with get_db_session() as session:
                query = select(Analytics).where(
                    and_(
                        Analytics.date >= date_from,
                        Analytics.date <= date_to,
                        Analytics.metric_type == metric_type
                    )
                ).order_by(Analytics.date)
                
                result = await session.execute(query)
                analytics_data = [
                    AnalyticsResponse.from_orm(analytics) 
                    for analytics in result.scalars()
                ]
                
                return analytics_data
                
        except Exception as e:
            logger.error(f"Error getting analytics data: {e}")
            return []
    
    async def generate_daily_analytics(self, target_date: datetime.date = None) -> Analytics:
        """Generate daily analytics aggregation"""
        if not target_date:
            target_date = datetime.now().date()
        
        try:
            async with get_db_session() as session:
                # Get all executions for the day
                executions_query = select(TestExecution).where(
                    func.date(TestExecution.start_time) == target_date
                )
                
                executions_result = await session.execute(executions_query)
                executions = list(executions_result.scalars())
                
                if not executions:
                    return None
                
                # Calculate metrics
                total_tests = len(executions)
                passed_tests = len([e for e in executions if e.status == TestStatus.PASSED])
                failed_tests = len([e for e in executions if e.status == TestStatus.FAILED])
                skipped_tests = len([e for e in executions if e.status == TestStatus.SKIPPED])
                
                success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0.0
                
                durations = [e.duration for e in executions if e.duration]
                average_duration = sum(durations) / len(durations) if durations else None
                total_duration = sum(durations) if durations else None
                
                cpu_usages = [e.cpu_usage for e in executions if e.cpu_usage]
                cpu_usage_avg = sum(cpu_usages) / len(cpu_usages) if cpu_usages else None
                
                memory_usages = [e.memory_usage for e in executions if e.memory_usage]
                memory_usage_avg = sum(memory_usages) / len(memory_usages) if memory_usages else None
                
                # Platform stats
                platform_stats = defaultdict(int)
                for execution in executions:
                    platform_stats[execution.platform or 'unknown'] += 1
                
                # Test type stats
                test_type_stats = defaultdict(int)
                for execution in executions:
                    test_type_stats[execution.test_type] += 1
                
                # Error categories
                error_categories = defaultdict(int)
                for execution in executions:
                    if execution.error_category:
                        error_categories[execution.error_category] += 1
                
                # AI metrics
                ai_confidences = [e.ai_confidence for e in executions if e.ai_confidence]
                ai_confidence_avg = sum(ai_confidences) / len(ai_confidences) if ai_confidences else None
                ai_suggestions_count = len([e for e in executions if e.ai_suggestions])
                
                # Create analytics record
                analytics = Analytics(
                    date=datetime.combine(target_date, datetime.min.time()),
                    metric_type="daily",
                    total_tests=total_tests,
                    passed_tests=passed_tests,
                    failed_tests=failed_tests,
                    skipped_tests=skipped_tests,
                    success_rate=success_rate,
                    average_duration=average_duration,
                    total_duration=total_duration,
                    cpu_usage_avg=cpu_usage_avg,
                    memory_usage_avg=memory_usage_avg,
                    platform_stats=dict(platform_stats),
                    test_type_stats=dict(test_type_stats),
                    error_categories=dict(error_categories),
                    ai_confidence_avg=ai_confidence_avg,
                    ai_suggestions_count=ai_suggestions_count
                )
                
                # Save or update existing record
                existing_query = select(Analytics).where(
                    and_(
                        func.date(Analytics.date) == target_date,
                        Analytics.metric_type == "daily"
                    )
                )
                
                existing_result = await session.execute(existing_query)
                existing_analytics = existing_result.scalar_one_or_none()
                
                if existing_analytics:
                    # Update existing
                    for key, value in analytics.__dict__.items():
                        if not key.startswith('_'):
                            setattr(existing_analytics, key, value)
                    await session.commit()
                    return existing_analytics
                else:
                    # Create new
                    session.add(analytics)
                    await session.commit()
                    await session.refresh(analytics)
                    return analytics
                
        except Exception as e:
            logger.error(f"Error generating daily analytics: {e}")
            raise

# Global analytics service instance
analytics_service = AnalyticsService()