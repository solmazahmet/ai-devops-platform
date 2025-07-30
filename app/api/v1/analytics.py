"""
Analytics API Endpoints
Advanced test analytics and dashboard endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import logging

from app.services.analytics_service import analytics_service
from app.models.analytics import DashboardMetrics, AnalyticsResponse, TestExecutionResponse
from app.core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics():
    """
    Get comprehensive dashboard metrics
    
    Returns:
    - Overview metrics (totals, success rates)
    - Performance metrics (duration, speed)
    - Distribution charts (platforms, test types)
    - Trend data (daily, hourly)
    - Recent activities
    - AI insights and suggestions
    """
    try:
        dashboard_metrics = await analytics_service.get_dashboard_metrics()
        return dashboard_metrics
        
    except Exception as e:
        logger.error(f"Dashboard metrics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard metrics: {str(e)}"
        )

@router.get("/overview")
async def get_analytics_overview(
    days: int = Query(7, description="Number of days to analyze", ge=1, le=90)
):
    """
    Get analytics overview for specified period
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        analytics_data = await analytics_service.get_analytics_data(
            date_from=start_date,
            date_to=end_date,
            metric_type="daily"
        )
        
        return {
            "period": f"Last {days} days",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "data": analytics_data
        }
        
    except Exception as e:
        logger.error(f"Analytics overview error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics overview: {str(e)}"
        )

@router.get("/trends/daily")
async def get_daily_trends(
    days: int = Query(30, description="Number of days", ge=1, le=365)
):
    """
    Get daily trend data for charts
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        analytics_data = await analytics_service.get_analytics_data(
            date_from=start_date,
            date_to=end_date,
            metric_type="daily"
        )
        
        # Format data for charts
        chart_data = []
        for data in analytics_data:
            chart_data.append({
                "date": data.date.strftime("%Y-%m-%d"),
                "total_tests": data.total_tests,
                "passed_tests": data.passed_tests,
                "failed_tests": data.failed_tests,
                "success_rate": data.success_rate,
                "average_duration": data.average_duration
            })
        
        return {
            "period": f"Last {days} days",
            "chart_data": chart_data
        }
        
    except Exception as e:
        logger.error(f"Daily trends error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get daily trends: {str(e)}"
        )

@router.get("/performance")
async def get_performance_metrics(
    period: str = Query("7d", description="Period: 1d, 7d, 30d, 90d")
):
    """
    Get detailed performance metrics
    """
    try:
        # Parse period
        period_map = {
            "1d": 1,
            "7d": 7,
            "30d": 30,
            "90d": 90
        }
        
        days = period_map.get(period, 7)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        analytics_data = await analytics_service.get_analytics_data(
            date_from=start_date,
            date_to=end_date,
            metric_type="daily"
        )
        
        if not analytics_data:
            return {
                "period": period,
                "metrics": {
                    "average_duration": 0,
                    "total_duration": 0,
                    "cpu_usage_avg": 0,
                    "memory_usage_avg": 0,
                    "total_tests": 0
                }
            }
        
        # Calculate aggregate metrics
        total_tests = sum(d.total_tests for d in analytics_data)
        total_duration = sum(d.total_duration or 0 for d in analytics_data)
        
        durations = [d.average_duration for d in analytics_data if d.average_duration]
        average_duration = sum(durations) / len(durations) if durations else 0
        
        cpu_usages = [d.cpu_usage_avg for d in analytics_data if d.cpu_usage_avg]
        cpu_usage_avg = sum(cpu_usages) / len(cpu_usages) if cpu_usages else 0
        
        memory_usages = [d.memory_usage_avg for d in analytics_data if d.memory_usage_avg]
        memory_usage_avg = sum(memory_usages) / len(memory_usages) if memory_usages else 0
        
        return {
            "period": period,
            "metrics": {
                "average_duration": round(average_duration, 2),
                "total_duration": round(total_duration, 2),
                "cpu_usage_avg": round(cpu_usage_avg, 2),
                "memory_usage_avg": round(memory_usage_avg, 2),
                "total_tests": total_tests
            },
            "daily_data": analytics_data
        }
        
    except Exception as e:
        logger.error(f"Performance metrics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )

@router.get("/platforms")
async def get_platform_analytics(
    days: int = Query(7, description="Number of days to analyze", ge=1, le=90)
):
    """
    Get platform-specific analytics
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        analytics_data = await analytics_service.get_analytics_data(
            date_from=start_date,
            date_to=end_date,
            metric_type="daily"
        )
        
        # Aggregate platform stats
        platform_totals = {}
        for data in analytics_data:
            if data.platform_stats:
                for platform, count in data.platform_stats.items():
                    platform_totals[platform] = platform_totals.get(platform, 0) + count
        
        # Sort by usage
        sorted_platforms = sorted(platform_totals.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "period": f"Last {days} days",
            "platform_distribution": dict(sorted_platforms),
            "total_tests": sum(platform_totals.values()),
            "platform_details": [
                {
                    "platform": platform,
                    "test_count": count,
                    "percentage": round(count / sum(platform_totals.values()) * 100, 1) if platform_totals else 0
                }
                for platform, count in sorted_platforms
            ]
        }
        
    except Exception as e:
        logger.error(f"Platform analytics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get platform analytics: {str(e)}"
        )

