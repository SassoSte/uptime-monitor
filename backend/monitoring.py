import asyncio
import time
import json
import subprocess
import socket
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import httpx
import speedtest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from .models import ConnectivityTest, SpeedTest, OutageEvent, MonitoringStats
from .database import AsyncSessionLocal
import logging

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
                'timestamp': datetime.utcnow(),
                'is_connected': success,
                'latency_ms': latency_ms if success else None,
                'target_host': host,
                'test_type': 'ping',
                'error_message': result.stderr if not success else None
            }
        except Exception as e:
            return {
                'timestamp': datetime.utcnow(),
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
            socket.gethostbyname('google.com')
            end_time = time.time()
            
            latency_ms = (end_time - start_time) * 1000
            
            return {
                'timestamp': datetime.utcnow(),
                'is_connected': True,
                'latency_ms': latency_ms,
                'target_host': dns_server,
                'test_type': 'dns',
                'error_message': None
            }
        except Exception as e:
            return {
                'timestamp': datetime.utcnow(),
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
                result = await self._run_speed_test()
                await self._save_speed_test(result)
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Speed test error: {e}")
                await asyncio.sleep(interval_seconds)
    
    async def _run_speed_test(self) -> Dict:
        """Run internet speed test"""
        try:
            st = speedtest.Speedtest()
            st.get_best_server()
            
            download_speed = st.download() / 1_000_000  # Convert to Mbps
            upload_speed = st.upload() / 1_000_000      # Convert to Mbps
            ping_result = st.results.ping
            
            server_info = st.results.server
            
            return {
                'timestamp': datetime.utcnow(),
                'download_mbps': download_speed,
                'upload_mbps': upload_speed,
                'ping_ms': ping_result,
                'server_name': server_info.get('sponsor', 'Unknown'),
                'server_location': f"{server_info.get('name', 'Unknown')}, {server_info.get('country', 'Unknown')}",
                'success': True,
                'error_message': None
            }
        except Exception as e:
            return {
                'timestamp': datetime.utcnow(),
                'download_mbps': None,
                'upload_mbps': None,
                'ping_ms': None,
                'server_name': None,
                'server_location': None,
                'success': False,
                'error_message': str(e)
            }
    
    async def _save_connectivity_test(self, result: Dict):
        """Save connectivity test result to database"""
        async with AsyncSessionLocal() as session:
            test = ConnectivityTest(**result)
            session.add(test)
            await session.commit()
    
    async def _save_speed_test(self, result: Dict):
        """Save speed test result to database"""
        async with AsyncSessionLocal() as session:
            test = SpeedTest(**result)
            session.add(test)
            await session.commit()
    
    async def _check_outage_status(self, result: Dict):
        """Check if we're in an outage and manage outage events"""
        is_connected = result['is_connected']
        now = datetime.utcnow()
        
        async with AsyncSessionLocal() as session:
            if not is_connected and self.current_outage is None:
                # Start new outage
                self.current_outage = OutageEvent(
                    start_time=now,
                    severity='complete',
                    description=f"Connection failed to {result['target_host']}",
                    is_resolved=False
                )
                session.add(self.current_outage)
                await session.commit()
                logger.warning(f"Outage started at {now}")
                
            elif is_connected and self.current_outage is not None:
                # End current outage
                self.current_outage.end_time = now
                self.current_outage.duration_seconds = int((now - self.current_outage.start_time).total_seconds())
                self.current_outage.is_resolved = True
                
                session.add(self.current_outage)
                await session.commit()
                
                logger.info(f"Outage resolved at {now}, duration: {self.current_outage.duration_seconds}s")
                self.current_outage = None
    
    async def _stats_calculator(self):
        """Calculate and store periodic statistics"""
        while self.is_running:
            try:
                await self._calculate_hourly_stats()
                await self._calculate_daily_stats()
                await asyncio.sleep(3600)  # Run every hour
            except Exception as e:
                logger.error(f"Stats calculation error: {e}")
                await asyncio.sleep(3600)
    
    async def _calculate_hourly_stats(self):
        """Calculate hourly statistics"""
        now = datetime.utcnow()
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        
        async with AsyncSessionLocal() as session:
            # Get connectivity tests for this hour
            query = select(ConnectivityTest).where(
                and_(
                    ConnectivityTest.timestamp >= hour_start,
                    ConnectivityTest.timestamp < hour_start + timedelta(hours=1)
                )
            )
            result = await session.execute(query)
            tests = result.scalars().all()
            
            if tests:
                total_tests = len(tests)
                successful_tests = sum(1 for t in tests if t.is_connected)
                uptime_percentage = (successful_tests / total_tests) * 100
                avg_latency = sum(t.latency_ms for t in tests if t.latency_ms) / max(1, len([t for t in tests if t.latency_ms]))
                
                # Save stats
                stats = MonitoringStats(
                    date=hour_start,
                    period_type='hourly',
                    uptime_percentage=uptime_percentage,
                    avg_latency_ms=avg_latency,
                    total_tests=total_tests
                )
                session.add(stats)
                await session.commit()
    
    async def _calculate_daily_stats(self):
        """Calculate daily statistics"""
        now = datetime.utcnow()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Similar logic to hourly stats but for daily period
        # Implementation would be similar to _calculate_hourly_stats()
        pass

    async def _database_cleanup_service(self):
        """Periodic database cleanup service to enforce retention policies"""
        while self.is_running:
            try:
                await self._cleanup_old_data()
                # Run cleanup once every 24 hours
                await asyncio.sleep(24 * 3600)
            except Exception as e:
                logger.error(f"Database cleanup error: {e}")
                # On error, wait 1 hour before trying again
                await asyncio.sleep(3600)
    
    async def _cleanup_old_data(self):
        """Clean up old data based on retention policy"""
        # Get retention policy from config
        retention_days = self.config.get('database', {}).get('retention_days', 90)
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        logger.info(f"Starting database cleanup - removing data older than {retention_days} days (before {cutoff_date})")
        
        async with AsyncSessionLocal() as session:
            try:
                # Clean up old connectivity tests
                connectivity_delete = delete(ConnectivityTest).where(
                    ConnectivityTest.timestamp < cutoff_date
                )
                connectivity_result = await session.execute(connectivity_delete)
                connectivity_deleted = connectivity_result.rowcount
                
                # Clean up old speed tests
                speed_delete = delete(SpeedTest).where(
                    SpeedTest.timestamp < cutoff_date
                )
                speed_result = await session.execute(speed_delete)
                speed_deleted = speed_result.rowcount
                
                # Clean up old resolved outage events
                outage_delete = delete(OutageEvent).where(
                    and_(
                        OutageEvent.start_time < cutoff_date,
                        OutageEvent.is_resolved == True
                    )
                )
                outage_result = await session.execute(outage_delete)
                outage_deleted = outage_result.rowcount
                
                # Clean up old monitoring stats
                stats_delete = delete(MonitoringStats).where(
                    MonitoringStats.date < cutoff_date
                )
                stats_result = await session.execute(stats_delete)
                stats_deleted = stats_result.rowcount
                
                await session.commit()
                
                total_deleted = connectivity_deleted + speed_deleted + outage_deleted + stats_deleted
                
                if total_deleted > 0:
                    logger.info(f"Database cleanup completed: deleted {connectivity_deleted} connectivity tests, "
                              f"{speed_deleted} speed tests, {outage_deleted} outage events, "
                              f"{stats_deleted} monitoring stats (total: {total_deleted} records)")
                else:
                    logger.info("Database cleanup completed: no old records found to delete")
                    
            except Exception as e:
                await session.rollback()
                logger.error(f"Database cleanup failed: {e}")
                raise