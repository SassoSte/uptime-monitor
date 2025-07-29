from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

Base = declarative_base()

class ConnectivityTest(Base):
    """Model for storing connectivity test results"""
    __tablename__ = "connectivity_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    is_connected = Column(Boolean, nullable=False)
    latency_ms = Column(Float, nullable=True)
    target_host = Column(String(255), nullable=False)
    test_type = Column(String(50), nullable=False)  # ping, dns, http
    error_message = Column(Text, nullable=True)
    
class SpeedTest(Base):
    """Model for storing internet speed test results"""
    __tablename__ = "speed_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    download_mbps = Column(Float, nullable=True)
    upload_mbps = Column(Float, nullable=True)
    ping_ms = Column(Float, nullable=True)
    server_name = Column(String(255), nullable=True)
    server_location = Column(String(255), nullable=True)
    success = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)

class OutageEvent(Base):
    """Model for storing internet outage events"""
    __tablename__ = "outage_events"
    
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    severity = Column(String(50), nullable=False)  # complete, partial, slow
    description = Column(Text, nullable=True)
    is_resolved = Column(Boolean, default=False)

class MonitoringStats(Base):
    """Model for storing daily/hourly monitoring statistics"""
    __tablename__ = "monitoring_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    period_type = Column(String(20), nullable=False)  # hourly, daily
    uptime_percentage = Column(Float, nullable=False)
    avg_latency_ms = Column(Float, nullable=True)
    avg_download_mbps = Column(Float, nullable=True)
    avg_upload_mbps = Column(Float, nullable=True)
    total_outages = Column(Integer, default=0)
    total_tests = Column(Integer, default=0)