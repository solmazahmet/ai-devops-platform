"""
Performance Monitoring API Endpoints
Real-time performance metrics and optimization insights
"""

from fastapi import APIRouter, HTTPException, status, Query, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from app.core.performance import performance_monitor, PerformanceContext
from app.core.cache import cache_manager
from app.core.database import db_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/performance", tags=["Performance"])

@router.get("/metrics")
async def get_performance_metrics(
    time_range: int = Query(3600, description="Time range in seconds"),
    metric_type: Optional[str] = Query(None, description="Filter by metric type")
):
    """
    Get comprehensive performance metrics
    
    Returns:
    - System metrics (CPU, memory, disk)
    - Application metrics (response times, errors)
    - Database metrics (connections, queries)
    - Cache metrics (hit rates, usage)
    """
    try:
        # Get performance summary
        perf_data = performance_monitor.get_performance_summary()
        
        # Add cache metrics
        cache_stats = await cache_manager.get_stats()
        perf_data["cache_metrics"] = cache_stats
        
        # Add database metrics
        db_health = await db_manager.health_check()
        perf_data["database_metrics"] = db_health
        
        # Filter by metric type if specified
        if metric_type:
            filtered_data = {}
            if metric_type in perf_data:
                filtered_data[metric_type] = perf_data[metric_type]
            perf_data = filtered_data
        
        return {
            "status": "success",
            "time_range_seconds": time_range,
            "collected_at": datetime.now().isoformat(),
            "metrics": perf_data
        }
        
    except Exception as e:
        logger.error(f"Performance metrics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )

@router.get("/system")
async def get_system_metrics():
    """
    Get current system performance metrics
    
    Returns real-time system resource usage
    """
    try:
        system_metrics = performance_monitor.get_system_metrics()
        
        return {
            "status": "success",
            "system_metrics": system_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System metrics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system metrics: {str(e)}"
        )

@router.get("/endpoints")
async def get_endpoint_performance(endpoint: Optional[str] = None):
    """
    Get API endpoint performance statistics
    
    Returns response times, error rates, and request counts
    """
    try:
        if endpoint:
            stats = performance_monitor.get_endpoint_stats(endpoint)
            if not stats:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No performance data found for endpoint: {endpoint}"
                )
        else:
            stats = performance_monitor.get_endpoint_stats()
        
        return {
            "status": "success",
            "endpoint_performance": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Endpoint performance error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get endpoint performance: {str(e)}"
        )

@router.get("/functions")
async def get_function_performance():
    """
    Get function execution performance statistics
    
    Returns execution times and success rates for monitored functions
    """
    try:
        stats = performance_monitor.get_function_stats()
        
        return {
            "status": "success",
            "function_performance": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Function performance error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get function performance: {str(e)}"
        )

@router.get("/alerts")
async def get_performance_alerts(limit: int = Query(50, le=100)):
    """
    Get recent performance alerts
    
    Returns alerts for slow responses, high resource usage, etc.
    """
    try:
        alerts = performance_monitor.system_alerts[-limit:] if performance_monitor.system_alerts else []
        
        # Group alerts by type
        alert_summary = {}
        for alert in alerts:
            alert_type = alert.get("type", "unknown")
            if alert_type not in alert_summary:
                alert_summary[alert_type] = {
                    "count": 0,
                    "latest": None,
                    "severity_counts": {"warning": 0, "critical": 0}
                }
            
            alert_summary[alert_type]["count"] += 1
            alert_summary[alert_type]["latest"] = alert.get("timestamp")
            severity = alert.get("severity", "warning")
            alert_summary[alert_type]["severity_counts"][severity] += 1
        
        return {
            "status": "success",
            "total_alerts": len(alerts),
            "alert_summary": alert_summary,
            "recent_alerts": alerts,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Performance alerts error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance alerts: {str(e)}"
        )

