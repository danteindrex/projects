"""
Analytics service for aggregating metrics and generating insights.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, asc

from app.models.integration import Integration, IntegrationStatus
from app.models.tool_execution import ToolExecution, StreamingEvent, AgentActivity
from app.models.analytics_metrics import MetricsAggregate, IntegrationHealthSnapshot, CostTracking
from app.services.cache_service import cache_service, CacheNamespaces
from app.db.database import get_db_session
from app.core.logging import get_logger

logger = get_logger(__name__)


class AnalyticsService:
    """Service for analytics data aggregation and insights generation."""
    
    @staticmethod
    async def aggregate_hourly_metrics(integration_id: int, target_hour: datetime, db: Session = None):
        """Aggregate metrics for a specific hour."""
        if not db:
            db = next(get_db_session())
            close_db = True
        else:
            close_db = False
            
        try:
            hour_start = target_hour.replace(minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)
            
            # Get all executions for this hour
            executions = db.query(ToolExecution).filter(
                ToolExecution.integration_id == integration_id,
                ToolExecution.started_at >= hour_start,
                ToolExecution.started_at < hour_end
            ).all()
            
            if not executions:
                logger.info(f"No executions found for integration {integration_id} at {hour_start}")
                return
            
            # Calculate metrics
            total_calls = len(executions)
            successful_calls = len([e for e in executions if e.success])
            failed_calls = total_calls - successful_calls
            
            response_times = [e.execution_time for e in executions if e.execution_time and e.success]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
            min_response_time = min(response_times) if response_times else 0.0
            max_response_time = max(response_times) if response_times else 0.0
            
            # Calculate P95 (95th percentile)
            if response_times:
                response_times_sorted = sorted(response_times)
                p95_index = int(len(response_times_sorted) * 0.95)
                p95_response_time = response_times_sorted[p95_index] if p95_index < len(response_times_sorted) else response_times_sorted[-1]
            else:
                p95_response_time = 0.0
            
            # Categorize errors
            timeout_errors = len([e for e in executions if not e.success and e.error_message and "timeout" in e.error_message.lower()])
            auth_errors = len([e for e in executions if not e.success and e.error_message and any(keyword in e.error_message.lower() for keyword in ["auth", "unauthorized", "forbidden"])])
            rate_limit_errors = len([e for e in executions if not e.success and e.error_message and "rate limit" in e.error_message.lower()])
            connectivity_errors = len([e for e in executions if not e.success and e.error_message and "connection" in e.error_message.lower()])
            other_errors = failed_calls - (timeout_errors + auth_errors + rate_limit_errors + connectivity_errors)
            
            # Tool usage breakdown
            tool_usage = {}
            for execution in executions:
                tool_name = execution.tool_name
                if tool_name not in tool_usage:
                    tool_usage[tool_name] = 0
                tool_usage[tool_name] += 1
            
            # Estimate cost (get integration to determine cost per call)
            integration = db.query(Integration).filter(Integration.id == integration_id).first()
            cost_estimates = {
                "salesforce": 0.002,
                "jira": 0.001,
                "zendesk": 0.0015,
                "github": 0.0005,
                "slack": 0.0008,
            }
            cost_per_call = cost_estimates.get(integration.integration_type.value, 0.001) if integration else 0.001
            estimated_cost = total_calls * cost_per_call
            
            # Check if aggregate already exists
            existing_aggregate = db.query(MetricsAggregate).filter(
                MetricsAggregate.integration_id == integration_id,
                MetricsAggregate.metric_type == "hourly",
                MetricsAggregate.metric_date == hour_start
            ).first()
            
            if existing_aggregate:
                # Update existing
                existing_aggregate.total_calls = total_calls
                existing_aggregate.successful_calls = successful_calls
                existing_aggregate.failed_calls = failed_calls
                existing_aggregate.avg_response_time = avg_response_time
                existing_aggregate.min_response_time = min_response_time
                existing_aggregate.max_response_time = max_response_time
                existing_aggregate.p95_response_time = p95_response_time
                existing_aggregate.timeout_errors = timeout_errors
                existing_aggregate.auth_errors = auth_errors
                existing_aggregate.rate_limit_errors = rate_limit_errors
                existing_aggregate.connectivity_errors = connectivity_errors
                existing_aggregate.other_errors = other_errors
                existing_aggregate.tool_usage = tool_usage
                existing_aggregate.estimated_cost = estimated_cost
                existing_aggregate.updated_at = datetime.utcnow()
            else:
                # Create new aggregate
                new_aggregate = MetricsAggregate(
                    integration_id=integration_id,
                    metric_type="hourly",
                    metric_date=hour_start,
                    total_calls=total_calls,
                    successful_calls=successful_calls,
                    failed_calls=failed_calls,
                    avg_response_time=avg_response_time,
                    min_response_time=min_response_time,
                    max_response_time=max_response_time,
                    p95_response_time=p95_response_time,
                    timeout_errors=timeout_errors,
                    auth_errors=auth_errors,
                    rate_limit_errors=rate_limit_errors,
                    connectivity_errors=connectivity_errors,
                    other_errors=other_errors,
                    tool_usage=tool_usage,
                    estimated_cost=estimated_cost
                )
                db.add(new_aggregate)
            
            db.commit()
            logger.info(f"Aggregated hourly metrics for integration {integration_id} at {hour_start}")
            
        except Exception as e:
            logger.error(f"Failed to aggregate hourly metrics: {e}")
            db.rollback()
            raise
        finally:
            if close_db:
                db.close()
    
    @staticmethod
    async def aggregate_daily_metrics(integration_id: int, target_date: datetime, db: Session = None):
        """Aggregate daily metrics from hourly aggregates."""
        if not db:
            db = next(get_db_session())
            close_db = True
        else:
            close_db = False
            
        try:
            day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            # Get hourly aggregates for the day
            hourly_aggregates = db.query(MetricsAggregate).filter(
                MetricsAggregate.integration_id == integration_id,
                MetricsAggregate.metric_type == "hourly",
                MetricsAggregate.metric_date >= day_start,
                MetricsAggregate.metric_date < day_end
            ).all()
            
            if not hourly_aggregates:
                logger.info(f"No hourly aggregates found for integration {integration_id} on {day_start.date()}")
                return
            
            # Aggregate the hourly data
            total_calls = sum(agg.total_calls for agg in hourly_aggregates)
            successful_calls = sum(agg.successful_calls for agg in hourly_aggregates)
            failed_calls = sum(agg.failed_calls for agg in hourly_aggregates)
            
            # Weighted average response time
            total_successful_calls = sum(agg.successful_calls for agg in hourly_aggregates if agg.successful_calls > 0)
            if total_successful_calls > 0:
                avg_response_time = sum(agg.avg_response_time * agg.successful_calls for agg in hourly_aggregates if agg.successful_calls > 0) / total_successful_calls
            else:
                avg_response_time = 0.0
            
            min_response_time = min((agg.min_response_time for agg in hourly_aggregates if agg.min_response_time > 0), default=0.0)
            max_response_time = max(agg.max_response_time for agg in hourly_aggregates)
            
            # P95 approximation (weighted average of P95s)
            if total_successful_calls > 0:
                p95_response_time = sum(agg.p95_response_time * agg.successful_calls for agg in hourly_aggregates if agg.successful_calls > 0) / total_successful_calls
            else:
                p95_response_time = 0.0
            
            # Error aggregation
            timeout_errors = sum(agg.timeout_errors for agg in hourly_aggregates)
            auth_errors = sum(agg.auth_errors for agg in hourly_aggregates)
            rate_limit_errors = sum(agg.rate_limit_errors for agg in hourly_aggregates)
            connectivity_errors = sum(agg.connectivity_errors for agg in hourly_aggregates)
            other_errors = sum(agg.other_errors for agg in hourly_aggregates)
            
            # Combine tool usage
            combined_tool_usage = {}
            for agg in hourly_aggregates:
                if agg.tool_usage:
                    for tool, count in agg.tool_usage.items():
                        combined_tool_usage[tool] = combined_tool_usage.get(tool, 0) + count
            
            # Total estimated cost
            estimated_cost = sum(agg.estimated_cost for agg in hourly_aggregates)
            
            # Check if daily aggregate already exists
            existing_aggregate = db.query(MetricsAggregate).filter(
                MetricsAggregate.integration_id == integration_id,
                MetricsAggregate.metric_type == "daily",
                MetricsAggregate.metric_date == day_start
            ).first()
            
            if existing_aggregate:
                # Update existing
                existing_aggregate.total_calls = total_calls
                existing_aggregate.successful_calls = successful_calls
                existing_aggregate.failed_calls = failed_calls
                existing_aggregate.avg_response_time = avg_response_time
                existing_aggregate.min_response_time = min_response_time
                existing_aggregate.max_response_time = max_response_time
                existing_aggregate.p95_response_time = p95_response_time
                existing_aggregate.timeout_errors = timeout_errors
                existing_aggregate.auth_errors = auth_errors
                existing_aggregate.rate_limit_errors = rate_limit_errors
                existing_aggregate.connectivity_errors = connectivity_errors
                existing_aggregate.other_errors = other_errors
                existing_aggregate.tool_usage = combined_tool_usage
                existing_aggregate.estimated_cost = estimated_cost
                existing_aggregate.updated_at = datetime.utcnow()
            else:
                # Create new daily aggregate
                new_aggregate = MetricsAggregate(
                    integration_id=integration_id,
                    metric_type="daily",
                    metric_date=day_start,
                    total_calls=total_calls,
                    successful_calls=successful_calls,
                    failed_calls=failed_calls,
                    avg_response_time=avg_response_time,
                    min_response_time=min_response_time,
                    max_response_time=max_response_time,
                    p95_response_time=p95_response_time,
                    timeout_errors=timeout_errors,
                    auth_errors=auth_errors,
                    rate_limit_errors=rate_limit_errors,
                    connectivity_errors=connectivity_errors,
                    other_errors=other_errors,
                    tool_usage=combined_tool_usage,
                    estimated_cost=estimated_cost
                )
                db.add(new_aggregate)
            
            db.commit()
            logger.info(f"Aggregated daily metrics for integration {integration_id} on {day_start.date()}")
            
        except Exception as e:
            logger.error(f"Failed to aggregate daily metrics: {e}")
            db.rollback()
            raise
        finally:
            if close_db:
                db.close()
    
    @staticmethod
    async def create_health_snapshot(integration_id: int, db: Session = None):
        """Create a health snapshot for an integration."""
        if not db:
            db = next(get_db_session())
            close_db = True
        else:
            close_db = False
            
        try:
            integration = db.query(Integration).filter(Integration.id == integration_id).first()
            if not integration:
                logger.error(f"Integration {integration_id} not found")
                return
            
            # Calculate health metrics from recent data
            last_24h = datetime.utcnow() - timedelta(hours=24)
            
            recent_executions = db.query(ToolExecution).filter(
                ToolExecution.integration_id == integration_id,
                ToolExecution.started_at >= last_24h
            ).all()
            
            # Calculate response time
            successful_executions = [e for e in recent_executions if e.success and e.execution_time]
            avg_response_time = sum(e.execution_time for e in successful_executions) / len(successful_executions) if successful_executions else 0.0
            
            # Calculate error count
            error_count_24h = len([e for e in recent_executions if not e.success])
            
            # Calculate uptime percentage (simplified)
            total_calls = len(recent_executions)
            successful_calls = len(successful_executions)
            uptime_percentage = (successful_calls / total_calls * 100) if total_calls > 0 else 100.0
            
            # Determine overall status
            if uptime_percentage >= 98:
                status = "healthy"
            elif uptime_percentage >= 95:
                status = "degraded"
            else:
                status = "unhealthy"
            
            # Simple health checks (would be more sophisticated in real implementation)
            connectivity_check = "pass" if uptime_percentage > 95 else "fail"
            auth_check = "pass" if not any("auth" in (e.error_message or "").lower() for e in recent_executions if not e.success) else "fail"
            rate_limit_check = "pass" if not any("rate limit" in (e.error_message or "").lower() for e in recent_executions if not e.success) else "fail"
            
            # Calculate health score (0-100)
            health_score = uptime_percentage
            if auth_check == "fail":
                health_score *= 0.8
            if rate_limit_check == "fail":
                health_score *= 0.9
            if connectivity_check == "fail":
                health_score *= 0.7
            
            # Create snapshot
            snapshot = IntegrationHealthSnapshot(
                integration_id=integration_id,
                status=status,
                response_time_ms=avg_response_time * 1000,
                uptime_percentage=uptime_percentage,
                error_count_24h=error_count_24h,
                connectivity_check=connectivity_check,
                auth_check=auth_check,
                rate_limit_check=rate_limit_check,
                health_score=health_score,
                metadata={
                    "total_calls_24h": total_calls,
                    "successful_calls_24h": successful_calls,
                    "snapshot_time": datetime.utcnow().isoformat()
                }
            )
            
            db.add(snapshot)
            db.commit()
            logger.info(f"Created health snapshot for integration {integration_id}")
            
        except Exception as e:
            logger.error(f"Failed to create health snapshot: {e}")
            db.rollback()
            raise
        finally:
            if close_db:
                db.close()
    
    @staticmethod
    async def get_performance_insights(integration_id: int, days: int = 30, db: Session = None) -> Dict[str, Any]:
        """Generate performance insights for an integration."""
        if not db:
            db = next(get_db_session())
            close_db = True
        else:
            close_db = False
            
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get daily aggregates for the period
            daily_metrics = db.query(MetricsAggregate).filter(
                MetricsAggregate.integration_id == integration_id,
                MetricsAggregate.metric_type == "daily",
                MetricsAggregate.metric_date >= start_date
            ).order_by(MetricsAggregate.metric_date).all()
            
            if not daily_metrics:
                return {"insights": "Insufficient data for analysis"}
            
            # Calculate trends
            response_times = [m.avg_response_time for m in daily_metrics if m.avg_response_time > 0]
            success_rates = [(m.successful_calls / m.total_calls * 100) if m.total_calls > 0 else 0 for m in daily_metrics]
            
            # Response time trend
            if len(response_times) > 1:
                rt_trend = "improving" if response_times[-1] < response_times[0] else "degrading"
                rt_change = ((response_times[-1] - response_times[0]) / response_times[0] * 100) if response_times[0] > 0 else 0
            else:
                rt_trend = "stable"
                rt_change = 0
            
            # Success rate trend
            if len(success_rates) > 1:
                sr_trend = "improving" if success_rates[-1] > success_rates[0] else "degrading"
                sr_change = success_rates[-1] - success_rates[0]
            else:
                sr_trend = "stable"
                sr_change = 0
            
            # Identify peak usage days
            usage_by_day = [(m.metric_date.strftime('%A'), m.total_calls) for m in daily_metrics]
            peak_day = max(usage_by_day, key=lambda x: x[1]) if usage_by_day else ("Unknown", 0)
            
            # Most common errors
            error_types = {}
            for metric in daily_metrics:
                error_types["timeout"] = error_types.get("timeout", 0) + metric.timeout_errors
                error_types["auth"] = error_types.get("auth", 0) + metric.auth_errors
                error_types["rate_limit"] = error_types.get("rate_limit", 0) + metric.rate_limit_errors
                error_types["connectivity"] = error_types.get("connectivity", 0) + metric.connectivity_errors
                error_types["other"] = error_types.get("other", 0) + metric.other_errors
            
            most_common_error = max(error_types.items(), key=lambda x: x[1]) if any(error_types.values()) else ("none", 0)
            
            insights = {
                "period_days": days,
                "data_points": len(daily_metrics),
                "response_time_trend": {
                    "direction": rt_trend,
                    "change_percent": round(rt_change, 2)
                },
                "success_rate_trend": {
                    "direction": sr_trend,
                    "change_percent": round(sr_change, 2)
                },
                "peak_usage_day": peak_day[0],
                "peak_usage_calls": peak_day[1],
                "most_common_error_type": most_common_error[0],
                "total_errors": sum(error_types.values()),
                "recommendations": []
            }
            
            # Generate recommendations
            if rt_trend == "degrading" and rt_change > 20:
                insights["recommendations"].append("Response times are degrading significantly. Consider optimizing API calls or checking integration health.")
            
            if sr_trend == "degrading" and sr_change < -5:
                insights["recommendations"].append("Success rate is declining. Review error logs and consider updating authentication credentials.")
            
            if most_common_error[1] > 0:
                if most_common_error[0] == "timeout":
                    insights["recommendations"].append("High number of timeout errors. Consider increasing timeout settings or optimizing request payloads.")
                elif most_common_error[0] == "rate_limit":
                    insights["recommendations"].append("Rate limiting detected. Consider implementing request throttling or upgrading your integration plan.")
                elif most_common_error[0] == "auth":
                    insights["recommendations"].append("Authentication errors detected. Check and refresh your integration credentials.")
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate performance insights: {e}")
            return {"error": str(e)}
        finally:
            if close_db:
                db.close()


# Global service instance
analytics_service = AnalyticsService()