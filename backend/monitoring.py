import asyncio
import time
import json
import subprocess
import socket
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from .models import ConnectivityTest, SpeedTest, OutageEvent, MonitoringStats, VPNStatus, VPNEvent, VPNUsageStats
from .database import AsyncSessionLocal
from .vpn_monitor import VPNMonitor, VPNStatus as VPNStatusData
import logging
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InternetMonitor:
    """Main monitoring service for internet connectivity and speed"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.monitoring_config = config.get('monitoring', {})
        self.targets = config.get('targets', {})
        self.is_running = False
        self.current_outage: Optional[OutageEvent] = None
        # Set up Arizona timezone
        self.arizona_tz = pytz.timezone('America/Phoenix')
        
        # Initialize VPN monitoring
        self.vpn_monitor = None
        if config.get('vpn_monitoring', {}).get('enabled', False):
            self.vpn_monitor = VPNMonitor(config)
            logger.info("VPN monitoring enabled")
    
    def get_arizona_time(self) -> datetime:
        """Get current time in Arizona timezone"""
        utc_now = datetime.utcnow()
        return utc_now.replace(tzinfo=pytz.UTC).astimezone(self.arizona_tz)
        
    async def start_monitoring(self):
        """Start the monitoring service"""
        self.is_running = True
        logger.info("Starting internet monitoring service...")
        
        # Start concurrent monitoring tasks
        tasks = [
            asyncio.create_task(self._ping_monitor()),
            asyncio.create_task(self._speed_test_monitor()),
            asyncio.create_task(self._dns_monitor()),
            asyncio.create_task(self._stats_calculator()),
            asyncio.create_task(self._database_cleanup_service())
        ]
        
        # Add VPN monitoring task if enabled
        if self.vpn_monitor:
            tasks.append(asyncio.create_task(self._vpn_monitor()))
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
        finally:
            self.is_running = False
    
    async def stop_monitoring(self):
        """Stop the monitoring service"""
        self.is_running = False
        logger.info("Stopping internet monitoring service...")
    
    async def _vpn_monitor(self):
        """VPN monitoring task"""
        if not self.vpn_monitor:
            return
            
        while self.is_running:
            try:
                # Detect VPN status
                vpn_status = await self.vpn_monitor.detect_vpn_status()
                
                # Save VPN status to database
                await self._save_vpn_status(vpn_status)
                
                # Handle VPN status changes
                if vpn_status != self.vpn_monitor.current_vpn_status:
                    await self._handle_vpn_status_change(vpn_status)
                    self.vpn_monitor.current_vpn_status = vpn_status
                
                # Wait for next check
                interval = self.config.get('vpn_monitoring', {}).get('check_interval_seconds', 30)
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"VPN monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def _save_vpn_status(self, vpn_status: VPNStatusData):
        """Save VPN status to database"""
        try:
            async with AsyncSessionLocal() as db:
                db_vpn_status = VPNStatus(
                    timestamp=vpn_status.connection_time or self.get_arizona_time(),
                    is_active=vpn_status.is_active,
                    provider=vpn_status.provider,
                    public_ip=vpn_status.public_ip,
                    server_location=vpn_status.server_location,
                    interface_name=vpn_status.interface_name,
                    detection_method=vpn_status.detection_method,
                    confidence=vpn_status.confidence,
                    connection_time=vpn_status.connection_time
                )
                
                db.add(db_vpn_status)
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to save VPN status: {e}")
    
    async def _handle_vpn_status_change(self, new_status: VPNStatusData):
        """Handle VPN status changes"""
        try:
            async with AsyncSessionLocal() as db:
                if new_status.is_active and not (self.vpn_monitor.current_vpn_status and self.vpn_monitor.current_vpn_status.is_active):
                    # VPN connected
                    event = VPNEvent(
                        timestamp=self.get_arizona_time(),
                        event_type='connected',
                        provider=new_status.provider,
                        public_ip=new_status.public_ip,
                        confidence=new_status.confidence
                    )
                    db.add(event)
                    logger.info(f"VPN connected: {new_status.provider or 'Unknown'}")
                    
                elif not new_status.is_active and (self.vpn_monitor.current_vpn_status and self.vpn_monitor.current_vpn_status.is_active):
                    # VPN disconnected
                    # Calculate duration if we have connection time
                    duration_minutes = None
                    if self.vpn_monitor.current_vpn_status.connection_time:
                        duration = self.get_arizona_time() - self.vpn_monitor.current_vpn_status.connection_time
                        duration_minutes = int(duration.total_seconds() / 60)
                    
                    event = VPNEvent(
                        timestamp=self.get_arizona_time(),
                        event_type='disconnected',
                        provider=self.vpn_monitor.current_vpn_status.provider,
                        public_ip=self.vpn_monitor.current_vpn_status.public_ip,
                        confidence=self.vpn_monitor.current_vpn_status.confidence,
                        duration_minutes=duration_minutes
                    )
                    db.add(event)
                    logger.info(f"VPN disconnected: {self.vpn_monitor.current_vpn_status.provider or 'Unknown'}")
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to handle VPN status change: {e}")
    
    async def _ping_monitor(self):
        """Monitor connectivity using ping tests"""
        interval = self.monitoring_config.get('ping_interval_seconds', 30)
        ping_hosts = self.targets.get('ping_hosts', ['8.8.8.8'])
        
        while self.is_running:
            try:
                for host in ping_hosts:
                    result = await self._ping_host(host)
                    await self._save_connectivity_test(result)
                    await self._check_outage_status(result)
                    
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Ping monitor error: {e}")
                await asyncio.sleep(interval)
    
    async def _ping_host(self, host: str) -> Dict:
        """Perform ping test to a specific host"""
        try:
            # Use subprocess for cross-platform ping
            if os.name == 'nt':  # Windows
                cmd = ['ping', '-n', '1', '-w', '5000', host]
            else:  # Unix/Linux/Mac
                cmd = ['ping', '-c', '1', '-W', '5', host]
            
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            end_time = time.time()
            
            latency_ms = (end_time - start_time) * 1000
            success = result.returncode == 0
            
            return {
                'timestamp': self.get_arizona_time(),
                'is_connected': success,
                'latency_ms': latency_ms if success else None,
                'target_host': host,
                'test_type': 'ping',
                'error_message': result.stderr if not success else None
            }
        except Exception as e:
            return {
                'timestamp': self.get_arizona_time(),
                'is_connected': False,
                'latency_ms': None,
                'target_host': host,
                'test_type': 'ping',
                'error_message': str(e)
            }
    
    async def _dns_monitor(self):
        """Monitor DNS resolution"""
        interval = self.monitoring_config.get('ping_interval_seconds', 30)
        dns_servers = self.targets.get('dns_servers', ['8.8.8.8'])
        
        while self.is_running:
            try:
                for dns_server in dns_servers:
                    result = await self._test_dns(dns_server)
                    await self._save_connectivity_test(result)
                    
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"DNS monitor error: {e}")
                await asyncio.sleep(interval)
    
    async def _test_dns(self, dns_server: str) -> Dict:
        """Test DNS resolution"""
        try:
            start_time = time.time()
            
            # Test DNS resolution
            socket.gethostbyname('google.com')
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            return {
                'timestamp': self.get_arizona_time(),
                'is_connected': True,
                'latency_ms': latency_ms,
                'target_host': dns_server,
                'test_type': 'dns',
                'error_message': None
            }
        except Exception as e:
            return {
                'timestamp': self.get_arizona_time(),
                'is_connected': False,
                'latency_ms': None,
                'target_host': dns_server,
                'test_type': 'dns',
                'error_message': str(e)
            }
    
    async def _speed_test_monitor(self):
        """Monitor internet speed"""
        interval_minutes = self.monitoring_config.get('speed_test_interval_minutes', 15)
        interval_seconds = interval_minutes * 60
        
        while self.is_running:
            try:
                # Get current VPN status for speed test
                vpn_active = False
                vpn_provider = None
                if self.vpn_monitor and self.vpn_monitor.current_vpn_status:
                    vpn_active = self.vpn_monitor.current_vpn_status.is_active
                    vpn_provider = self.vpn_monitor.current_vpn_status.provider
                
                result = await self._run_speed_test(vpn_active, vpn_provider)
                await self._save_speed_test(result)
                
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Speed test monitor error: {e}")
                await asyncio.sleep(interval_seconds)
    
    async def _run_speed_test(self, vpn_active: bool = False, vpn_provider: Optional[str] = None) -> Dict:
        """Run internet speed test"""
        try:
            speed_test_config = self.config.get('speed_test', {})
            method = speed_test_config.get('method', 'speedtest-cli')
            timeout = speed_test_config.get('timeout_seconds', 60)
            
            if method == 'speedtest-cli':
                return await self._run_speedtest_cli(timeout, vpn_active, vpn_provider)
            else:
                return await self._run_http_speed_test(timeout, vpn_active, vpn_provider)
                
        except Exception as e:
            return {
                'timestamp': self.get_arizona_time(),
                'success': False,
                'download_mbps': None,
                'upload_mbps': None,
                'ping_ms': None,
                'server_name': None,
                'server_location': None,
                'error_message': str(e),
                'vpn_active': vpn_active,
                'vpn_provider': vpn_provider
            }
    
    async def _run_speedtest_cli(self, timeout: int, vpn_active: bool, vpn_provider: Optional[str]) -> Dict:
        """Run speed test using speedtest-cli"""
        try:
            cmd = ['speedtest-cli', '--json', '--timeout', str(timeout)]
            
            # Run speed test
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                return {
                    'timestamp': self.get_arizona_time(),
                    'success': True,
                    'download_mbps': data.get('download', 0) / 1_000_000,  # Convert from bytes/s to Mbps
                    'upload_mbps': data.get('upload', 0) / 1_000_000,  # Convert from bytes/s to Mbps
                    'ping_ms': data.get('ping', 0),
                    'server_name': data.get('server', {}).get('name', 'Unknown'),
                    'server_location': data.get('server', {}).get('country', 'Unknown'),
                    'error_message': None,
                    'vpn_active': vpn_active,
                    'vpn_provider': vpn_provider
                }
            else:
                return {
                    'timestamp': self.get_arizona_time(),
                    'success': False,
                    'download_mbps': None,
                    'upload_mbps': None,
                    'ping_ms': None,
                    'server_name': None,
                    'server_location': None,
                    'error_message': result.stderr,
                    'vpn_active': vpn_active,
                    'vpn_provider': vpn_provider
                }
                
        except subprocess.TimeoutExpired:
            return {
                'timestamp': self.get_arizona_time(),
                'success': False,
                'download_mbps': None,
                'upload_mbps': None,
                'ping_ms': None,
                'server_name': None,
                'server_location': None,
                'error_message': 'Speed test timed out',
                'vpn_active': vpn_active,
                'vpn_provider': vpn_provider
            }
        except Exception as e:
            return {
                'timestamp': self.get_arizona_time(),
                'success': False,
                'download_mbps': None,
                'upload_mbps': None,
                'ping_ms': None,
                'server_name': None,
                'server_location': None,
                'error_message': str(e),
                'vpn_active': vpn_active,
                'vpn_provider': vpn_provider
            }
    
    async def _run_http_speed_test(self, timeout: int, vpn_active: bool, vpn_provider: Optional[str]) -> Dict:
        """Run HTTP-based speed test as fallback"""
        try:
            # Simple HTTP download test
            test_url = "https://httpbin.org/bytes/1048576"  # 1MB file
            
            start_time = time.time()
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(test_url)
                end_time = time.time()
            
            if response.status_code == 200:
                duration = end_time - start_time
                file_size_mb = 1  # 1MB
                download_mbps = (file_size_mb * 8) / duration  # Convert to Mbps
                
                # Apply calibration factor
                calibration_factor = self.config.get('speed_test', {}).get('calibration_factor', 15.0)
                download_mbps *= calibration_factor
                
                return {
                    'timestamp': self.get_arizona_time(),
                    'success': True,
                    'download_mbps': download_mbps,
                    'upload_mbps': None,  # HTTP test doesn't measure upload
                    'ping_ms': None,
                    'server_name': 'HTTP Test',
                    'server_location': 'Unknown',
                    'error_message': None,
                    'vpn_active': vpn_active,
                    'vpn_provider': vpn_provider
                }
            else:
                return {
                    'timestamp': self.get_arizona_time(),
                    'success': False,
                    'download_mbps': None,
                    'upload_mbps': None,
                    'ping_ms': None,
                    'server_name': None,
                    'server_location': None,
                    'error_message': f'HTTP test failed with status {response.status_code}',
                    'vpn_active': vpn_active,
                    'vpn_provider': vpn_provider
                }
                
        except Exception as e:
            return {
                'timestamp': self.get_arizona_time(),
                'success': False,
                'download_mbps': None,
                'upload_mbps': None,
                'ping_ms': None,
                'server_name': None,
                'server_location': None,
                'error_message': str(e),
                'vpn_active': vpn_active,
                'vpn_provider': vpn_provider
            }
    
    async def _save_connectivity_test(self, result: Dict):
        """Save connectivity test result to database"""
        try:
            async with AsyncSessionLocal() as db:
                test = ConnectivityTest(
                    timestamp=result['timestamp'],
                    is_connected=result['is_connected'],
                    latency_ms=result['latency_ms'],
                    target_host=result['target_host'],
                    test_type=result['test_type'],
                    error_message=result['error_message']
                )
                
                db.add(test)
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to save connectivity test: {e}")
    
    async def _save_speed_test(self, result: Dict):
        """Save speed test result to database"""
        try:
            async with AsyncSessionLocal() as db:
                test = SpeedTest(
                    timestamp=result['timestamp'],
                    download_mbps=result['download_mbps'],
                    upload_mbps=result['upload_mbps'],
                    ping_ms=result['ping_ms'],
                    server_name=result['server_name'],
                    server_location=result['server_location'],
                    success=result['success'],
                    error_message=result['error_message'],
                    vpn_active=result['vpn_active'],
                    vpn_provider=result['vpn_provider']
                )
                
                db.add(test)
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to save speed test: {e}")
    
    async def _check_outage_status(self, result: Dict):
        """Check and update outage status"""
        try:
            async with AsyncSessionLocal() as db:
                if not result['is_connected']:
                    # Connection failed
                    if not self.current_outage:
                        # Start new outage
                        self.current_outage = OutageEvent(
                            start_time=result['timestamp'],
                            severity='complete' if result['test_type'] == 'ping' else 'partial',
                            description=f"Connection failed to {result['target_host']} ({result['test_type']})"
                        )
                        db.add(self.current_outage)
                        await db.commit()
                        logger.warning(f"Outage started: {self.current_outage.description}")
                else:
                    # Connection restored
                    if self.current_outage and not self.current_outage.is_resolved:
                        # End current outage
                        self.current_outage.end_time = result['timestamp']
                        self.current_outage.is_resolved = True
                        
                        if self.current_outage.start_time:
                            duration = result['timestamp'] - self.current_outage.start_time
                            self.current_outage.duration_seconds = int(duration.total_seconds())
                        
                        await db.commit()
                        logger.info(f"Outage resolved after {self.current_outage.duration_seconds} seconds")
                        self.current_outage = None
                        
        except Exception as e:
            logger.error(f"Failed to check outage status: {e}")
    
    async def _stats_calculator(self):
        """Calculate and store monitoring statistics"""
        interval = 3600  # Calculate stats every hour
        
        while self.is_running:
            try:
                await self._calculate_hourly_stats()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Stats calculator error: {e}")
                await asyncio.sleep(interval)
    
    async def _calculate_hourly_stats(self):
        """Calculate hourly monitoring statistics"""
        try:
            async with AsyncSessionLocal() as db:
                now = self.get_arizona_time()
                hour_start = now.replace(minute=0, second=0, microsecond=0)
                hour_end = hour_start + timedelta(hours=1)
                
                # Get connectivity tests for the hour
                connectivity_query = select(ConnectivityTest).where(
                    and_(
                        ConnectivityTest.timestamp >= hour_start,
                        ConnectivityTest.timestamp < hour_end
                    )
                )
                connectivity_result = await db.execute(connectivity_query)
                connectivity_tests = connectivity_result.scalars().all()
                
                if connectivity_tests:
                    total_tests = len(connectivity_tests)
                    successful_tests = sum(1 for t in connectivity_tests if t.is_connected)
                    uptime_percentage = (successful_tests / total_tests) * 100
                    
                    # Calculate average latency
                    latencies = [t.latency_ms for t in connectivity_tests if t.latency_ms]
                    avg_latency_ms = sum(latencies) / len(latencies) if latencies else None
                else:
                    uptime_percentage = 0
                    avg_latency_ms = None
                
                # Get speed tests for the hour
                speed_query = select(SpeedTest).where(
                    and_(
                        SpeedTest.timestamp >= hour_start,
                        SpeedTest.timestamp < hour_end,
                        SpeedTest.success == True
                    )
                )
                speed_result = await db.execute(speed_query)
                speed_tests = speed_result.scalars().all()
                
                if speed_tests:
                    avg_download_mbps = sum(t.download_mbps for t in speed_tests if t.download_mbps) / len(speed_tests)
                    avg_upload_mbps = sum(t.upload_mbps for t in speed_tests if t.upload_mbps) / len(speed_tests)
                else:
                    avg_download_mbps = None
                    avg_upload_mbps = None
                
                # Get outages for the hour
                outage_query = select(OutageEvent).where(
                    and_(
                        OutageEvent.start_time >= hour_start,
                        OutageEvent.start_time < hour_end
                    )
                )
                outage_result = await db.execute(outage_query)
                outages = outage_result.scalars().all()
                
                # Create stats record
                stats = MonitoringStats(
                    date=hour_start,
                    period_type='hourly',
                    uptime_percentage=uptime_percentage,
                    avg_latency_ms=avg_latency_ms,
                    avg_download_mbps=avg_download_mbps,
                    avg_upload_mbps=avg_upload_mbps,
                    total_outages=len(outages),
                    total_tests=len(connectivity_tests)
                )
                
                db.add(stats)
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to calculate hourly stats: {e}")
    
    async def _database_cleanup_service(self):
        """Clean up old database records"""
        interval = 86400  # Run cleanup once per day
        
        while self.is_running:
            try:
                await self._cleanup_old_records()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Database cleanup error: {e}")
                await asyncio.sleep(interval)
    
    async def _cleanup_old_records(self):
        """Clean up old database records"""
        try:
            async with AsyncSessionLocal() as db:
                retention_days = self.config.get('database', {}).get('retention_days', 90)
                cutoff_date = self.get_arizona_time() - timedelta(days=retention_days)
                
                # Clean up old connectivity tests
                connectivity_delete = delete(ConnectivityTest).where(
                    ConnectivityTest.timestamp < cutoff_date
                )
                await db.execute(connectivity_delete)
                
                # Clean up old speed tests
                speed_delete = delete(SpeedTest).where(
                    SpeedTest.timestamp < cutoff_date
                )
                await db.execute(speed_delete)
                
                # Clean up old resolved outage events
                outage_delete = delete(OutageEvent).where(
                    and_(
                        OutageEvent.start_time < cutoff_date,
                        OutageEvent.is_resolved == True
                    )
                )
                await db.execute(outage_delete)
                
                # Clean up old monitoring stats
                stats_delete = delete(MonitoringStats).where(
                    MonitoringStats.date < cutoff_date
                )
                await db.execute(stats_delete)
                
                # Clean up old VPN data
                vpn_status_delete = delete(VPNStatus).where(
                    VPNStatus.timestamp < cutoff_date
                )
                await db.execute(vpn_status_delete)
                
                vpn_event_delete = delete(VPNEvent).where(
                    VPNEvent.timestamp < cutoff_date
                )
                await db.execute(vpn_event_delete)
                
                await db.commit()
                logger.info(f"Cleaned up records older than {retention_days} days")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old records: {e}")