@router.get("/errors")
async def get_error_analytics(
    days: int = Query(7, description="Number of days to analyze", ge=1, le=90)
):
    """
    Get error pattern analytics
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        analytics_data = await analytics_service.get_analytics_data(
            date_from=start_date,
            date_to=end_date,
            metric_type="daily"
        )
        
        # Aggregate error categories
        error_totals = {}
        total_errors = 0
        
        for data in analytics_data:
            if data.error_categories:
                for error_type, count in data.error_categories.items():
                    error_totals[error_type] = error_totals.get(error_type, 0) + count
                    total_errors += count
        
        # Sort by frequency
        sorted_errors = sorted(error_totals.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "period": f"Last {days} days",
            "total_errors": total_errors,
            "error_distribution": dict(sorted_errors),
            "error_details": [
                {
                    "error_type": error_type,
                    "count": count,
                    "percentage": round(count / total_errors * 100, 1) if total_errors else 0
                }
                for error_type, count in sorted_errors
            ]
        }
        
    except Exception as e:
        logger.error(f"Error analytics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get error analytics: {str(e)}"
        )

@router.post("/test-execution")
async def record_test_execution(
    test_data: Dict[str, Any]
):
    """
    Record a new test execution for analytics
    """
    try:
        execution = await analytics_service.record_test_execution(test_data)
        
        return {
            "status": "success",
            "execution_id": execution.id,
            "message": "Test execution recorded successfully"
        }
        
    except Exception as e:
        logger.error(f"Record test execution error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record test execution: {str(e)}"
        )

@router.put("/test-execution/{execution_id}")
async def update_test_execution(
    execution_id: int,
    update_data: Dict[str, Any]
):
    """
    Update test execution with results
    """
    try:
        execution = await analytics_service.update_test_execution(execution_id, update_data)
        
        if execution:
            return {
                "status": "success",
                "execution_id": execution.id,
                "message": "Test execution updated successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test execution not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update test execution error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update test execution: {str(e)}"
        )

@router.post("/generate-daily-analytics")
async def generate_daily_analytics(
    target_date: Optional[date] = Query(None, description="Target date (YYYY-MM-DD)")
):
    """
    Generate daily analytics aggregation
    """
    try:
        analytics = await analytics_service.generate_daily_analytics(target_date)
        
        if analytics:
            return {
                "status": "success",
                "analytics_id": analytics.id,
                "date": analytics.date.strftime("%Y-%m-%d"),
                "message": "Daily analytics generated successfully"
            }
        else:
            return {
                "status": "info",
                "message": "No test data found for the specified date"
            }
        
    except Exception as e:
        logger.error(f"Generate daily analytics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate daily analytics: {str(e)}"
        )

@router.get("/health")
async def analytics_health_check():
    """
    Analytics service health check
    """
    try:
        # Quick test of analytics service
        dashboard_metrics = await analytics_service.get_dashboard_metrics()
        
        return {
            "status": "healthy",
            "service": "analytics",
            "message": "Analytics service is operational",
            "timestamp": datetime.now().isoformat(),
            "cache_keys": len(analytics_service._cache)
        }
        
    except Exception as e:
        logger.error(f"Analytics health check error: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "analytics",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )