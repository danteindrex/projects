"""
Service for tracking tool execution and streaming events.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.tool_execution import ToolExecution, ToolExecutionEvent, StreamingEvent, AgentActivity
from app.models.integration import Integration
from app.models.user import User
from app.tools.base import ToolExecutionResult, ToolExecutionEvent as BaseToolEvent
from app.db.database import get_db_session

logger = logging.getLogger(__name__)


class ToolTrackingService:
    """Service for tracking tool executions and streaming events."""
    
    @staticmethod
    async def start_tool_execution(
        tool_name: str,
        integration_id: int,
        session_id: str,
        user_id: int,
        parameters: Dict[str, Any],
        db: Session = None
    ) -> int:
        """Start tracking a tool execution."""
        if not db:
            db = next(get_db_session())
            close_db = True
        else:
            close_db = False
        
        try:
            execution = ToolExecution(
                tool_name=tool_name,
                integration_id=integration_id,
                session_id=session_id,
                user_id=user_id,
                parameters=parameters,
                started_at=datetime.utcnow()
            )
            
            db.add(execution)
            db.commit()
            db.refresh(execution)
            
            logger.info(f"Started tracking tool execution {execution.id} for {tool_name}")
            return execution.id
            
        except Exception as e:
            logger.error(f"Failed to start tool execution tracking: {e}")
            db.rollback()
            raise
        finally:
            if close_db:
                db.close()
    
    @staticmethod
    async def complete_tool_execution(
        execution_id: int,
        result: ToolExecutionResult,
        db: Session = None
    ) -> None:
        """Complete a tool execution with results."""
        if not db:
            db = next(get_db_session())
            close_db = True
        else:
            close_db = False
        
        try:
            execution = db.query(ToolExecution).filter(ToolExecution.id == execution_id).first()
            if not execution:
                logger.error(f"Tool execution {execution_id} not found")
                return
            
            execution.success = result.success
            execution.result_data = result.data or {}
            execution.error_message = result.error
            execution.execution_time = result.execution_time
            execution.completed_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Completed tool execution {execution_id} with success={result.success}")
            
        except Exception as e:
            logger.error(f"Failed to complete tool execution tracking: {e}")
            db.rollback()
            raise
        finally:
            if close_db:
                db.close()
    
    @staticmethod
    async def log_tool_event(
        execution_id: int,
        event: BaseToolEvent,
        db: Session = None
    ) -> None:
        """Log a tool execution event."""
        if not db:
            db = next(get_db_session())
            close_db = True
        else:
            close_db = False
        
        try:
            db_event = ToolExecutionEvent(
                execution_id=execution_id,
                event_type=event.type,
                message=event.message,
                event_data=event.data or {},
                timestamp=event.timestamp
            )
            
            db.add(db_event)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log tool event: {e}")
            db.rollback()
        finally:
            if close_db:
                db.close()
    
    @staticmethod
    async def log_streaming_event(
        session_id: str,
        user_id: int,
        event_type: str,
        content: str,
        metadata: Dict[str, Any],
        tool_name: str = None,
        integration_id: int = None,
        db: Session = None
    ) -> None:
        """Log a streaming event sent to client."""
        if not db:
            db = next(get_db_session())
            close_db = True
        else:
            close_db = False
        
        try:
            event = StreamingEvent(
                session_id=session_id,
                user_id=user_id,
                event_type=event_type,
                content=content,
                event_metadata=metadata,
                tool_name=tool_name,
                integration_id=integration_id,
                timestamp=datetime.utcnow()
            )
            
            db.add(event)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log streaming event: {e}")
            db.rollback()
        finally:
            if close_db:
                db.close()
    
    @staticmethod
    async def log_agent_activity(
        agent_id: str,
        agent_type: str,
        activity_type: str,
        session_id: str,
        user_id: int,
        integration_id: int = None,
        processing_time: float = 0.0,
        tokens_used: int = 0,
        tools_called: int = 0,
        input_data: Dict[str, Any] = None,
        result_data: Dict[str, Any] = None,
        error_message: str = None,
        success: bool = True,
        db: Session = None
    ) -> None:
        """Log agent activity."""
        if not db:
            db = next(get_db_session())
            close_db = True
        else:
            close_db = False
        
        try:
            activity = AgentActivity(
                agent_id=agent_id,
                agent_type=agent_type,
                activity_type=activity_type,
                session_id=session_id,
                user_id=user_id,
                integration_id=integration_id,
                processing_time=processing_time,
                tokens_used=tokens_used,
                tools_called=tools_called,
                input_data=input_data or {},
                result_data=result_data or {},
                error_message=error_message,
                success=success,
                timestamp=datetime.utcnow()
            )
            
            db.add(activity)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log agent activity: {e}")
            db.rollback()
        finally:
            if close_db:
                db.close()
    
    @staticmethod
    def get_tool_execution_stats(
        user_id: int = None,
        integration_id: int = None,
        tool_name: str = None,
        days: int = 30,
        db: Session = None
    ) -> Dict[str, Any]:
        """Get tool execution statistics."""
        if not db:
            db = next(get_db_session())
            close_db = True
        else:
            close_db = False
        
        try:
            from datetime import timedelta
            from sqlalchemy import func
            
            # Base query
            query = db.query(ToolExecution)
            
            # Apply filters
            if user_id:
                query = query.filter(ToolExecution.user_id == user_id)
            if integration_id:
                query = query.filter(ToolExecution.integration_id == integration_id)
            if tool_name:
                query = query.filter(ToolExecution.tool_name == tool_name)
            if days:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                query = query.filter(ToolExecution.started_at >= cutoff_date)
            
            # Get basic stats
            total_executions = query.count()
            successful_executions = query.filter(ToolExecution.success == True).count()
            failed_executions = total_executions - successful_executions
            
            # Average execution time
            avg_time = db.query(func.avg(ToolExecution.execution_time)).filter(
                query.statement.whereclause
            ).scalar() or 0.0
            
            # Tool usage breakdown
            tool_usage = db.query(
                ToolExecution.tool_name,
                func.count().label('count'),
                func.avg(ToolExecution.execution_time).label('avg_time')
            ).filter(query.statement.whereclause).group_by(
                ToolExecution.tool_name
            ).all()
            
            return {
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "failed_executions": failed_executions,
                "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
                "average_execution_time": round(avg_time, 2),
                "tool_usage": [
                    {
                        "tool_name": usage.tool_name,
                        "count": usage.count,
                        "avg_time": round(usage.avg_time or 0, 2)
                    }
                    for usage in tool_usage
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get tool execution stats: {e}")
            return {}
        finally:
            if close_db:
                db.close()
    
    @staticmethod
    def get_recent_executions(
        user_id: int = None,
        integration_id: int = None,
        limit: int = 50,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """Get recent tool executions."""
        if not db:
            db = next(get_db_session())
            close_db = True
        else:
            close_db = False
        
        try:
            query = db.query(ToolExecution).order_by(ToolExecution.started_at.desc())
            
            if user_id:
                query = query.filter(ToolExecution.user_id == user_id)
            if integration_id:
                query = query.filter(ToolExecution.integration_id == integration_id)
            
            executions = query.limit(limit).all()
            
            return [
                {
                    "id": exec.id,
                    "tool_name": exec.tool_name,
                    "integration_id": exec.integration_id,
                    "success": exec.success,
                    "execution_time": exec.execution_time,
                    "started_at": exec.started_at.isoformat(),
                    "completed_at": exec.completed_at.isoformat() if exec.completed_at else None,
                    "error_message": exec.error_message,
                    "parameters": exec.parameters,
                    "result_data": exec.result_data
                }
                for exec in executions
            ]
            
        except Exception as e:
            logger.error(f"Failed to get recent executions: {e}")
            return []
        finally:
            if close_db:
                db.close()


# Global service instance
tool_tracking_service = ToolTrackingService()