#!/usr/bin/env python3
"""
VPN Detection and Monitoring System
Detects VPN usage and provides insights into its impact on network performance
"""

import asyncio
import time
import json
import subprocess
import socket
import os
import platform
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import httpx
import logging
import pytz
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class VPNStatus:
    """VPN status information"""
    is_active: bool
    provider: Optional[str]
    server_location: Optional[str]
    public_ip: Optional[str]
    interface_name: Optional[str]
    connection_time: Optional[datetime]
    detection_method: str
    confidence: float  # 0.0 to 1.0

class VPNMonitor:
    """VPN detection and monitoring service"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.vpn_config = config.get('vpn_monitoring', {})
        self.is_running = False
        self.current_vpn_status: Optional[VPNStatus] = None
        self.vpn_history: List[Dict] = []
        self.arizona_tz = pytz.timezone('America/Phoenix')
        
        # VPN provider signatures
        self.vpn_providers = {
            'nordvpn': {
                'processes': ['nordvpn', 'nordvpnd'],
                'interfaces': ['nordlynx', 'tun0', 'tun1'],
                'ip_ranges': ['185.93.185.0/24', '185.93.186.0/24'],
                'dns_servers': ['103.86.96.100', '103.86.99.100'],
                'signature_ips': ['185.93.185.', '185.93.186.']
            },
            'expressvpn': {
                'processes': ['expressvpn', 'expressvpnd'],
                'interfaces': ['tun0', 'tun1'],
                'ip_ranges': ['45.67.0.0/16'],
                'dns_servers': ['10.0.0.1'],
                'signature_ips': ['45.67.']
            },
            'protonvpn': {
                'processes': ['protonvpn', 'protonvpnd'],
                'interfaces': ['proton0', 'tun0'],
                'ip_ranges': ['37.19.0.0/16'],
                'dns_servers': ['10.2.0.1'],
                'signature_ips': ['37.19.']
            },
            'surfshark': {
                'processes': ['surfshark', 'surfsharkd'],
                'interfaces': ['surfshark', 'tun0'],
                'ip_ranges': ['185.199.0.0/16'],
                'dns_servers': ['162.252.172.57'],
                'signature_ips': ['185.199.']
            }
        }
    
    def get_arizona_time(self) -> datetime:
        """Get current time in Arizona timezone"""
        utc_now = datetime.utcnow()
        return utc_now.replace(tzinfo=pytz.UTC).astimezone(self.arizona_tz)
    
    async def start_vpn_monitoring(self):
        """Start VPN monitoring service"""
        self.is_running = True
        logger.info("Starting VPN monitoring service...")
        
        while self.is_running:
            try:
                # Detect VPN status
                vpn_status = await self.detect_vpn_status()
                
                # Update current status
                if vpn_status != self.current_vpn_status:
                    await self._handle_vpn_status_change(vpn_status)
                    self.current_vpn_status = vpn_status
                
                # Log VPN status
                await self._log_vpn_status(vpn_status)
                
                # Wait for next check
                interval = self.vpn_config.get('check_interval_seconds', 30)
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"VPN monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def detect_vpn_status(self) -> VPNStatus:
        """Comprehensive VPN detection using multiple methods"""
        detection_results = []
        
        # Method 1: Process detection
        process_result = await self._detect_vpn_processes()
        detection_results.append(process_result)
        
        # Method 2: Network interface detection
        interface_result = await self._detect_vpn_interfaces()
        detection_results.append(interface_result)
        
        # Method 3: IP address analysis
        ip_result = await self._detect_vpn_by_ip()
        detection_results.append(ip_result)
        
        # Method 4: DNS server analysis
        dns_result = await self._detect_vpn_by_dns()
        detection_results.append(dns_result)
        
        # Method 5: Network routing analysis
        routing_result = await self._detect_vpn_by_routing()
        detection_results.append(routing_result)
        
        # Combine results
        return self._combine_detection_results(detection_results)
    
    async def _detect_vpn_processes(self) -> Dict:
        """Detect VPN processes running on the system"""
        try:
            if platform.system() == "Darwin":  # macOS
                cmd = ["ps", "aux"]
            else:  # Linux/Unix
                cmd = ["ps", "aux"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                processes = result.stdout.lower()
                
                for provider, signatures in self.vpn_providers.items():
                    for process_name in signatures['processes']:
                        if process_name in processes:
                            return {
                                'method': 'process',
                                'provider': provider,
                                'confidence': 0.9,
                                'details': f"Found {process_name} process"
                            }
            
            return {'method': 'process', 'confidence': 0.0}
            
        except Exception as e:
            logger.error(f"Process detection error: {e}")
            return {'method': 'process', 'confidence': 0.0}
    
    async def _detect_vpn_interfaces(self) -> Dict:
        """Detect VPN network interfaces"""
        try:
            if platform.system() == "Darwin":  # macOS
                cmd = ["ifconfig"]
            else:  # Linux/Unix
                cmd = ["ip", "link", "show"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                interfaces = result.stdout.lower()
                
                # More specific VPN interface detection
                for provider, signatures in self.vpn_providers.items():
                    for interface_name in signatures['interfaces']:
                        if interface_name in interfaces:
                            # Additional validation for macOS: check if it's a real VPN interface
                            if platform.system() == "Darwin" and interface_name.startswith('tun'):
                                # For tun interfaces, check if they have VPN-specific characteristics
                                # Look for VPN-related patterns in the interface details
                                if f"{interface_name}:" in interfaces:
                                    # Check if this interface has VPN-specific IP ranges or characteristics
                                    # For now, we'll be more conservative and require additional evidence
                                    return {
                                        'method': 'interface',
                                        'provider': provider,
                                        'confidence': 0.4,  # Lower confidence for tun interfaces
                                        'details': f"Found {interface_name} interface (needs validation)"
                                    }
                            else:
                                # For non-tun interfaces (like nordlynx), higher confidence
                                return {
                                    'method': 'interface',
                                    'provider': provider,
                                    'confidence': 0.8,
                                    'details': f"Found {interface_name} interface"
                                }
            
            return {'method': 'interface', 'confidence': 0.0}
            
        except Exception as e:
            logger.error(f"Interface detection error: {e}")
            return {'method': 'interface', 'confidence': 0.0}
    
    async def _detect_vpn_by_ip(self) -> Dict:
        """Detect VPN by analyzing public IP address"""
        try:
            # Get public IP
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get('https://httpbin.org/ip')
                if response.status_code == 200:
                    data = response.json()
                    public_ip = data.get('origin', '').split(',')[0].strip()
                    
                    # Check against known VPN IP ranges
                    for provider, signatures in self.vpn_providers.items():
                        for signature_ip in signatures['signature_ips']:
                            if public_ip.startswith(signature_ip):
                                return {
                                    'method': 'ip',
                                    'provider': provider,
                                    'confidence': 0.7,
                                    'details': f"IP {public_ip} matches {provider} signature",
                                    'public_ip': public_ip
                                }
                    
                    return {
                        'method': 'ip',
                        'confidence': 0.3,
                        'details': f"Public IP: {public_ip}",
                        'public_ip': public_ip
                    }
            
            return {'method': 'ip', 'confidence': 0.0}
            
        except Exception as e:
            logger.error(f"IP detection error: {e}")
            return {'method': 'ip', 'confidence': 0.0}
    
    async def _detect_vpn_by_dns(self) -> Dict:
        """Detect VPN by analyzing DNS server configuration"""
        try:
            # Get DNS servers
            if platform.system() == "Darwin":  # macOS
                cmd = ["scutil", "--dns"]
            else:  # Linux/Unix
                cmd = ["cat", "/etc/resolv.conf"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                dns_config = result.stdout.lower()
                
                for provider, signatures in self.vpn_providers.items():
                    for dns_server in signatures['dns_servers']:
                        if dns_server in dns_config:
                            return {
                                'method': 'dns',
                                'provider': provider,
                                'confidence': 0.6,
                                'details': f"DNS server {dns_server} matches {provider}"
                            }
            
            return {'method': 'dns', 'confidence': 0.0}
            
        except Exception as e:
            logger.error(f"DNS detection error: {e}")
            return {'method': 'dns', 'confidence': 0.0}
    
    async def _detect_vpn_by_routing(self) -> Dict:
        """Detect VPN by analyzing network routing"""
        try:
            if platform.system() == "Darwin":  # macOS
                cmd = ["netstat", "-rn"]
            else:  # Linux/Unix
                cmd = ["ip", "route", "show"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                routing_table = result.stdout.lower()
                
                # Look for VPN routing patterns - be more specific
                vpn_patterns = [
                    r'nordlynx',  # NordVPN specific
                    r'proton0',   # ProtonVPN specific
                    r'vpn',       # Generic VPN
                ]
                
                # Be more conservative with tun patterns on macOS
                if platform.system() == "Darwin":
                    # On macOS, tun interfaces are common system interfaces
                    # Only consider them VPN-related if we have other evidence
                    pass
                else:
                    # On Linux, tun interfaces are more likely to be VPN-related
                    vpn_patterns.append(r'tun\d+')
                
                for pattern in vpn_patterns:
                    if re.search(pattern, routing_table):
                        return {
                            'method': 'routing',
                            'confidence': 0.5,
                            'details': f"Found VPN routing pattern: {pattern}"
                        }
            
            return {'method': 'routing', 'confidence': 0.0}
            
        except Exception as e:
            logger.error(f"Routing detection error: {e}")
            return {'method': 'routing', 'confidence': 0.0}
    
    def _combine_detection_results(self, results: List[Dict]) -> VPNStatus:
        """Combine multiple detection results into a single VPN status"""
        # Find the highest confidence result
        best_result = max(results, key=lambda x: x.get('confidence', 0))
        
        # Calculate overall confidence
        total_confidence = sum(r.get('confidence', 0) for r in results)
        avg_confidence = total_confidence / len(results)
        
        # Get public IP if available
        public_ip = None
        for result in results:
            if result.get('method') == 'ip' and result.get('public_ip'):
                public_ip = result.get('public_ip')
                break
        
        # IMPROVED DETECTION LOGIC:
        # VPN is only considered active if we have strong evidence
        is_active = False
        provider = None
        
        # Check for strong indicators of active VPN
        strong_indicators = []
        for result in results:
            if result.get('confidence', 0) >= 0.7:  # High confidence
                strong_indicators.append(result)
            elif result.get('method') == 'ip' and result.get('provider'):  # IP matches known VPN
                strong_indicators.append(result)
            elif result.get('method') == 'interface' and result.get('provider'):  # VPN interface found
                strong_indicators.append(result)
        
        # VPN is active if we have strong indicators OR high overall confidence
        if strong_indicators or avg_confidence > 0.6:
            is_active = True
            # Get provider from best strong indicator
            if strong_indicators:
                provider = strong_indicators[0].get('provider')
            elif best_result.get('confidence', 0) > 0.5:
                provider = best_result.get('provider')
        
        # Additional validation: If we have a public IP, check if it's actually a VPN IP
        if public_ip and is_active:
            # Check if the IP actually matches known VPN ranges
            ip_matches_vpn = False
            for result in results:
                if result.get('method') == 'ip' and result.get('provider'):
                    ip_matches_vpn = True
                    break
            
            # If IP doesn't match any known VPN ranges, be more conservative
            if not ip_matches_vpn:
                # Only consider active if we have very strong process/interface evidence
                strong_evidence = any(
                    r.get('confidence', 0) >= 0.8 and r.get('method') in ['process', 'interface']
                    for r in results
                )
                if not strong_evidence:
                    is_active = False
                    provider = None
        
        # FINAL VALIDATION: If we only have process detection but no VPN IP, be very conservative
        if is_active and public_ip:
            # Check if we have strong evidence beyond just process detection
            has_strong_evidence = False
            
            # Look for interface detection with high confidence
            for result in results:
                if (result.get('method') == 'interface' and 
                    result.get('confidence', 0) >= 0.7 and 
                    result.get('provider')):
                    has_strong_evidence = True
                    break
            
            # Look for IP detection that matches VPN ranges
            for result in results:
                if (result.get('method') == 'ip' and 
                    result.get('provider')):
                    has_strong_evidence = True
                    break
            
            # If we only have process detection and no VPN IP, don't consider it active
            if not has_strong_evidence:
                is_active = False
                provider = None
        
        return VPNStatus(
            is_active=is_active,
            provider=provider,
            server_location=None,  # Could be enhanced with IP geolocation
            public_ip=public_ip,
            interface_name=None,
            connection_time=self.current_vpn_status.connection_time if self.current_vpn_status and is_active else self.get_arizona_time(),
            detection_method=best_result.get('method', 'unknown'),
            confidence=avg_confidence
        )
    
    async def _handle_vpn_status_change(self, new_status: VPNStatus):
        """Handle VPN status changes"""
        if new_status.is_active and not (self.current_vpn_status and self.current_vpn_status.is_active):
            # VPN connected
            logger.info(f"VPN connected: {new_status.provider or 'Unknown'}")
            await self._log_vpn_event('connected', new_status)
            
        elif not new_status.is_active and (self.current_vpn_status and self.current_vpn_status.is_active):
            # VPN disconnected
            logger.info(f"VPN disconnected: {self.current_vpn_status.provider or 'Unknown'}")
            await self._log_vpn_event('disconnected', self.current_vpn_status)
    
    async def _log_vpn_status(self, status: VPNStatus):
        """Log current VPN status"""
        # This would save to database in a real implementation
        log_entry = {
            'timestamp': self.get_arizona_time().isoformat(),
            'is_active': status.is_active,
            'provider': status.provider,
            'public_ip': status.public_ip,
            'confidence': status.confidence,
            'detection_method': status.detection_method
        }
        
        self.vpn_history.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.vpn_history) > 1000:
            self.vpn_history = self.vpn_history[-1000:]
    
    async def _log_vpn_event(self, event_type: str, status: VPNStatus):
        """Log VPN connection/disconnection events"""
        event = {
            'timestamp': self.get_arizona_time().isoformat(),
            'event_type': event_type,
            'provider': status.provider,
            'public_ip': status.public_ip,
            'confidence': status.confidence
        }
        
        # This would save to database in a real implementation
        logger.info(f"VPN event: {event}")
    
    def get_current_vpn_status(self) -> Optional[VPNStatus]:
        """Get current VPN status"""
        return self.current_vpn_status
    
    def get_vpn_history(self, hours: int = 24) -> List[Dict]:
        """Get VPN history for the specified hours"""
        cutoff_time = self.get_arizona_time() - timedelta(hours=hours)
        
        return [
            entry for entry in self.vpn_history
            if datetime.fromisoformat(entry['timestamp']) >= cutoff_time
        ]
    
    def get_vpn_usage_stats(self, hours: int = 24) -> Dict:
        """Get VPN usage statistics"""
        history = self.get_vpn_history(hours)
        
        if not history:
            return {
                'total_time_minutes': 0,
                'usage_percentage': 0,
                'connection_count': 0,
                'providers_used': [],
                'avg_confidence': 0
            }
        
        # Calculate usage statistics
        total_entries = len(history)
        vpn_active_entries = sum(1 for entry in history if entry['is_active'])
        usage_percentage = (vpn_active_entries / total_entries) * 100
        
        # Estimate total VPN time (assuming 30-second intervals)
        total_time_minutes = (vpn_active_entries * 30) / 60
        
        # Count unique providers
        providers = set(entry['provider'] for entry in history if entry['provider'])
        
        # Average confidence
        avg_confidence = sum(entry['confidence'] for entry in history) / total_entries
        
        return {
            'total_time_minutes': round(total_time_minutes, 1),
            'usage_percentage': round(usage_percentage, 1),
            'connection_count': len([e for e in history if e.get('event_type') == 'connected']),
            'providers_used': list(providers),
            'avg_confidence': round(avg_confidence, 2)
        }

# Example usage
async def main():
    """Test the VPN monitoring system"""
    config = {
        "vpn_monitoring": {
            "check_interval_seconds": 30,
            "enabled": True
        }
    }
    
    monitor = VPNMonitor(config)
    
    print("🔍 Testing VPN Detection System")
    print("=" * 50)
    
    # Test VPN detection
    status = await monitor.detect_vpn_status()
    
    print(f"VPN Active: {status.is_active}")
    print(f"Provider: {status.provider or 'Unknown'}")
    print(f"Public IP: {status.public_ip or 'Unknown'}")
    print(f"Confidence: {status.confidence:.2f}")
    print(f"Detection Method: {status.detection_method}")
    
    if status.is_active:
        print("✅ VPN detected and active")
    else:
        print("❌ No VPN detected")

if __name__ == "__main__":
    asyncio.run(main()) 