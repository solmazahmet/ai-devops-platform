"""
Performance Monitoring and Optimization
Real-time performance metrics and optimization utilities
"""

import time
import logging
import asyncio
import psutil
import functools
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, deque
import threading
import json

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags or {}
        }

class PerformanceMonitor:
    """Comprehensive performance monitoring system"""
    
    def __init__(self):
        self.metrics = deque(maxlen=10000)  # Store last 10k metrics
        self.endpoint_stats = defaultdict(lambda: {
            "count": 0,
            "total_time": 0,
            "min_time": float('inf'),
            "max_time": 0,
            "errors": 0,
            "last_called": None
        })
        self.function_stats = defaultdict(lambda: {
            "count": 0,
            "total_time": 0,
            "avg_time": 0,
            "errors": 0
        })
        self.system_alerts = []
        self.lock = threading.Lock()
        
        # Performance thresholds
        self.thresholds = {
            "response_time": 2.0,  # seconds
            "memory_usage": 85,    # percentage
            "cpu_usage": 80,       # percentage
            "error_rate": 5        # percentage
        }
        
        # Start background monitoring
        self._start_system_monitoring()
    
    def record_metric(self, name: str, value: float, unit: str, tags: Dict[str, str] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        
        with self.lock:
            self.metrics.append(metric)
        
        # Check for alerts
        self._check_alerts(metric)
    
    def record_request(self, endpoint: str, response_time: float, status_code: int = 200):
        """Record API request performance"""
        with self.lock:
            stats = self.endpoint_stats[endpoint]
            stats["count"] += 1
            stats["total_time"] += response_time
            stats["min_time"] = min(stats["min_time"], response_time)
            stats["max_time"] = max(stats["max_time"], response_time)
            stats["last_called"] = datetime.now()
            
            if status_code >= 400:
                stats["errors"] += 1
        
        # Record as metric
        self.record_metric(
            name="api_response_time",
            value=response_time,
            unit="seconds",
            tags={"endpoint": endpoint, "status": str(status_code)}
        )
    
    def record_function_call(self, function_name: str, execution_time: float, success: bool = True):
        """Record function execution performance"""
        with self.lock:
            stats = self.function_stats[function_name]
            stats["count"] += 1
            stats["total_time"] += execution_time
            stats["avg_time"] = stats["total_time"] / stats["count"]
            
            if not success:
                stats["errors"] += 1
        
        self.record_metric(
            name="function_execution_time",
            value=execution_time,
            unit="seconds",
            tags={"function": function_name, "success": str(success)}
        )
    
    def get_endpoint_stats(self, endpoint: str = None) -> Dict[str, Any]:
        """Get endpoint performance statistics"""
        with self.lock:
            if endpoint:
                stats = self.endpoint_stats.get(endpoint, {})
                if stats.get("count", 0) > 0:
                    return {
                        "endpoint": endpoint,
                        "total_requests": stats["count"],
                        "avg_response_time": round(stats["total_time"] / stats["count"], 4),
                        "min_response_time": round(stats["min_time"], 4),
                        "max_response_time": round(stats["max_time"], 4),
                        "error_count": stats["errors"],
                        "error_rate": round((stats["errors"] / stats["count"]) * 100, 2),
                        "last_called": stats["last_called"].isoformat() if stats["last_called"] else None
                    }
                return {}
            else:
                # Return all endpoint stats
                all_stats = {}
                for ep, stats in self.endpoint_stats.items():
                    if stats["count"] > 0:
                        all_stats[ep] = {
                            "total_requests": stats["count"],
                            "avg_response_time": round(stats["total_time"] / stats["count"], 4),
                            "min_response_time": round(stats["min_time"], 4),
                            "max_response_time": round(stats["max_time"], 4),
                            "error_count": stats["errors"],
                            "error_rate": round((stats["errors"] / stats["count"]) * 100, 2),
                            "last_called": stats["last_called"].isoformat() if stats["last_called"] else None
                        }
                return all_stats
    
    def get_function_stats(self) -> Dict[str, Any]:
        """Get function performance statistics"""
        with self.lock:
            return {
                func: {
                    "call_count": stats["count"],
                    "avg_execution_time": round(stats["avg_time"], 4),
                    "total_execution_time": round(stats["total_time"], 4),
                    "error_count": stats["errors"],
                    "success_rate": round(((stats["count"] - stats["errors"]) / stats["count"]) * 100, 2)
                } for func, stats in self.function_stats.items() if stats["count"] > 0
            }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used / (1024**3)  # GB
            memory_total = memory.total / (1024**3)  # GB
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used = disk.used / (1024**3)  # GB
            disk_total = disk.total / (1024**3)  # GB
            
            # Network metrics (if available)
            try:
                network = psutil.net_io_counters()
                network_sent = network.bytes_sent / (1024**2)  # MB
                network_recv = network.bytes_recv / (1024**2)  # MB
            except:
                network_sent = network_recv = 0
            
            return {
                "cpu": {
                    "usage_percent": round(cpu_percent, 2),
                    "core_count": cpu_count,
                    "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else []
                },
                "memory": {
                    "usage_percent": round(memory_percent, 2),
                    "used_gb": round(memory_used, 2),
                    "total_gb": round(memory_total, 2),
                    "available_gb": round((memory_total - memory_used), 2)
                },
                "disk": {
                    "usage_percent": round(disk_percent, 2),
                    "used_gb": round(disk_used, 2),
                    "total_gb": round(disk_total, 2),
                    "free_gb": round((disk_total - disk_used), 2)
                },
                "network": {
                    "bytes_sent_mb": round(network_sent, 2),
                    "bytes_recv_mb": round(network_recv, 2)
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        # Calculate metric aggregations
        recent_metrics = [m for m in self.metrics if m.timestamp > datetime.now() - timedelta(hours=1)]
        
        # Group metrics by name
        metric_groups = defaultdict(list)
        for metric in recent_metrics:
            metric_groups[metric.name].append(metric.value)
        
        metric_stats = {}
        for name, values in metric_groups.items():
            if values:
                metric_stats[name] = {
                    "count": len(values),
                    "avg": round(sum(values) / len(values), 4),
                    "min": round(min(values), 4),
                    "max": round(max(values), 4),
                    "latest": round(values[-1], 4)
                }
        
        return {
            "summary": {
                "total_metrics": len(self.metrics),
                "recent_metrics_1h": len(recent_metrics),
                "monitored_endpoints": len(self.endpoint_stats),
                "monitored_functions": len(self.function_stats),
                "active_alerts": len(self.system_alerts)
            },
            "metric_stats": metric_stats,
            "endpoint_performance": self.get_endpoint_stats(),
            "function_performance": self.get_function_stats(),
            "system_metrics": self.get_system_metrics(),
            "alerts": self.system_alerts[-10:]  # Last 10 alerts
        }
    
    def _check_alerts(self, metric: PerformanceMetric):
        """Check if metric triggers any alerts"""
        alerts = []
        
        if metric.name == "api_response_time" and metric.value > self.thresholds["response_time"]:
            alerts.append({
                "type": "slow_response",
                "message": f"Slow API response: {metric.value:.2f}s > {self.thresholds['response_time']}s",
                "metric": metric.to_dict(),
                "severity": "warning" if metric.value < self.thresholds["response_time"] * 2 else "critical"
            })
        
        # Add system metric alerts
        if metric.name == "cpu_usage" and metric.value > self.thresholds["cpu_usage"]:
            alerts.append({
                "type": "high_cpu",
                "message": f"High CPU usage: {metric.value:.1f}% > {self.thresholds['cpu_usage']}%",
                "metric": metric.to_dict(),
                "severity": "warning" if metric.value < 95 else "critical"
            })
        
        if metric.name == "memory_usage" and metric.value > self.thresholds["memory_usage"]:
            alerts.append({
                "type": "high_memory",
                "message": f"High memory usage: {metric.value:.1f}% > {self.thresholds['memory_usage']}%",
                "metric": metric.to_dict(),
                "severity": "warning" if metric.value < 95 else "critical"
            })
        
        # Add alerts to the list
        for alert in alerts:
            alert["timestamp"] = datetime.now().isoformat()
            self.system_alerts.append(alert)
        
        # Keep only last 100 alerts
        if len(self.system_alerts) > 100:
            self.system_alerts = self.system_alerts[-100:]
    
    def _start_system_monitoring(self):
        """Start background system monitoring"""
        def monitor_system():
            while True:
                try:
                    # Record system metrics
                    system_metrics = self.get_system_metrics()
                    
                    if "cpu" in system_metrics:
                        self.record_metric("cpu_usage", system_metrics["cpu"]["usage_percent"], "percent")
                        self.record_metric("memory_usage", system_metrics["memory"]["usage_percent"], "percent")
                        self.record_metric("disk_usage", system_metrics["disk"]["usage_percent"], "percent")
                    
                    time.sleep(30)  # Monitor every 30 seconds
                    
                except Exception as e:
                    logger.error(f"System monitoring error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
    
    def export_metrics(self, format: str = "json", time_range: int = 3600) -> str:
        """Export metrics in specified format"""
        cutoff_time = datetime.now() - timedelta(seconds=time_range)
        filtered_metrics = [m for m in self.metrics if m.timestamp > cutoff_time]
        
        if format == "json":
            return json.dumps([m.to_dict() for m in filtered_metrics], indent=2)
        elif format == "csv":
            lines = ["timestamp,name,value,unit,tags"]
            for m in filtered_metrics:
                tags_str = ";".join(f"{k}={v}" for k, v in (m.tags or {}).items())
                lines.append(f"{m.timestamp.isoformat()},{m.name},{m.value},{m.unit},{tags_str}")
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def reset_stats(self):
        """Reset all performance statistics"""
        with self.lock:
            self.metrics.clear()
            self.endpoint_stats.clear()
            self.function_stats.clear()
            self.system_alerts.clear()
        logger.info("Performance statistics reset")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Decorators for performance monitoring
def monitor_endpoint(func):
    """Decorator to monitor API endpoint performance"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        endpoint_name = f"{func.__module__}.{func.__name__}"
        start_time = time.time()
        status_code = 200
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            status_code = 500
            raise
        finally:
            response_time = time.time() - start_time
            performance_monitor.record_request(endpoint_name, response_time, status_code)
    
    return wrapper

def monitor_function(func):
    """Decorator to monitor function performance"""
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        function_name = f"{func.__module__}.{func.__name__}"
        start_time = time.time()
        success = True
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            raise
        finally:
            execution_time = time.time() - start_time
            performance_monitor.record_function_call(function_name, execution_time, success)
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        function_name = f"{func.__module__}.{func.__name__}"
        start_time = time.time()
        success = True
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            raise
        finally:
            execution_time = time.time() - start_time
            performance_monitor.record_function_call(function_name, execution_time, success)
    
    # Return appropriate wrapper based on function type
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

# Context manager for performance measurement
class PerformanceContext:
    """Context manager for measuring performance of code blocks"""
    
    def __init__(self, name: str, tags: Dict[str, str] = None):
        self.name = name
        self.tags = tags or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            performance_monitor.record_metric(
                name=self.name,
                value=duration,
                unit="seconds",
                tags=self.tags
            )

# Usage example:
# with PerformanceContext("database_query", {"table": "users"}) as perf:
#     # Database operation here
#     pass