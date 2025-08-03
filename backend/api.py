from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func, delete
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import pytz
from .database import get_database, init_database
from .models import ConnectivityTest, SpeedTest, OutageEvent, MonitoringStats, VPNStatus, VPNEvent, VPNUsageStats
from pydantic import BaseModel

app = FastAPI(title="UpTime Monitor API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up Arizona timezone
arizona_tz = pytz.timezone('America/Phoenix')

def get_arizona_time() -> datetime:
    """Get current time in Arizona timezone"""
    utc_now = datetime.utcnow()
    return utc_now.replace(tzinfo=pytz.UTC).astimezone(arizona_tz)

# Pydantic models for API responses
class ConnectivityTestResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    id: int
    timestamp: datetime
    is_connected: bool
    latency_ms: Optional[float]
    target_host: str
    test_type: str
    error_message: Optional[str]

class SpeedTestResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    id: int
    timestamp: datetime
    download_mbps: Optional[float]
    upload_mbps: Optional[float]
    ping_ms: Optional[float]
    server_name: Optional[str]
    server_location: Optional[str]
    success: bool
    error_message: Optional[str]
    vpn_active: Optional[bool]
    vpn_provider: Optional[str]

class OutageEventResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    id: int
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[int]
    severity: str
    description: Optional[str]
    is_resolved: bool

class DashboardStats(BaseModel):
    model_config = {"from_attributes": True}
    
    current_status: str
    uptime_24h: float
    avg_speed_24h: Optional[float]
    total_outages_24h: int
    current_latency: Optional[float]
    last_speed_test: Optional[SpeedTestResponse]
    vpn_status: Optional[Dict]

class ChartDataPoint(BaseModel):
    model_config = {"from_attributes": True}
    
    timestamp: datetime
    value: float
    label: str

class VPNStatusResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    id: int
    timestamp: datetime
    is_active: bool
    provider: Optional[str]
    public_ip: Optional[str]
    server_location: Optional[str]
    interface_name: Optional[str]
    detection_method: str
    confidence: float
    connection_time: Optional[datetime]

class VPNEventResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    id: int
    timestamp: datetime
    event_type: str
    provider: Optional[str]
    public_ip: Optional[str]
    confidence: float
    duration_minutes: Optional[int]

class VPNUsageStatsResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    total_time_minutes: float
    usage_percentage: float
    connection_count: int
    providers_used: List[str]
    avg_confidence: float
    current_status: Optional[Dict]

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_database()

@app.get("/")
async def root():
    """API root endpoint"""
    return {"message": "UpTime Monitor API", "version": "1.0.0"}

@app.get("/api/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_database)):
    """Get dashboard statistics"""
    now = get_arizona_time()
    yesterday = now - timedelta(days=1)
    
    # Get connectivity tests from last 24 hours
    connectivity_query = select(ConnectivityTest).where(
        ConnectivityTest.timestamp >= yesterday
    ).order_by(desc(ConnectivityTest.timestamp))
    
    connectivity_result = await db.execute(connectivity_query)
    connectivity_tests = connectivity_result.scalars().all()
    
    # Calculate uptime percentage
    if connectivity_tests:
        total_tests = len(connectivity_tests)
        successful_tests = sum(1 for t in connectivity_tests if t.is_connected)
        uptime_24h = (successful_tests / total_tests) * 100
        
        # Get current status from most recent test
        latest_test = connectivity_tests[0] if connectivity_tests else None
        current_status = "connected" if latest_test and latest_test.is_connected else "disconnected"
        current_latency = latest_test.latency_ms if latest_test else None
    else:
        uptime_24h = 0.0
        current_status = "unknown"
        current_latency = None
    
    # Get speed tests from last 24 hours
    speed_query = select(SpeedTest).where(
        and_(SpeedTest.timestamp >= yesterday, SpeedTest.success == True)
    ).order_by(desc(SpeedTest.timestamp))
    
    speed_result = await db.execute(speed_query)
    speed_tests = speed_result.scalars().all()
    
    # Calculate average speed
    if speed_tests:
        avg_download = sum(t.download_mbps for t in speed_tests if t.download_mbps) / len(speed_tests)
        last_speed_test = SpeedTestResponse.model_validate(speed_tests[0])
    else:
        avg_download = None
        last_speed_test = None
    
    # Get outages from last 24 hours
    outage_query = select(OutageEvent).where(
        OutageEvent.start_time >= yesterday
    )
    outage_result = await db.execute(outage_query)
    outages = outage_result.scalars().all()
    
    # Get current VPN status
    vpn_query = select(VPNStatus).order_by(desc(VPNStatus.timestamp)).limit(1)
    vpn_result = await db.execute(vpn_query)
    latest_vpn = vpn_result.scalar_one_or_none()
    
    vpn_status = None
    if latest_vpn:
        vpn_status = {
            "is_active": latest_vpn.is_active,
            "provider": latest_vpn.provider,
            "public_ip": latest_vpn.public_ip,
            "confidence": latest_vpn.confidence,
            "detection_method": latest_vpn.detection_method
        }
    
    return DashboardStats(
        current_status=current_status,
        uptime_24h=uptime_24h,
        avg_speed_24h=avg_download,
        total_outages_24h=len(outages),
        current_latency=current_latency,
        last_speed_test=last_speed_test,
        vpn_status=vpn_status
    )

@app.get("/api/connectivity", response_model=List[ConnectivityTestResponse])
async def get_connectivity_tests(
    hours: int = Query(24, description="Hours of history to retrieve"),
    db: AsyncSession = Depends(get_database)
):
    """Get connectivity test history"""
    since = get_arizona_time() - timedelta(hours=hours)
    
    query = select(ConnectivityTest).where(
        ConnectivityTest.timestamp >= since
    ).order_by(desc(ConnectivityTest.timestamp)).limit(1000)
    
    result = await db.execute(query)
    tests = result.scalars().all()
    
    return [ConnectivityTestResponse.model_validate(test) for test in tests]

@app.get("/api/speed-tests", response_model=List[SpeedTestResponse])
async def get_speed_tests(
    hours: int = Query(24, description="Hours of history to retrieve"),
    vpn_only: bool = Query(False, description="Filter for VPN-only tests"),
    no_vpn: bool = Query(False, description="Filter for non-VPN tests"),
    db: AsyncSession = Depends(get_database)
):
    """Get speed test history with optional VPN filtering"""
    since = get_arizona_time() - timedelta(hours=hours)
    
    query = select(SpeedTest).where(SpeedTest.timestamp >= since)
    
    if vpn_only:
        query = query.where(SpeedTest.vpn_active == True)
    elif no_vpn:
        query = query.where(SpeedTest.vpn_active == False)
    
    query = query.order_by(desc(SpeedTest.timestamp))
    
    result = await db.execute(query)
    tests = result.scalars().all()
    
    return [SpeedTestResponse.model_validate(test) for test in tests]

@app.get("/api/outages", response_model=List[OutageEventResponse])
async def get_outages(
    days: int = Query(7, description="Days of history to retrieve"),
    db: AsyncSession = Depends(get_database)
):
    """Get outage history"""
    since = get_arizona_time() - timedelta(days=days)
    
    query = select(OutageEvent).where(
        OutageEvent.start_time >= since
    ).order_by(desc(OutageEvent.start_time))
    
    result = await db.execute(query)
    outages = result.scalars().all()
    
    return [OutageEventResponse.model_validate(outage) for outage in outages]

@app.get("/api/vpn/status", response_model=VPNStatusResponse)
async def get_current_vpn_status(db: AsyncSession = Depends(get_database)):
    """Get current VPN status"""
    query = select(VPNStatus).order_by(desc(VPNStatus.timestamp)).limit(1)
    result = await db.execute(query)
    vpn_status = result.scalar_one_or_none()
    
    if not vpn_status:
        raise HTTPException(status_code=404, detail="No VPN status data available")
    
    return VPNStatusResponse.model_validate(vpn_status)

@app.get("/api/vpn/history", response_model=List[VPNStatusResponse])
async def get_vpn_history(
    hours: int = Query(24, description="Hours of history to retrieve"),
    db: AsyncSession = Depends(get_database)
):
    """Get VPN status history"""
    since = get_arizona_time() - timedelta(hours=hours)
    
    query = select(VPNStatus).where(
        VPNStatus.timestamp >= since
    ).order_by(desc(VPNStatus.timestamp))
    
    result = await db.execute(query)
    vpn_statuses = result.scalars().all()
    
    return [VPNStatusResponse.model_validate(status) for status in vpn_statuses]

@app.get("/api/vpn/events", response_model=List[VPNEventResponse])
async def get_vpn_events(
    days: int = Query(7, description="Days of history to retrieve"),
    db: AsyncSession = Depends(get_database)
):
    """Get VPN connection/disconnection events"""
    since = get_arizona_time() - timedelta(days=days)
    
    query = select(VPNEvent).where(
        VPNEvent.timestamp >= since
    ).order_by(desc(VPNEvent.timestamp))
    
    result = await db.execute(query)
    events = result.scalars().all()
    
    return [VPNEventResponse.model_validate(event) for event in events]

@app.get("/api/vpn/stats", response_model=VPNUsageStatsResponse)
async def get_vpn_usage_stats(
    hours: int = Query(24, description="Hours to calculate stats for"),
    db: AsyncSession = Depends(get_database)
):
    """Get VPN usage statistics"""
    since = get_arizona_time() - timedelta(hours=hours)
    
    # Get VPN status history
    vpn_query = select(VPNStatus).where(VPNStatus.timestamp >= since)
    vpn_result = await db.execute(vpn_query)
    vpn_statuses = vpn_result.scalars().all()
    
    # Get current VPN status
    current_query = select(VPNStatus).order_by(desc(VPNStatus.timestamp)).limit(1)
    current_result = await db.execute(current_query)
    current_vpn = current_result.scalar_one_or_none()
    
    if not vpn_statuses:
        return VPNUsageStatsResponse(
            total_time_minutes=0,
            usage_percentage=0,
            connection_count=0,
            providers_used=[],
            avg_confidence=0,
            current_status=None
        )
    
    # Calculate statistics
    total_entries = len(vpn_statuses)
    vpn_active_entries = sum(1 for status in vpn_statuses if status.is_active)
    usage_percentage = (vpn_active_entries / total_entries) * 100
    
    # Estimate total VPN time (assuming 30-second intervals)
    total_time_minutes = (vpn_active_entries * 30) / 60
    
    # Count unique providers
    providers = set(status.provider for status in vpn_statuses if status.provider)
    
    # Average confidence
    avg_confidence = sum(status.confidence for status in vpn_statuses) / total_entries
    
    # Count connection events
    event_query = select(VPNEvent).where(
        and_(VPNEvent.timestamp >= since, VPNEvent.event_type == 'connected')
    )
    event_result = await db.execute(event_query)
    connection_count = len(event_result.scalars().all())
    
    # Current status
    current_status = None
    if current_vpn:
        current_status = {
            "is_active": current_vpn.is_active,
            "provider": current_vpn.provider,
            "public_ip": current_vpn.public_ip,
            "confidence": current_vpn.confidence,
            "detection_method": current_vpn.detection_method
        }
    
    return VPNUsageStatsResponse(
        total_time_minutes=round(total_time_minutes, 1),
        usage_percentage=round(usage_percentage, 1),
        connection_count=connection_count,
        providers_used=list(providers),
        avg_confidence=round(avg_confidence, 2),
        current_status=current_status
    )

@app.get("/api/vpn/speed-impact")
async def get_vpn_speed_impact(
    hours: int = Query(24, description="Hours to analyze"),
    db: AsyncSession = Depends(get_database)
):
    """Get speed test impact analysis with and without VPN"""
    since = get_arizona_time() - timedelta(hours=hours)
    
    # Get speed tests with VPN
    vpn_speed_query = select(SpeedTest).where(
        and_(
            SpeedTest.timestamp >= since,
            SpeedTest.success == True,
            SpeedTest.vpn_active == True,
            SpeedTest.download_mbps.isnot(None)
        )
    )
    vpn_result = await db.execute(vpn_speed_query)
    vpn_speeds = vpn_result.scalars().all()
    
    # Get speed tests without VPN
    no_vpn_speed_query = select(SpeedTest).where(
        and_(
            SpeedTest.timestamp >= since,
            SpeedTest.success == True,
            SpeedTest.vpn_active == False,
            SpeedTest.download_mbps.isnot(None)
        )
    )
    no_vpn_result = await db.execute(no_vpn_speed_query)
    no_vpn_speeds = no_vpn_result.scalars().all()
    
    # Calculate averages
    vpn_avg = sum(s.download_mbps for s in vpn_speeds) / len(vpn_speeds) if vpn_speeds else 0
    no_vpn_avg = sum(s.download_mbps for s in no_vpn_speeds) / len(no_vpn_speeds) if no_vpn_speeds else 0
    
    # Calculate impact
    if no_vpn_avg > 0:
        impact_percentage = ((no_vpn_avg - vpn_avg) / no_vpn_avg) * 100
    else:
        impact_percentage = 0
    
    return {
        "analysis_period_hours": hours,
        "vpn_tests_count": len(vpn_speeds),
        "no_vpn_tests_count": len(no_vpn_speeds),
        "vpn_avg_speed_mbps": round(vpn_avg, 2),
        "no_vpn_avg_speed_mbps": round(no_vpn_avg, 2),
        "speed_impact_percentage": round(impact_percentage, 1),
        "impact_description": f"VPN reduces speed by {round(impact_percentage, 1)}%" if impact_percentage > 0 else "No significant impact detected"
    }

@app.get("/api/charts/uptime", response_model=List[ChartDataPoint])
async def get_uptime_chart_data(
    hours: int = Query(24, description="Hours of data for chart"),
    db: AsyncSession = Depends(get_database)
):
    """Get uptime data for charts"""
    since = get_arizona_time() - timedelta(hours=hours)
    
    # Get connectivity tests for the period
    query = select(ConnectivityTest).where(
        ConnectivityTest.timestamp >= since
    ).order_by(ConnectivityTest.timestamp)
    
    result = await db.execute(query)
    tests = result.scalars().all()
    
    return [
        ChartDataPoint(
            timestamp=test.timestamp,
            value=100.0 if test.is_connected else 0.0,
            label="Connected" if test.is_connected else "Disconnected"
        ) for test in tests
    ]

@app.get("/api/charts/speed", response_model=List[ChartDataPoint])
async def get_speed_chart_data(
    hours: int = Query(24, description="Hours of data for chart"),
    metric: str = Query("download", description="Speed metric: download, upload, or ping"),
    vpn_only: bool = Query(False, description="Filter for VPN-only tests"),
    no_vpn: bool = Query(False, description="Filter for non-VPN tests"),
    db: AsyncSession = Depends(get_database)
):
    """Get speed data for charts with optional VPN filtering"""
    since = get_arizona_time() - timedelta(hours=hours)
    
    if metric == "download":
        value_column = SpeedTest.download_mbps
        unit = "Mbps"
    elif metric == "upload":
        value_column = SpeedTest.upload_mbps
        unit = "Mbps"
    else:  # ping
        value_column = SpeedTest.ping_ms
        unit = "ms"
    
    query = select(SpeedTest).where(
        and_(
            SpeedTest.timestamp >= since,
            SpeedTest.success == True,
            value_column.isnot(None)
        )
    )
    
    if vpn_only:
        query = query.where(SpeedTest.vpn_active == True)
    elif no_vpn:
        query = query.where(SpeedTest.vpn_active == False)
    
    query = query.order_by(SpeedTest.timestamp)
    
    result = await db.execute(query)
    tests = result.scalars().all()
    
    return [
        ChartDataPoint(
            timestamp=test.timestamp,
            value=getattr(test, metric + "_mbps" if metric != "ping" else "ping_ms"),
            label=f"{getattr(test, metric + '_mbps' if metric != 'ping' else 'ping_ms'):.1f} {unit}"
        ) for test in tests
    ]

@app.get("/api/report")
async def generate_report(
    days: int = Query(7, description="Days to include in report"),
    db: AsyncSession = Depends(get_database)
):
    """Generate a comprehensive monitoring report"""
    since = get_arizona_time() - timedelta(days=days)
    
    # Get all data for the period
    connectivity_query = select(ConnectivityTest).where(ConnectivityTest.timestamp >= since)
    speed_query = select(SpeedTest).where(SpeedTest.timestamp >= since)
    outage_query = select(OutageEvent).where(OutageEvent.start_time >= since)
    vpn_query = select(VPNStatus).where(VPNStatus.timestamp >= since)
    
    connectivity_result = await db.execute(connectivity_query)
    speed_result = await db.execute(speed_query)
    outage_result = await db.execute(outage_query)
    vpn_result = await db.execute(vpn_query)
    
    connectivity_tests = connectivity_result.scalars().all()
    speed_tests = speed_result.scalars().all()
    outages = outage_result.scalars().all()
    vpn_statuses = vpn_result.scalars().all()
    
    # Calculate comprehensive stats
    if connectivity_tests:
        total_tests = len(connectivity_tests)
        successful_tests = sum(1 for t in connectivity_tests if t.is_connected)
        overall_uptime = (successful_tests / total_tests) * 100
        avg_latency = sum(t.latency_ms for t in connectivity_tests if t.latency_ms) / max(1, len([t for t in connectivity_tests if t.latency_ms]))
    else:
        overall_uptime = 0
        avg_latency = 0
    
    successful_speed_tests = [t for t in speed_tests if t.success]
    if successful_speed_tests:
        avg_download = sum(t.download_mbps for t in successful_speed_tests) / len(successful_speed_tests)
        avg_upload = sum(t.upload_mbps for t in successful_speed_tests) / len(successful_speed_tests)
        min_download = min(t.download_mbps for t in successful_speed_tests)
        max_download = max(t.download_mbps for t in successful_speed_tests)
    else:
        avg_download = avg_upload = min_download = max_download = 0
    
    total_outage_time = sum(o.duration_seconds or 0 for o in outages if o.is_resolved)
    
    # VPN statistics
    vpn_active_count = sum(1 for v in vpn_statuses if v.is_active)
    vpn_usage_percentage = (vpn_active_count / len(vpn_statuses)) * 100 if vpn_statuses else 0
    vpn_providers = list(set(v.provider for v in vpn_statuses if v.provider))
    
    # Speed tests with and without VPN
    vpn_speeds = [t for t in successful_speed_tests if t.vpn_active]
    no_vpn_speeds = [t for t in successful_speed_tests if not t.vpn_active]
    
    vpn_avg_speed = sum(t.download_mbps for t in vpn_speeds) / len(vpn_speeds) if vpn_speeds else 0
    no_vpn_avg_speed = sum(t.download_mbps for t in no_vpn_speeds) / len(no_vpn_speeds) if no_vpn_speeds else 0
    
    vpn_impact = ((no_vpn_avg_speed - vpn_avg_speed) / no_vpn_avg_speed) * 100 if no_vpn_avg_speed > 0 else 0
    
    return {
        "period": {
            "start": since.isoformat(),
            "end": get_arizona_time().isoformat(),
            "days": days
        },
        "summary": {
            "overall_uptime_percentage": round(overall_uptime, 2),
            "total_outages": len(outages),
            "total_outage_duration_minutes": round(total_outage_time / 60, 2),
            "avg_latency_ms": round(avg_latency, 2),
            "avg_download_speed_mbps": round(avg_download, 2),
            "avg_upload_speed_mbps": round(avg_upload, 2),
            "min_download_speed_mbps": round(min_download, 2),
            "max_download_speed_mbps": round(max_download, 2)
        },
        "vpn_analysis": {
            "vpn_usage_percentage": round(vpn_usage_percentage, 1),
            "vpn_providers_used": vpn_providers,
            "vpn_tests_count": len(vpn_speeds),
            "no_vpn_tests_count": len(no_vpn_speeds),
            "vpn_avg_speed_mbps": round(vpn_avg_speed, 2),
            "no_vpn_avg_speed_mbps": round(no_vpn_avg_speed, 2),
            "vpn_speed_impact_percentage": round(vpn_impact, 1)
        },
        "outages": [OutageEventResponse.model_validate(outage) for outage in outages],
        "recommendations": [
            "Contact ISP if uptime is below 99%" if overall_uptime < 99 else "Uptime is acceptable",
            "Check for network issues if average latency > 100ms" if avg_latency > 100 else "Latency is good",
            "Consider upgrading plan if speeds are consistently low" if avg_download < 10 else "Speeds are adequate",
            f"VPN reduces speed by {round(vpn_impact, 1)}% - consider disconnecting for speed tests" if vpn_impact > 15 else "VPN impact is minimal"
        ]
    }

@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        # Return default config if file doesn't exist
        return {
            "monitoring": {
                "ping_interval_seconds": 30,
                "speed_test_interval_minutes": 15,
                "connectivity_timeout_seconds": 10,
                "max_retries": 3
            },
            "targets": {
                "ping_hosts": ["8.8.8.8", "1.1.1.1", "google.com"],
                "dns_servers": ["8.8.8.8", "1.1.1.1"]
            },
            "database": {
                "file": "uptime_monitor.db",
                "retention_days": 90
            },
            "alerts": {
                "outage_threshold_seconds": 60,
                "slow_speed_threshold_mbps": 10
            },
            "server": {
                "host": "localhost",
                "port": 8000,
                "debug": True
            },
            "vpn_monitoring": {
                "enabled": True,
                "check_interval_seconds": 30
            }
        }

@app.post("/api/config")
async def save_config(config_data: dict):
    """Save configuration to file"""
    try:
        # Validate the config structure (basic validation)
        required_sections = ["monitoring", "targets", "database", "alerts"]
        for section in required_sections:
            if section not in config_data:
                raise HTTPException(status_code=400, detail=f"Missing required section: {section}")
        
        # Write to config.json
        with open('config.json', 'w') as f:
            json.dump(config_data, f, indent=2)
        
        return {"message": "Configuration saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")

@app.post("/api/cleanup")
async def manual_database_cleanup():
    """Manually trigger database cleanup"""
    try:
        # Load current config to get retention days
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        retention_days = config.get('database', {}).get('retention_days', 90)
        cutoff_date = get_arizona_time() - timedelta(days=retention_days)
        
        # Get database session
        async for db in get_database():
            # Clean up old connectivity tests
            connectivity_delete = delete(ConnectivityTest).where(
                ConnectivityTest.timestamp < cutoff_date
            )
            connectivity_result = await db.execute(connectivity_delete)
            connectivity_deleted = connectivity_result.rowcount
            
            # Clean up old speed tests  
            speed_delete = delete(SpeedTest).where(
                SpeedTest.timestamp < cutoff_date
            )
            speed_result = await db.execute(speed_delete)
            speed_deleted = speed_result.rowcount
            
            # Clean up old resolved outage events
            outage_delete = delete(OutageEvent).where(
                and_(
                    OutageEvent.start_time < cutoff_date,
                    OutageEvent.is_resolved == True
                )
            )
            outage_result = await db.execute(outage_delete)
            outage_deleted = outage_result.rowcount
            
            # Clean up old monitoring stats
            stats_delete = delete(MonitoringStats).where(
                MonitoringStats.date < cutoff_date
            )
            stats_result = await db.execute(stats_delete)
            stats_deleted = stats_result.rowcount
            
            # Clean up old VPN data
            vpn_status_delete = delete(VPNStatus).where(
                VPNStatus.timestamp < cutoff_date
            )
            vpn_status_result = await db.execute(vpn_status_delete)
            vpn_status_deleted = vpn_status_result.rowcount
            
            vpn_event_delete = delete(VPNEvent).where(
                VPNEvent.timestamp < cutoff_date
            )
            vpn_event_result = await db.execute(vpn_event_delete)
            vpn_event_deleted = vpn_event_result.rowcount
            
            await db.commit()
            
            total_deleted = (connectivity_deleted + speed_deleted + outage_deleted + 
                           stats_deleted + vpn_status_deleted + vpn_event_deleted)
            
            return {
                "message": "Database cleanup completed successfully",
                "retention_days": retention_days,
                "cutoff_date": cutoff_date.isoformat(),
                "deleted_records": {
                    "connectivity_tests": connectivity_deleted,
                    "speed_tests": speed_deleted,
                    "outage_events": outage_deleted,
                    "monitoring_stats": stats_deleted,
                    "vpn_status": vpn_status_deleted,
                    "vpn_events": vpn_event_deleted,
                    "total": total_deleted
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database cleanup failed: {str(e)}")

@app.get("/api/health")
async def get_health_status():
    """Get system health and monitoring service status"""
    # Check if monitoring service is running by looking for recent data
    try:
        from .database import get_database
        
        # Get a database session
        async for db in get_database():
            # Check for recent connectivity tests (within last 5 minutes)
            recent_time = get_arizona_time() - timedelta(minutes=5)
            
            connectivity_query = select(ConnectivityTest).where(
                ConnectivityTest.timestamp >= recent_time
            ).limit(1)
            
            result = await db.execute(connectivity_query)
            recent_test = result.scalar_one_or_none()
            
            monitoring_active = recent_test is not None
            
            return {
                "status": "healthy" if monitoring_active else "warning",
                "monitoring_service": {
                    "active": monitoring_active,
                    "last_activity": recent_test.timestamp.isoformat() if recent_test else None,
                    "message": "Monitoring service is active" if monitoring_active else "No recent monitoring activity detected"
                },
                "database": {
                    "connected": True,
                    "message": "Database connection successful"
                },
                "timestamp": get_arizona_time().isoformat()
            }
            
    except Exception as e:
        return {
            "status": "error",
            "monitoring_service": {
                "active": False,
                "last_activity": None,
                "message": f"Health check failed: {str(e)}"
            },
            "database": {
                "connected": False,
                "message": f"Database connection failed: {str(e)}"
            },
            "timestamp": get_arizona_time().isoformat()
        }