@router.get("/cache")
async def get_cache_performance():
    """
    Get cache performance metrics
    
    Returns hit rates, memory usage, and key statistics
    """
    try:
        cache_stats = await cache_manager.get_stats()
        cache_health = await cache_manager.health_check()
        
        return {
            "status": "success",
            "cache_performance": {
                "statistics": cache_stats,
                "health": cache_health
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cache performance error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache performance: {str(e)}"
        )

@router.get("/database")
async def get_database_performance():
    """
    Get database performance metrics
    
    Returns connection pool status, query performance, etc.
    """
    try:
        db_health = await db_manager.health_check()
        
        return {
            "status": "success",
            "database_performance": db_health,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database performance error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database performance: {str(e)}"
        )

@router.post("/benchmark")
async def run_performance_benchmark():
    """
    Run a comprehensive performance benchmark
    
    Tests various system components and returns performance scores
    """
    try:
        benchmark_results = {}
        
        # Database benchmark
        with PerformanceContext("database_benchmark", {"component": "database"}) as perf:
            try:
                db_health = await db_manager.health_check()
                benchmark_results["database"] = {
                    "status": "success",
                    "health": db_health.get("status", "unknown"),
                    "response_time": perf.start_time
                }
            except Exception as e:
                benchmark_results["database"] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Cache benchmark
        with PerformanceContext("cache_benchmark", {"component": "cache"}) as perf:
            try:
                # Test cache operations
                test_key = "benchmark_test"
                test_value = {"benchmark": True, "timestamp": datetime.now().isoformat()}
                
                await cache_manager.set(test_key, test_value, 60)
                retrieved = await cache_manager.get(test_key)
                await cache_manager.delete(test_key)
                
                benchmark_results["cache"] = {
                    "status": "success",
                    "test_passed": retrieved == test_value,
                    "response_time": perf.start_time
                }
            except Exception as e:
                benchmark_results["cache"] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # System benchmark
        system_metrics = performance_monitor.get_system_metrics()
        benchmark_results["system"] = {
            "status": "success",
            "cpu_usage": system_metrics.get("cpu", {}).get("usage_percent", 0),
            "memory_usage": system_metrics.get("memory", {}).get("usage_percent", 0),
            "disk_usage": system_metrics.get("disk", {}).get("usage_percent", 0)
        }
        
        # Calculate overall performance score
        scores = []
        if benchmark_results["database"]["status"] == "success":
            scores.append(90)  # Database working
        if benchmark_results["cache"]["status"] == "success":
            scores.append(85)   # Cache working
        
        cpu_usage = benchmark_results["system"]["cpu_usage"]
        memory_usage = benchmark_results["system"]["memory_usage"]
        system_score = max(0, 100 - max(cpu_usage, memory_usage))
        scores.append(system_score)
        
        overall_score = sum(scores) / len(scores) if scores else 0
        
        return {
            "status": "success",
            "benchmark_results": benchmark_results,
            "performance_score": round(overall_score, 2),
            "score_breakdown": {
                "database": 90 if benchmark_results["database"]["status"] == "success" else 0,
                "cache": 85 if benchmark_results["cache"]["status"] == "success" else 0,
                "system": round(system_score, 2)
            },
            "recommendations": _generate_performance_recommendations(benchmark_results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Performance benchmark error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run performance benchmark: {str(e)}"
        )

@router.get("/export", response_class=PlainTextResponse)
async def export_performance_data(
    format: str = Query("json", regex="^(json|csv)$"),
    time_range: int = Query(3600, description="Time range in seconds")
):
    """
    Export performance metrics data
    
    Supports JSON and CSV formats
    """
    try:
        exported_data = performance_monitor.export_metrics(format, time_range)
        
        media_type = "application/json" if format == "json" else "text/csv"
        filename = f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
        
        return PlainTextResponse(
            content=exported_data,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Performance export error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export performance data: {str(e)}"
        )

@router.post("/reset")
async def reset_performance_stats():
    """
    Reset all performance statistics
    
    Clears all collected metrics and statistics
    """
    try:
        performance_monitor.reset_stats()
        await cache_manager.reset_stats()
        
        return {
            "status": "success",
            "message": "Performance statistics reset successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Performance reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset performance stats: {str(e)}"
        )

@router.get("/health")
async def performance_health_check():
    """
    Comprehensive health check for all performance components
    
    Returns status of monitoring, caching, and database systems
    """
    try:
        health_status = {
            "monitoring": {
                "status": "healthy",
                "active_metrics": len(performance_monitor.metrics),
                "monitored_endpoints": len(performance_monitor.endpoint_stats),
                "monitored_functions": len(performance_monitor.function_stats)
            },
            "cache": await cache_manager.health_check(),
            "database": await db_manager.health_check()
        }
        
        # Determine overall health
        component_health = [
            health_status["monitoring"]["status"] == "healthy",
            health_status["cache"]["status"] == "healthy",
            health_status["database"]["status"] == "healthy"
        ]
        
        overall_healthy = sum(component_health)
        if overall_healthy == len(component_health):
            overall_status = "healthy"
        elif overall_healthy >= len(component_health) / 2:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "components": health_status,
            "healthy_components": overall_healthy,
            "total_components": len(component_health),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Performance health check error: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

def _generate_performance_recommendations(benchmark_results: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate performance optimization recommendations"""
    recommendations = []
    
    # Database recommendations
    if benchmark_results.get("database", {}).get("status") != "success":
        recommendations.append({
            "category": "database",
            "priority": "high",
            "recommendation": "Database connection issues detected. Check connection pool settings and database availability.",
            "action": "Review database configuration and network connectivity"
        })
    
    # Cache recommendations
    if benchmark_results.get("cache", {}).get("status") != "success":
        recommendations.append({
            "category": "cache",
            "priority": "medium",
            "recommendation": "Cache system issues detected. Verify Redis connection or enable memory fallback.",
            "action": "Check cache configuration and Redis server status"
        })
    
    # System recommendations
    system = benchmark_results.get("system", {})
    cpu_usage = system.get("cpu_usage", 0)
    memory_usage = system.get("memory_usage", 0)
    
    if cpu_usage > 80:
        recommendations.append({
            "category": "system",
            "priority": "high",
            "recommendation": f"High CPU usage detected ({cpu_usage}%). Consider scaling or optimizing resource-intensive operations.",
            "action": "Monitor CPU-intensive processes and consider horizontal scaling"
        })
    
    if memory_usage > 85:
        recommendations.append({
            "category": "system",
            "priority": "high",
            "recommendation": f"High memory usage detected ({memory_usage}%). Consider increasing memory or optimizing memory usage.",
            "action": "Review memory-intensive operations and consider memory optimization"
        })
    
    # General recommendations
    if not recommendations:
        recommendations.append({
            "category": "general",
            "priority": "low",
            "recommendation": "System performance is optimal. Consider implementing additional monitoring for proactive optimization.",
            "action": "Continue monitoring and consider performance testing under load"
        })
    
    return recommendations