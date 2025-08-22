"""
Database models for pre-aggregated analytics metrics.
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.db.database import Base


class MetricsAggregate(Base):
    """Pre-aggregated metrics for faster analytics queries."""
    __tablename__ = "metrics_aggregates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Aggregation metadata
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False, index=True)  # hourly, daily, weekly
    metric_date = Column(DateTime, nullable=False, index=True)  # Start of the period
    
    # Performance metrics
    total_calls = Column(Integer, default=0)
    successful_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)
    avg_response_time = Column(Float, default=0.0)
    min_response_time = Column(Float, default=0.0)
    max_response_time = Column(Float, default=0.0)
    p95_response_time = Column(Float, default=0.0)
    
    # Error metrics
    timeout_errors = Column(Integer, default=0)
    auth_errors = Column(Integer, default=0)
    rate_limit_errors = Column(Integer, default=0)
    connectivity_errors = Column(Integer, default=0)
    other_errors = Column(Integer, default=0)
    
    # Tool usage breakdown (JSON)
    tool_usage = Column(JSON, default={})  # {tool_name: call_count}
    
    # Cost metrics
    estimated_cost = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    integration = relationship("Integration")
    
    # Indexes and constraints for performance
    __table_args__ = (
        UniqueConstraint('integration_id', 'metric_type', 'metric_date', name='uk_metrics_aggregate_unique'),
        Index('idx_metrics_aggregate_integration_type_date', 'integration_id', 'metric_type', 'metric_date'),
        Index('idx_metrics_aggregate_date_type', 'metric_date', 'metric_type'),
    )
    
    def __repr__(self):
        return f"<MetricsAggregate(id={self.id}, integration_id={self.integration_id}, type={self.metric_type}, date={self.metric_date})>"


class IntegrationHealthSnapshot(Base):
    """Periodic snapshots of integration health for trend analysis."""
    __tablename__ = "integration_health_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Snapshot metadata
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=False, index=True)
    snapshot_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Health metrics
    status = Column(String(20), nullable=False)  # healthy, degraded, unhealthy
    response_time_ms = Column(Float, default=0.0)
    uptime_percentage = Column(Float, default=0.0)
    error_count_24h = Column(Integer, default=0)
    
    # Detailed health checks
    connectivity_check = Column(String(20), default="unknown")  # pass, fail, unknown
    auth_check = Column(String(20), default="unknown")
    rate_limit_check = Column(String(20), default="unknown")
    
    # Additional metadata
    health_score = Column(Float, default=0.0)  # 0-100 overall health score
    metadata = Column(JSON, default={})
    
    # Relationships
    integration = relationship("Integration")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_health_snapshot_integration_time', 'integration_id', 'snapshot_time'),
        Index('idx_health_snapshot_time', 'snapshot_time'),
        Index('idx_health_snapshot_status', 'status', 'snapshot_time'),
    )
    
    def __repr__(self):
        return f"<IntegrationHealthSnapshot(id={self.id}, integration_id={self.integration_id}, status={self.status})>"


class CostTracking(Base):
    """Track estimated costs for integrations and API usage."""
    __tablename__ = "cost_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Cost tracking metadata
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    billing_period = Column(String(20), nullable=False, index=True)  # monthly, daily
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Cost metrics
    total_api_calls = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
    cost_per_call = Column(Float, default=0.0)
    
    # Usage breakdown
    usage_by_tool = Column(JSON, default={})  # {tool_name: {calls: int, cost: float}}
    usage_by_day = Column(JSON, default={})   # {date: {calls: int, cost: float}}
    
    # Billing metadata
    cost_model = Column(String(50), default="estimated")  # estimated, actual, tiered
    currency = Column(String(3), default="USD")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    integration = relationship("Integration")
    user = relationship("User")
    
    # Indexes for performance
    __table_args__ = (
        UniqueConstraint('integration_id', 'billing_period', 'period_start', name='uk_cost_tracking_unique'),
        Index('idx_cost_tracking_user_period', 'user_id', 'period_start'),
        Index('idx_cost_tracking_integration_period', 'integration_id', 'period_start'),
    )
    
    def __repr__(self):
        return f"<CostTracking(id={self.id}, integration_id={self.integration_id}, period={self.billing_period})>"