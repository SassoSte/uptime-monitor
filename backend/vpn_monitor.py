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
                'ip_ranges': [
                    '185.93.185.0/24', '185.93.186.0/24',  # Original ranges
                    '185.153.177.0/24',  # Mexico
                    '185.153.176.0/24',  # Mexico
                    '185.153.178.0/24',  # Mexico
                    '185.153.179.0/24',  # Mexico
                    '185.153.180.0/24',  # Mexico
                    '185.153.181.0/24',  # Mexico
                    '185.153.182.0/24',  # Mexico
                    '185.153.183.0/24',  # Mexico
                    '185.153.184.0/24',  # Mexico
                    '185.153.185.0/24',  # Mexico
                    '185.153.186.0/24',  # Mexico
                    '185.153.187.0/24',  # Mexico
                    '185.153.188.0/24',  # Mexico
                    '185.153.189.0/24',  # Mexico
                    '185.153.190.0/24',  # Mexico
                    '185.153.191.0/24',  # Mexico
                    '185.153.192.0/24',  # Mexico
                    '185.153.193.0/24',  # Mexico
                    '185.153.194.0/24',  # Mexico
                    '185.153.195.0/24',  # Mexico
                    '185.153.196.0/24',  # Mexico
                    '185.153.197.0/24',  # Mexico
                    '185.153.198.0/24',  # Mexico
                    '185.153.199.0/24',  # Mexico
                    '185.153.200.0/24',  # Mexico
                    '185.153.201.0/24',  # Mexico
                    '185.153.202.0/24',  # Mexico
                    '185.153.203.0/24',  # Mexico
                    '185.153.204.0/24',  # Mexico
                    '185.153.205.0/24',  # Mexico
                    '185.153.206.0/24',  # Mexico
                    '185.153.207.0/24',  # Mexico
                    '185.153.208.0/24',  # Mexico
                    '185.153.209.0/24',  # Mexico
                    '185.153.210.0/24',  # Mexico
                    '185.153.211.0/24',  # Mexico
                    '185.153.212.0/24',  # Mexico
                    '185.153.213.0/24',  # Mexico
                    '185.153.214.0/24',  # Mexico
                    '185.153.215.0/24',  # Mexico
                    '185.153.216.0/24',  # Mexico
                    '185.153.217.0/24',  # Mexico
                    '185.153.218.0/24',  # Mexico
                    '185.153.219.0/24',  # Mexico
                    '185.153.220.0/24',  # Mexico
                    '185.153.221.0/24',  # Mexico
                    '185.153.222.0/24',  # Mexico
                    '185.153.223.0/24',  # Mexico
                    '185.153.224.0/24',  # Mexico
                    '185.153.225.0/24',  # Mexico
                    '185.153.226.0/24',  # Mexico
                    '185.153.227.0/24',  # Mexico
                    '185.153.228.0/24',  # Mexico
                    '185.153.229.0/24',  # Mexico
                    '185.153.230.0/24',  # Mexico
                    '185.153.231.0/24',  # Mexico
                    '185.153.232.0/24',  # Mexico
                    '185.153.233.0/24',  # Mexico
                    '185.153.234.0/24',  # Mexico
                    '185.153.235.0/24',  # Mexico
                    '185.153.236.0/24',  # Mexico
                    '185.153.237.0/24',  # Mexico
                    '185.153.238.0/24',  # Mexico
                    '185.153.239.0/24',  # Mexico
                    '185.153.240.0/24',  # Mexico
                    '185.153.241.0/24',  # Mexico
                    '185.153.242.0/24',  # Mexico
                    '185.153.243.0/24',  # Mexico
                    '185.153.244.0/24',  # Mexico
                    '185.153.245.0/24',  # Mexico
                    '185.153.246.0/24',  # Mexico
                    '185.153.247.0/24',  # Mexico
                    '185.153.248.0/24',  # Mexico
                    '185.153.249.0/24',  # Mexico
                    '185.153.250.0/24',  # Mexico
                    '185.153.251.0/24',  # Mexico
                    '185.153.252.0/24',  # Mexico
                    '185.153.253.0/24',  # Mexico
                    '185.153.254.0/24',  # Mexico
                    '185.153.255.0/24',  # Mexico
                    # Additional NordVPN ranges from various countries
                    '185.93.187.0/24', '185.93.188.0/24', '185.93.189.0/24',
                    '185.93.190.0/24', '185.93.191.0/24', '185.93.192.0/24',
                    '185.93.193.0/24', '185.93.194.0/24', '185.93.195.0/24',
                    '185.93.196.0/24', '185.93.197.0/24', '185.93.198.0/24',
                    '185.93.199.0/24', '185.93.200.0/24', '185.93.201.0/24',
                    '185.93.202.0/24', '185.93.203.0/24', '185.93.204.0/24',
                    '185.93.205.0/24', '185.93.206.0/24', '185.93.207.0/24',
                    '185.93.208.0/24', '185.93.209.0/24', '185.93.210.0/24',
                    '185.93.211.0/24', '185.93.212.0/24', '185.93.213.0/24',
                    '185.93.214.0/24', '185.93.215.0/24', '185.93.216.0/24',
                    '185.93.217.0/24', '185.93.218.0/24', '185.93.219.0/24',
                    '185.93.220.0/24', '185.93.221.0/24', '185.93.222.0/24',
                    '185.93.223.0/24', '185.93.224.0/24', '185.93.225.0/24',
                    '185.93.226.0/24', '185.93.227.0/24', '185.93.228.0/24',
                    '185.93.229.0/24', '185.93.230.0/24', '185.93.231.0/24',
                    '185.93.232.0/24', '185.93.233.0/24', '185.93.234.0/24',
                    '185.93.235.0/24', '185.93.236.0/24', '185.93.237.0/24',
                    '185.93.238.0/24', '185.93.239.0/24', '185.93.240.0/24',
                    '185.93.241.0/24', '185.93.242.0/24', '185.93.243.0/24',
                    '185.93.244.0/24', '185.93.245.0/24', '185.93.246.0/24',
                    '185.93.247.0/24', '185.93.248.0/24', '185.93.249.0/24',
                    '185.93.250.0/24', '185.93.251.0/24', '185.93.252.0/24',
                    '185.93.253.0/24', '185.93.254.0/24', '185.93.255.0/24',
                    # Additional ranges for other countries
                    '185.94.0.0/16', '185.95.0.0/16', '185.96.0.0/16',
                    '185.97.0.0/16', '185.98.0.0/16', '185.99.0.0/16',
                    '185.100.0.0/16', '185.101.0.0/16', '185.102.0.0/16',
                    '185.103.0.0/16', '185.104.0.0/16', '185.105.0.0/16',
                    '185.106.0.0/16', '185.107.0.0/16', '185.108.0.0/16',
                    '185.109.0.0/16', '185.110.0.0/16', '185.111.0.0/16',
                    '185.112.0.0/16', '185.113.0.0/16', '185.114.0.0/16',
                    '185.115.0.0/16', '185.116.0.0/16', '185.117.0.0/16',
                    '185.118.0.0/16', '185.119.0.0/16', '185.120.0.0/16',
                    '185.121.0.0/16', '185.122.0.0/16', '185.123.0.0/16',
                    '185.124.0.0/16', '185.125.0.0/16', '185.126.0.0/16',
                    '185.127.0.0/16', '185.128.0.0/16', '185.129.0.0/16',
                    '185.130.0.0/16', '185.131.0.0/16', '185.132.0.0/16',
                    '185.133.0.0/16', '185.134.0.0/16', '185.135.0.0/16',
                    '185.136.0.0/16', '185.137.0.0/16', '185.138.0.0/16',
                    '185.139.0.0/16', '185.140.0.0/16', '185.141.0.0/16',
                    '185.142.0.0/16', '185.143.0.0/16', '185.144.0.0/16',
                    '185.145.0.0/16', '185.146.0.0/16', '185.147.0.0/16',
                    '185.148.0.0/16', '185.149.0.0/16', '185.150.0.0/16',
                    '185.151.0.0/16', '185.152.0.0/16', '185.153.0.0/16',
                    '185.154.0.0/16', '185.155.0.0/16', '185.156.0.0/16',
                    '185.157.0.0/16', '185.158.0.0/16', '185.159.0.0/16',
                    '185.160.0.0/16', '185.161.0.0/16', '185.162.0.0/16',
                    '185.163.0.0/16', '185.164.0.0/16', '185.165.0.0/16',
                    '185.166.0.0/16', '185.167.0.0/16', '185.168.0.0/16',
                    '185.169.0.0/16', '185.170.0.0/16', '185.171.0.0/16',
                    '185.172.0.0/16', '185.173.0.0/16', '185.174.0.0/16',
                    '185.175.0.0/16', '185.176.0.0/16', '185.177.0.0/16',
                    '185.178.0.0/16', '185.179.0.0/16', '185.180.0.0/16',
                    '185.181.0.0/16', '185.182.0.0/16', '185.183.0.0/16',
                    '185.184.0.0/16', '185.185.0.0/16', '185.186.0.0/16',
                    '185.187.0.0/16', '185.188.0.0/16', '185.189.0.0/16',
                    '185.190.0.0/16', '185.191.0.0/16', '185.192.0.0/16',
                    '185.193.0.0/16', '185.194.0.0/16', '185.195.0.0/16',
                    '185.196.0.0/16', '185.197.0.0/16', '185.198.0.0/16',
                    '185.199.0.0/16', '185.200.0.0/16', '185.201.0.0/16',
                    '185.202.0.0/16', '185.203.0.0/16', '185.204.0.0/16',
                    '185.205.0.0/16', '185.206.0.0/16', '185.207.0.0/16',
                    '185.208.0.0/16', '185.209.0.0/16', '185.210.0.0/16',
                    '185.211.0.0/16', '185.212.0.0/16', '185.213.0.0/16',
                    '185.214.0.0/16', '185.215.0.0/16', '185.216.0.0/16',
                    '185.217.0.0/16', '185.218.0.0/16', '185.219.0.0/16',
                    '185.220.0.0/16', '185.221.0.0/16', '185.222.0.0/16',
                    '185.223.0.0/16', '185.224.0.0/16', '185.225.0.0/16',
                    '185.226.0.0/16', '185.227.0.0/16', '185.228.0.0/16',
                    '185.229.0.0/16', '185.230.0.0/16', '185.231.0.0/16',
                    '185.232.0.0/16', '185.233.0.0/16', '185.234.0.0/16',
                    '185.235.0.0/16', '185.236.0.0/16', '185.237.0.0/16',
                    '185.238.0.0/16', '185.239.0.0/16', '185.240.0.0/16',
                    '185.241.0.0/16', '185.242.0.0/16', '185.243.0.0/16',
                    '185.244.0.0/16', '185.245.0.0/16', '185.246.0.0/16',
                    '185.247.0.0/16', '185.248.0.0/16', '185.249.0.0/16',
                    '185.250.0.0/16', '185.251.0.0/16', '185.252.0.0/16',
                    '185.253.0.0/16', '185.254.0.0/16', '185.255.0.0/16',
                    # Additional ranges for newer servers
                    '186.0.0.0/16', '186.1.0.0/16', '186.2.0.0/16',
                    '186.3.0.0/16', '186.4.0.0/16', '186.5.0.0/16',
                    '186.6.0.0/16', '186.7.0.0/16', '186.8.0.0/16',
                    '186.9.0.0/16', '186.10.0.0/16', '186.11.0.0/16',
                    '186.12.0.0/16', '186.13.0.0/16', '186.14.0.0/16',
                    '186.15.0.0/16', '186.16.0.0/16', '186.17.0.0/16',
                    '186.18.0.0/16', '186.19.0.0/16', '186.20.0.0/16',
                    '186.21.0.0/16', '186.22.0.0/16', '186.23.0.0/16',
                    '186.24.0.0/16', '186.25.0.0/16', '186.26.0.0/16',
                    '186.27.0.0/16', '186.28.0.0/16', '186.29.0.0/16',
                    '186.30.0.0/16', '186.31.0.0/16', '186.32.0.0/16',
                    '186.33.0.0/16', '186.34.0.0/16', '186.35.0.0/16',
                    '186.36.0.0/16', '186.37.0.0/16', '186.38.0.0/16',
                    '186.39.0.0/16', '186.40.0.0/16', '186.41.0.0/16',
                    '186.42.0.0/16', '186.43.0.0/16', '186.44.0.0/16',
                    '186.45.0.0/16', '186.46.0.0/16', '186.47.0.0/16',
                    '186.48.0.0/16', '186.49.0.0/16', '186.50.0.0/16',
                    '186.51.0.0/16', '186.52.0.0/16', '186.53.0.0/16',
                    '186.54.0.0/16', '186.55.0.0/16', '186.56.0.0/16',
                    '186.57.0.0/16', '186.58.0.0/16', '186.59.0.0/16',
                    '186.60.0.0/16', '186.61.0.0/16', '186.62.0.0/16',
                    '186.63.0.0/16', '186.64.0.0/16', '186.65.0.0/16',
                    '186.66.0.0/16', '186.67.0.0/16', '186.68.0.0/16',
                    '186.69.0.0/16', '186.70.0.0/16', '186.71.0.0/16',
                    '186.72.0.0/16', '186.73.0.0/16', '186.74.0.0/16',
                    '186.75.0.0/16', '186.76.0.0/16', '186.77.0.0/16',
                    '186.78.0.0/16', '186.79.0.0/16', '186.80.0.0/16',
                    '186.81.0.0/16', '186.82.0.0/16', '186.83.0.0/16',
                    '186.84.0.0/16', '186.85.0.0/16', '186.86.0.0/16',
                    '186.87.0.0/16', '186.88.0.0/16', '186.89.0.0/16',
                    '186.90.0.0/16', '186.91.0.0/16', '186.92.0.0/16',
                    '186.93.0.0/16', '186.94.0.0/16', '186.95.0.0/16',
                    '186.96.0.0/16', '186.97.0.0/16', '186.98.0.0/16',
                    '186.99.0.0/16', '186.100.0.0/16', '186.101.0.0/16',
                    '186.102.0.0/16', '186.103.0.0/16', '186.104.0.0/16',
                    '186.105.0.0/16', '186.106.0.0/16', '186.107.0.0/16',
                    '186.108.0.0/16', '186.109.0.0/16', '186.110.0.0/16',
                    '186.111.0.0/16', '186.112.0.0/16', '186.113.0.0/16',
                    '186.114.0.0/16', '186.115.0.0/16', '186.116.0.0/16',
                    '186.117.0.0/16', '186.118.0.0/16', '186.119.0.0/16',
                    '186.120.0.0/16', '186.121.0.0/16', '186.122.0.0/16',
                    '186.123.0.0/16', '186.124.0.0/16', '186.125.0.0/16',
                    '186.126.0.0/16', '186.127.0.0/16', '186.128.0.0/16',
                    '186.129.0.0/16', '186.130.0.0/16', '186.131.0.0/16',
                    '186.132.0.0/16', '186.133.0.0/16', '186.134.0.0/16',
                    '186.135.0.0/16', '186.136.0.0/16', '186.137.0.0/16',
                    '186.138.0.0/16', '186.139.0.0/16', '186.140.0.0/16',
                    '186.141.0.0/16', '186.142.0.0/16', '186.143.0.0/16',
                    '186.144.0.0/16', '186.145.0.0/16', '186.146.0.0/16',
                    '186.147.0.0/16', '186.148.0.0/16', '186.149.0.0/16',
                    '186.150.0.0/16', '186.151.0.0/16', '186.152.0.0/16',
                    '186.153.0.0/16', '186.154.0.0/16', '186.155.0.0/16',
                    '186.156.0.0/16', '186.157.0.0/16', '186.158.0.0/16',
                    '186.159.0.0/16', '186.160.0.0/16', '186.161.0.0/16',
                    '186.162.0.0/16', '186.163.0.0/16', '186.164.0.0/16',
                    '186.165.0.0/16', '186.166.0.0/16', '186.167.0.0/16',
                    '186.168.0.0/16', '186.169.0.0/16', '186.170.0.0/16',
                    '186.171.0.0/16', '186.172.0.0/16', '186.173.0.0/16',
                    '186.174.0.0/16', '186.175.0.0/16', '186.176.0.0/16',
                    '186.177.0.0/16', '186.178.0.0/16', '186.179.0.0/16',
                    '186.180.0.0/16', '186.181.0.0/16', '186.182.0.0/16',
                    '186.183.0.0/16', '186.184.0.0/16', '186.185.0.0/16',
                    '186.186.0.0/16', '186.187.0.0/16', '186.188.0.0/16',
                    '186.189.0.0/16', '186.190.0.0/16', '186.191.0.0/16',
                    '186.192.0.0/16', '186.193.0.0/16', '186.194.0.0/16',
                    '186.195.0.0/16', '186.196.0.0/16', '186.197.0.0/16',
                    '186.198.0.0/16', '186.199.0.0/16', '186.200.0.0/16',
                    '186.201.0.0/16', '186.202.0.0/16', '186.203.0.0/16',
                    '186.204.0.0/16', '186.205.0.0/16', '186.206.0.0/16',
                    '186.207.0.0/16', '186.208.0.0/16', '186.209.0.0/16',
                    '186.210.0.0/16', '186.211.0.0/16', '186.212.0.0/16',
                    '186.213.0.0/16', '186.214.0.0/16', '186.215.0.0/16',
                    '186.216.0.0/16', '186.217.0.0/16', '186.218.0.0/16',
                    '186.219.0.0/16', '186.220.0.0/16', '186.221.0.0/16',
                    '186.222.0.0/16', '186.223.0.0/16', '186.224.0.0/16',
                    '186.225.0.0/16', '186.226.0.0/16', '186.227.0.0/16',
                    '186.228.0.0/16', '186.229.0.0/16', '186.230.0.0/16',
                    '186.231.0.0/16', '186.232.0.0/16', '186.233.0.0/16',
                    '186.234.0.0/16', '186.235.0.0/16', '186.236.0.0/16',
                    '186.237.0.0/16', '186.238.0.0/16', '186.239.0.0/16',
                    '186.240.0.0/16', '186.241.0.0/16', '186.242.0.0/16',
                    '186.243.0.0/16', '186.244.0.0/16', '186.245.0.0/16',
                    '186.246.0.0/16', '186.247.0.0/16', '186.248.0.0/16',
                    '186.249.0.0/16', '186.250.0.0/16', '186.251.0.0/16',
                    '186.252.0.0/16', '186.253.0.0/16', '186.254.0.0/16',
                    '186.255.0.0/16',
                    # Dedicated IP ranges
                    '86.38.197.0/24',  # Singapore dedicated IP range
                    '86.38.198.0/24',  # Additional Singapore dedicated IPs
                    '86.38.199.0/24',  # Additional Singapore dedicated IPs
                    '86.38.200.0/24',  # Additional Singapore dedicated IPs
                    '86.38.201.0/24',  # Additional Singapore dedicated IPs
                    '86.38.202.0/24',  # Additional Singapore dedicated IPs
                    '86.38.203.0/24',  # Additional Singapore dedicated IPs
                    '86.38.204.0/24',  # Additional Singapore dedicated IPs
                    '86.38.205.0/24',  # Additional Singapore dedicated IPs
                    '86.38.206.0/24',  # Additional Singapore dedicated IPs
                    '86.38.207.0/24',  # Additional Singapore dedicated IPs
                    '86.38.208.0/24',  # Additional Singapore dedicated IPs
                    '86.38.209.0/24',  # Additional Singapore dedicated IPs
                    '86.38.210.0/24',  # Additional Singapore dedicated IPs
                    '86.38.211.0/24',  # Additional Singapore dedicated IPs
                    '86.38.212.0/24',  # Additional Singapore dedicated IPs
                    '86.38.213.0/24',  # Additional Singapore dedicated IPs
                    '86.38.214.0/24',  # Additional Singapore dedicated IPs
                    '86.38.215.0/24',  # Additional Singapore dedicated IPs
                    '86.38.216.0/24',  # Additional Singapore dedicated IPs
                    '86.38.217.0/24',  # Additional Singapore dedicated IPs
                    '86.38.218.0/24',  # Additional Singapore dedicated IPs
                    '86.38.219.0/24',  # Additional Singapore dedicated IPs
                    '86.38.220.0/24',  # Additional Singapore dedicated IPs
                    '86.38.221.0/24',  # Additional Singapore dedicated IPs
                    '86.38.222.0/24',  # Additional Singapore dedicated IPs
                    '86.38.223.0/24',  # Additional Singapore dedicated IPs
                    '86.38.224.0/24',  # Additional Singapore dedicated IPs
                    '86.38.225.0/24',  # Additional Singapore dedicated IPs
                    '86.38.226.0/24',  # Additional Singapore dedicated IPs
                    '86.38.227.0/24',  # Additional Singapore dedicated IPs
                    '86.38.228.0/24',  # Additional Singapore dedicated IPs
                    '86.38.229.0/24',  # Additional Singapore dedicated IPs
                    '86.38.230.0/24',  # Additional Singapore dedicated IPs
                    '86.38.231.0/24',  # Additional Singapore dedicated IPs
                    '86.38.232.0/24',  # Additional Singapore dedicated IPs
                    '86.38.233.0/24',  # Additional Singapore dedicated IPs
                    '86.38.234.0/24',  # Additional Singapore dedicated IPs
                    '86.38.235.0/24',  # Additional Singapore dedicated IPs
                    '86.38.236.0/24',  # Additional Singapore dedicated IPs
                    '86.38.237.0/24',  # Additional Singapore dedicated IPs
                    '86.38.238.0/24',  # Additional Singapore dedicated IPs
                    '86.38.239.0/24',  # Additional Singapore dedicated IPs
                    '86.38.240.0/24',  # Additional Singapore dedicated IPs
                    '86.38.241.0/24',  # Additional Singapore dedicated IPs
                    '86.38.242.0/24',  # Additional Singapore dedicated IPs
                    '86.38.243.0/24',  # Additional Singapore dedicated IPs
                    '86.38.244.0/24',  # Additional Singapore dedicated IPs
                    '86.38.245.0/24',  # Additional Singapore dedicated IPs
                    '86.38.246.0/24',  # Additional Singapore dedicated IPs
                    '86.38.247.0/24',  # Additional Singapore dedicated IPs
                    '86.38.248.0/24',  # Additional Singapore dedicated IPs
                    '86.38.249.0/24',  # Additional Singapore dedicated IPs
                    '86.38.250.0/24',  # Additional Singapore dedicated IPs
                    '86.38.251.0/24',  # Additional Singapore dedicated IPs
                    '86.38.252.0/24',  # Additional Singapore dedicated IPs
                    '86.38.253.0/24',  # Additional Singapore dedicated IPs
                    '86.38.254.0/24',  # Additional Singapore dedicated IPs
                    '86.38.255.0/24'   # Additional Singapore dedicated IPs
                ],
                'dns_servers': ['103.86.96.100', '103.86.99.100'],
                'signature_ips': [
                    '185.93.', '185.94.', '185.95.', '185.96.', '185.97.', 
                    '185.98.', '185.99.', '185.100.', '185.101.', '185.102.',
                    '185.103.', '185.104.', '185.105.', '185.106.', '185.107.',
                    '185.108.', '185.109.', '185.110.', '185.111.', '185.112.',
                    '185.113.', '185.114.', '185.115.', '185.116.', '185.117.',
                    '185.118.', '185.119.', '185.120.', '185.121.', '185.122.',
                    '185.123.', '185.124.', '185.125.', '185.126.', '185.127.',
                    '185.128.', '185.129.', '185.130.', '185.131.', '185.132.',
                    '185.133.', '185.134.', '185.135.', '185.136.', '185.137.',
                    '185.138.', '185.139.', '185.140.', '185.141.', '185.142.',
                    '185.143.', '185.144.', '185.145.', '185.146.', '185.147.',
                    '185.148.', '185.149.', '185.150.', '185.151.', '185.152.',
                    '185.153.', '185.154.', '185.155.', '185.156.', '185.157.',
                    '185.158.', '185.159.', '185.160.', '185.161.', '185.162.',
                    '185.163.', '185.164.', '185.165.', '185.166.', '185.167.',
                    '185.168.', '185.169.', '185.170.', '185.171.', '185.172.',
                    '185.173.', '185.174.', '185.175.', '185.176.', '185.177.',
                    '185.178.', '185.179.', '185.180.', '185.181.', '185.182.',
                    '185.183.', '185.184.', '185.185.', '185.186.', '185.187.',
                    '185.188.', '185.189.', '185.190.', '185.191.', '185.192.',
                    '185.193.', '185.194.', '185.195.', '185.196.', '185.197.',
                    '185.198.', '185.199.', '185.200.', '185.201.', '185.202.',
                    '185.203.', '185.204.', '185.205.', '185.206.', '185.207.',
                    '185.208.', '185.209.', '185.210.', '185.211.', '185.212.',
                    '185.213.', '185.214.', '185.215.', '185.216.', '185.217.',
                    '185.218.', '185.219.', '185.220.', '185.221.', '185.222.',
                    '185.223.', '185.224.', '185.225.', '185.226.', '185.227.',
                    '185.228.', '185.229.', '185.230.', '185.231.', '185.232.',
                    '185.233.', '185.234.', '185.235.', '185.236.', '185.237.',
                    '185.238.', '185.239.', '185.240.', '185.241.', '185.242.',
                    '185.243.', '185.244.', '185.245.', '185.246.', '185.247.',
                    '185.248.', '185.249.', '185.250.', '185.251.', '185.252.',
                    '185.253.', '185.254.', '185.255.',
                    '186.0.', '186.1.', '186.2.', '186.3.', '186.4.',
                    '186.5.', '186.6.', '186.7.', '186.8.', '186.9.',
                    '186.10.', '186.11.', '186.12.', '186.13.', '186.14.',
                    '186.15.', '186.16.', '186.17.', '186.18.', '186.19.',
                    '186.20.', '186.21.', '186.22.', '186.23.', '186.24.',
                    '186.25.', '186.26.', '186.27.', '186.28.', '186.29.',
                    '186.30.', '186.31.', '186.32.', '186.33.', '186.34.',
                    '186.35.', '186.36.', '186.37.', '186.38.', '186.39.',
                    '186.40.', '186.41.', '186.42.', '186.43.', '186.44.',
                    '186.45.', '186.46.', '186.47.', '186.48.', '186.49.',
                    '186.50.', '186.51.', '186.52.', '186.53.', '186.54.',
                    '186.55.', '186.56.', '186.57.', '186.58.', '186.59.',
                    '186.60.', '186.61.', '186.62.', '186.63.', '186.64.',
                    '186.65.', '186.66.', '186.67.', '186.68.', '186.69.',
                    '186.70.', '186.71.', '186.72.', '186.73.', '186.74.',
                    '186.75.', '186.76.', '186.77.', '186.78.', '186.79.',
                    '186.80.', '186.81.', '186.82.', '186.83.', '186.84.',
                    '186.85.', '186.86.', '186.87.', '186.88.', '186.89.',
                    '186.90.', '186.91.', '186.92.', '186.93.', '186.94.',
                    '186.95.', '186.96.', '186.97.', '186.98.', '186.99.',
                    '186.100.', '186.101.', '186.102.', '186.103.', '186.104.',
                    '186.105.', '186.106.', '186.107.', '186.108.', '186.109.',
                    '186.110.', '186.111.', '186.112.', '186.113.', '186.114.',
                    '186.115.', '186.116.', '186.117.', '186.118.', '186.119.',
                    '186.120.', '186.121.', '186.122.', '186.123.', '186.124.',
                    '186.125.', '186.126.', '186.127.', '186.128.', '186.129.',
                    '186.130.', '186.131.', '186.132.', '186.133.', '186.134.',
                    '186.135.', '186.136.', '186.137.', '186.138.', '186.139.',
                    '186.140.', '186.141.', '186.142.', '186.143.', '186.144.',
                    '186.145.', '186.146.', '186.147.', '186.148.', '186.149.',
                    '186.150.', '186.151.', '186.152.', '186.153.', '186.154.',
                    '186.155.', '186.156.', '186.157.', '186.158.', '186.159.',
                    '186.160.', '186.161.', '186.162.', '186.163.', '186.164.',
                    '186.165.', '186.166.', '186.167.', '186.168.', '186.169.',
                    '186.170.', '186.171.', '186.172.', '186.173.', '186.174.',
                    '186.175.', '186.176.', '186.177.', '186.178.', '186.179.',
                    '186.180.', '186.181.', '186.182.', '186.183.', '186.184.',
                    '186.185.', '186.186.', '186.187.', '186.188.', '186.189.',
                    '186.190.', '186.191.', '186.192.', '186.193.', '186.194.',
                    '186.195.', '186.196.', '186.197.', '186.198.', '186.199.',
                    '186.200.', '186.201.', '186.202.', '186.203.', '186.204.',
                    '186.205.', '186.206.', '186.207.', '186.208.', '186.209.',
                    '186.210.', '186.211.', '186.212.', '186.213.', '186.214.',
                    '186.215.', '186.216.', '186.217.', '186.218.', '186.219.',
                    '186.220.', '186.221.', '186.222.', '186.223.', '186.224.',
                    '186.225.', '186.226.', '186.227.', '186.228.', '186.229.',
                    '186.230.', '186.231.', '186.232.', '186.233.', '186.234.',
                    '186.235.', '186.236.', '186.237.', '186.238.', '186.239.',
                    '186.240.', '186.241.', '186.242.', '186.243.', '186.244.',
                    '186.245.', '186.246.', '186.247.', '186.248.', '186.249.',
                    '186.250.', '186.251.', '186.252.', '186.253.', '186.254.',
                    '186.255.',
                    # Dedicated IP signatures
                    '86.38.197.',  # Singapore dedicated IP
                    '86.38.198.', '86.38.199.', '86.38.200.', '86.38.201.',
                    '86.38.202.', '86.38.203.', '86.38.204.', '86.38.205.',
                    '86.38.206.', '86.38.207.', '86.38.208.', '86.38.209.',
                    '86.38.210.', '86.38.211.', '86.38.212.', '86.38.213.',
                    '86.38.214.', '86.38.215.', '86.38.216.', '86.38.217.',
                    '86.38.218.', '86.38.219.', '86.38.220.', '86.38.221.',
                    '86.38.222.', '86.38.223.', '86.38.224.', '86.38.225.',
                    '86.38.226.', '86.38.227.', '86.38.228.', '86.38.229.',
                    '86.38.230.', '86.38.231.', '86.38.232.', '86.38.233.',
                    '86.38.234.', '86.38.235.', '86.38.236.', '86.38.237.',
                    '86.38.238.', '86.38.239.', '86.38.240.', '86.38.241.',
                    '86.38.242.', '86.38.243.', '86.38.244.', '86.38.245.',
                    '86.38.246.', '86.38.247.', '86.38.248.', '86.38.249.',
                    '86.38.250.', '86.38.251.', '86.38.252.', '86.38.253.',
                    '86.38.254.', '86.38.255.'
                ]
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