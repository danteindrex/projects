import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from app.core.logging import log_agent_event
from app.core.kafka_service import publish_agent_event
from app.services.agent_lifecycle import agent_lifecycle_manager

logger = logging.getLogger(__name__)

class AgentPerformanceMonitor:
    def __init__(self):
        self.metrics: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.health_checks: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.alerts: List[Dict[str, Any]] = []
        self.monitoring_config = {
            'response_time_threshold': 5.0,  # seconds
            'error_rate_threshold': 0.1,     # 10%
            'memory_threshold': 0.8,         # 80%
            'cpu_threshold': 0.9,            # 90%
            'check_interval': 30,            # seconds
            'retention_days': 7
        }
    
    async def start_monitoring(self):
        """Start the monitoring loop"""
        logger.info("Starting agent performance monitoring")
        
        while True:
            try:
                await self.collect_metrics()
                await self.run_health_checks()
                await self.check_alerts()
                await self.cleanup_old_data()
                
                await asyncio.sleep(self.monitoring_config['check_interval'])
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def collect_metrics(self):
        """Collect performance metrics from all agents"""
        try:
            agents_status = await agent_lifecycle_manager.get_all_agents_status()
            
            for agent_status in agents_status:
                agent_id = agent_status['id']
                
                # Collect basic metrics
                metrics = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'response_time': agent_status.get('response_time', 0.0),
                    'task_count': agent_status.get('task_count', 0),
                    'error_count': agent_status.get('error_count', 0),
                    'memory_usage': agent_status.get('memory_usage', 0.0),
                    'cpu_usage': agent_status.get('cpu_usage', 0.0),
                    'state': agent_status.get('state', 'unknown')
                }
                
                self.metrics[agent_id].append(metrics)
                
                # Keep only recent metrics
                cutoff = datetime.utcnow() - timedelta(days=self.monitoring_config['retention_days'])
                self.metrics[agent_id] = [
                    m for m in self.metrics[agent_id] 
                    if datetime.fromisoformat(m['timestamp']) > cutoff
                ]
                
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
    
    async def run_health_checks(self):
        """Run health checks on all agents"""
        try:
            agents_status = await agent_lifecycle_manager.get_all_agents_status()
            
            for agent_status in agents_status:
                agent_id = agent_status['id']
                
                health_check = await self._perform_health_check(agent_id, agent_status)
                self.health_checks[agent_id].append(health_check)
                
                # Keep only recent health checks
                cutoff = datetime.utcnow() - timedelta(days=self.monitoring_config['retention_days'])
                self.health_checks[agent_id] = [
                    h for h in self.health_checks[agent_id] 
                    if datetime.fromisoformat(h['timestamp']) > cutoff
                ]
                
        except Exception as e:
            logger.error(f"Failed to run health checks: {e}")
    
    async def _perform_health_check(self, agent_id: str, agent_status: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a health check on a specific agent"""
        try:
            health_check = {
                'timestamp': datetime.utcnow().isoformat(),
                'agent_id': agent_id,
                'overall_health': 'healthy',
                'checks': {},
                'recommendations': []
            }
            
            # Check response time
            response_time = agent_status.get('response_time', 0.0)
            if response_time > self.monitoring_config['response_time_threshold']:
                health_check['checks']['response_time'] = 'warning'
                health_check['recommendations'].append('Response time is high, consider scaling')
            else:
                health_check['checks']['response_time'] = 'healthy'
            
            # Check error rate
            error_count = agent_status.get('error_count', 0)
            task_count = agent_status.get('task_count', 1)
            error_rate = error_count / max(task_count, 1)
            
            if error_rate > self.monitoring_config['error_rate_threshold']:
                health_check['checks']['error_rate'] = 'critical'
                health_check['overall_health'] = 'unhealthy'
                health_check['recommendations'].append('Error rate is high, investigate issues')
            else:
                health_check['checks']['error_rate'] = 'healthy'
            
            # Check memory usage
            memory_usage = agent_status.get('memory_usage', 0.0)
            if memory_usage > self.monitoring_config['memory_threshold']:
                health_check['checks']['memory'] = 'warning'
                health_check['recommendations'].append('Memory usage is high, consider optimization')
            else:
                health_check['checks']['memory'] = 'healthy'
            
            # Check CPU usage
            cpu_usage = agent_status.get('cpu_usage', 0.0)
            if cpu_usage > self.monitoring_config['cpu_threshold']:
                health_check['checks']['cpu'] = 'warning'
                health_check['recommendations'].append('CPU usage is high, consider scaling')
            else:
                health_check['checks']['cpu'] = 'healthy'
            
            # Check agent state
            state = agent_status.get('state', 'unknown')
            if state in ['error', 'stopped']:
                health_check['checks']['state'] = 'critical'
                health_check['overall_health'] = 'unhealthy'
                health_check['recommendations'].append('Agent is in error state, restart required')
            else:
                health_check['checks']['state'] = 'healthy'
            
            return health_check
            
        except Exception as e:
            logger.error(f"Failed to perform health check on agent {agent_id}: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'agent_id': agent_id,
                'overall_health': 'unknown',
                'checks': {},
                'recommendations': ['Health check failed'],
                'error': str(e)
            }
    
    async def check_alerts(self):
        """Check for conditions that require alerts"""
        try:
            for agent_id, health_checks in self.health_checks.items():
                if not health_checks:
                    continue
                
                latest_check = health_checks[-1]
                
                if latest_check['overall_health'] == 'unhealthy':
                    await self._create_alert(agent_id, 'critical', latest_check)
                elif latest_check['overall_health'] == 'warning':
                    await self._create_alert(agent_id, 'warning', latest_check)
                    
        except Exception as e:
            logger.error(f"Failed to check alerts: {e}")
    
    async def _create_alert(self, agent_id: str, severity: str, health_check: Dict[str, Any]):
        """Create an alert for an agent"""
        try:
            alert = {
                'id': f"alert_{int(time.time())}_{agent_id}",
                'agent_id': agent_id,
                'severity': severity,
                'timestamp': datetime.utcnow().isoformat(),
                'message': f"Agent {agent_id} health check: {health_check['overall_health']}",
                'details': health_check,
                'acknowledged': False
            }
            
            self.alerts.append(alert)
            
            # Publish alert to Kafka
            await publish_agent_event(agent_id, "alert_created", alert)
            
            log_agent_event(agent_id, "alert_created", alert=alert)
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
    
    async def cleanup_old_data(self):
        """Clean up old metrics and health checks"""
        try:
            cutoff = datetime.utcnow() - timedelta(days=self.monitoring_config['retention_days'])
            
            # Clean up old metrics
            for agent_id in list(self.metrics.keys()):
                self.metrics[agent_id] = [
                    m for m in self.metrics[agent_id] 
                    if datetime.fromisoformat(m['timestamp']) > cutoff
                ]
            
            # Clean up old health checks
            for agent_id in list(self.health_checks.keys()):
                self.health_checks[agent_id] = [
                    h for h in self.health_checks[agent_id] 
                    if datetime.fromisoformat(h['timestamp']) > cutoff
                ]
            
            # Clean up old alerts
            self.alerts = [
                a for a in self.alerts 
                if datetime.fromisoformat(a['timestamp']) > cutoff
            ]
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    def get_agent_metrics(self, agent_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics for a specific agent"""
        try:
            if agent_id not in self.metrics:
                return []
            
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            return [
                m for m in self.metrics[agent_id] 
                if datetime.fromisoformat(m['timestamp']) > cutoff
            ]
            
        except Exception as e:
            logger.error(f"Failed to get metrics for agent {agent_id}: {e}")
            return []
    
    def get_agent_health_history(self, agent_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health check history for a specific agent"""
        try:
            if agent_id not in self.health_checks:
                return []
            
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            return [
                h for h in self.health_checks[agent_id] 
                if datetime.fromisoformat(h['timestamp']) > cutoff
            ]
            
        except Exception as e:
            logger.error(f"Failed to get health history for agent {agent_id}: {e}")
            return []
    
    def get_performance_summary(self, agent_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for an agent"""
        try:
            metrics = self.get_agent_metrics(agent_id, hours)
            
            if not metrics:
                return {}
            
            response_times = [m['response_time'] for m in metrics if m['response_time'] > 0]
            error_counts = [m['error_count'] for m in metrics]
            task_counts = [m['task_count'] for m in metrics]
            
            summary = {
                'agent_id': agent_id,
                'period_hours': hours,
                'total_checks': len(metrics),
                'avg_response_time': statistics.mean(response_times) if response_times else 0.0,
                'max_response_time': max(response_times) if response_times else 0.0,
                'total_errors': max(error_counts) if error_counts else 0,
                'total_tasks': max(task_counts) if task_counts else 0,
                'error_rate': max(error_counts) / max(max(task_counts), 1) if task_counts else 0.0,
                'last_check': metrics[-1]['timestamp'] if metrics else None
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get performance summary for agent {agent_id}: {e}")
            return {}
    
    def get_all_alerts(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all alerts, optionally filtered by severity"""
        try:
            if severity:
                return [a for a in self.alerts if a['severity'] == severity]
            return self.alerts
            
        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            return []
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        try:
            for alert in self.alerts:
                if alert['id'] == alert_id:
                    alert['acknowledged'] = True
                    alert['acknowledged_at'] = datetime.utcnow().isoformat()
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
            return False

# Global instance
agent_monitor = AgentPerformanceMonitor()

# Convenience functions
async def start_monitoring():
    """Start the monitoring system"""
    await agent_monitor.start_monitoring()

def get_agent_metrics(agent_id: str, hours: int = 24) -> List[Dict[str, Any]]:
    """Get metrics for an agent"""
    return agent_monitor.get_agent_metrics(agent_id, hours)

def get_performance_summary(agent_id: str, hours: int = 24) -> Dict[str, Any]:
    """Get performance summary for an agent"""
    return agent_monitor.get_performance_summary(agent_id, hours)

def get_all_alerts(severity: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get all alerts"""
    return agent_monitor.get_all_alerts(severity)
