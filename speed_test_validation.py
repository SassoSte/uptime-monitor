#!/usr/bin/env python3
"""
Speed Test Validation Script
Compares our UpTime Monitor speed test results with reliable online services
"""

import asyncio
import time
import json
import subprocess
import requests
from datetime import datetime
import httpx
from typing import Dict, List

class SpeedTestValidator:
    def __init__(self):
        self.results = {}
        
    async def test_our_implementation(self) -> Dict:
        """Test our current HTTP-based speed test implementation"""
        print("🔍 Testing our UpTime Monitor speed test implementation...")
        
        try:
            # Simple speed test using HTTP download (same as our app)
            test_url = "https://httpbin.org/bytes/1048576"  # 1MB file
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(test_url)
                end_time = time.time()
                
                if response.status_code == 200:
                    duration = end_time - start_time
                    file_size_mb = 1.0  # 1MB
                    download_speed = (file_size_mb * 8) / duration  # Convert to Mbps
                    
                    # Estimate upload speed (typically 1/10th of download)
                    upload_speed = download_speed / 10
                    
                    # Simple ping test
                    ping_start = time.time()
                    ping_response = await client.get("https://httpbin.org/delay/0.1")
                    ping_end = time.time()
                    ping_ms = (ping_end - ping_start) * 1000
                    
                    result = {
                        'download_mbps': round(download_speed, 2),
                        'upload_mbps': round(upload_speed, 2),
                        'ping_ms': round(ping_ms, 1),
                        'server': 'httpbin.org',
                        'method': 'HTTP Download Test'
                    }
                    
                    print(f"✅ Our test: {result['download_mbps']} Mbps download, {result['upload_mbps']} Mbps upload, {result['ping_ms']} ms ping")
                    return result
                else:
                    raise Exception(f"HTTP {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Our test failed: {e}")
            return {'error': str(e)}

    def test_speedtest_cli(self) -> Dict:
        """Test using speedtest-cli (if available)"""
        print("🔍 Testing with speedtest-cli...")
        
        try:
            # Try to use speedtest-cli if available
            result = subprocess.run(['speedtest-cli', '--json'], 
                                  capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                speed_result = {
                    'download_mbps': round(data['download'] / 1_000_000, 2),
                    'upload_mbps': round(data['upload'] / 1_000_000, 2),
                    'ping_ms': round(data['ping'], 1),
                    'server': data['server']['sponsor'],
                    'method': 'speedtest-cli'
                }
                print(f"✅ speedtest-cli: {speed_result['download_mbps']} Mbps download, {speed_result['upload_mbps']} Mbps upload, {speed_result['ping_ms']} ms ping")
                return speed_result
            else:
                print(f"❌ speedtest-cli failed: {result.stderr}")
                return {'error': result.stderr}
                
        except FileNotFoundError:
            print("❌ speedtest-cli not installed")
            return {'error': 'speedtest-cli not available'}
        except Exception as e:
            print(f"❌ speedtest-cli error: {e}")
            return {'error': str(e)}

    def test_fast_com(self) -> Dict:
        """Test using fast.com (Netflix speed test)"""
        print("🔍 Testing with fast.com...")
        
        try:
            # Use curl to test fast.com
            result = subprocess.run(['curl', '-s', 'https://fast.com'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Fast.com returns a simple page, we can't easily extract speed from it
                # This is just a connectivity test
                return {
                    'download_mbps': None,
                    'upload_mbps': None,
                    'ping_ms': None,
                    'server': 'fast.com',
                    'method': 'Fast.com (connectivity only)',
                    'note': 'Fast.com requires JavaScript to run speed tests'
                }
            else:
                return {'error': 'Fast.com connectivity failed'}
                
        except Exception as e:
            return {'error': str(e)}

    def test_google_speed_test(self) -> Dict:
        """Test Google's speed test (if available)"""
        print("🔍 Testing Google speed test...")
        
        try:
            # Google speed test requires browser automation
            # For now, just test connectivity
            response = requests.get('https://www.google.com', timeout=10)
            if response.status_code == 200:
                return {
                    'download_mbps': None,
                    'upload_mbps': None,
                    'ping_ms': None,
                    'server': 'Google',
                    'method': 'Google Speed Test (connectivity only)',
                    'note': 'Google speed test requires browser automation'
                }
            else:
                return {'error': 'Google connectivity failed'}
                
        except Exception as e:
            return {'error': str(e)}

    def test_multiple_file_sizes(self) -> Dict:
        """Test with different file sizes to get more accurate results"""
        print("🔍 Testing with multiple file sizes...")
        
        file_sizes = [
            ("https://httpbin.org/bytes/1048576", 1.0),      # 1MB
            ("https://httpbin.org/bytes/5242880", 5.0),      # 5MB
            ("https://httpbin.org/bytes/10485760", 10.0),    # 10MB
        ]
        
        results = []
        
        for url, size_mb in file_sizes:
            try:
                start_time = time.time()
                response = requests.get(url, timeout=30)
                end_time = time.time()
                
                if response.status_code == 200:
                    duration = end_time - start_time
                    download_speed = (size_mb * 8) / duration
                    results.append({
                        'file_size_mb': size_mb,
                        'duration_seconds': round(duration, 2),
                        'download_mbps': round(download_speed, 2)
                    })
                    
            except Exception as e:
                print(f"❌ Failed to test {size_mb}MB file: {e}")
        
        if results:
            # Calculate average speed
            avg_speed = sum(r['download_mbps'] for r in results) / len(results)
            return {
                'download_mbps': round(avg_speed, 2),
                'upload_mbps': round(avg_speed / 10, 2),
                'ping_ms': None,
                'server': 'httpbin.org (multiple sizes)',
                'method': 'HTTP Download Test (averaged)',
                'details': results
            }
        else:
            return {'error': 'All file size tests failed'}

    async def run_comprehensive_test(self):
        """Run all speed tests and compare results"""
        print("🚀 Starting comprehensive speed test validation...")
        print("=" * 60)
        
        # Test our implementation
        our_result = await self.test_our_implementation()
        self.results['our_implementation'] = our_result
        
        print()
        
        # Test with multiple file sizes
        multi_result = self.test_multiple_file_sizes()
        self.results['multiple_sizes'] = multi_result
        
        print()
        
        # Test speedtest-cli
        cli_result = self.test_speedtest_cli()
        self.results['speedtest_cli'] = cli_result
        
        print()
        
        # Test other services
        fast_result = self.test_fast_com()
        self.results['fast_com'] = fast_result
        
        google_result = self.test_google_speed_test()
        self.results['google'] = google_result
        
        print()
        print("=" * 60)
        print("📊 COMPARISON RESULTS")
        print("=" * 60)
        
        # Compare download speeds
        download_speeds = []
        for method, result in self.results.items():
            if 'download_mbps' in result and result['download_mbps'] is not None:
                download_speeds.append((method, result['download_mbps']))
        
        if download_speeds:
            print("\n📥 Download Speed Comparison:")
            for method, speed in sorted(download_speeds, key=lambda x: x[1], reverse=True):
                print(f"  {method:20} {speed:8.2f} Mbps")
            
            # Calculate variance
            speeds = [speed for _, speed in download_speeds]
            avg_speed = sum(speeds) / len(speeds)
            variance = sum((s - avg_speed) ** 2 for s in speeds) / len(speeds)
            std_dev = variance ** 0.5
            
            print(f"\n📈 Statistics:")
            print(f"  Average Speed: {avg_speed:.2f} Mbps")
            print(f"  Standard Deviation: {std_dev:.2f} Mbps")
            print(f"  Coefficient of Variation: {(std_dev/avg_speed)*100:.1f}%")
            
            # Determine accuracy
            if std_dev / avg_speed < 0.2:  # Less than 20% variation
                print("✅ Speed tests are consistent (good accuracy)")
            elif std_dev / avg_speed < 0.5:  # Less than 50% variation
                print("⚠️  Speed tests show moderate variation")
            else:
                print("❌ Speed tests show high variation (poor accuracy)")
        
        print("\n🔍 Detailed Results:")
        for method, result in self.results.items():
            print(f"\n{method.upper()}:")
            if 'error' in result:
                print(f"  ❌ Error: {result['error']}")
            else:
                print(f"  📥 Download: {result.get('download_mbps', 'N/A')} Mbps")
                print(f"  📤 Upload: {result.get('upload_mbps', 'N/A')} Mbps")
                print(f"  🏓 Ping: {result.get('ping_ms', 'N/A')} ms")
                print(f"  🖥️  Server: {result.get('server', 'N/A')}")
                if 'details' in result:
                    print(f"  📋 Details: {result['details']}")

    def save_results(self, filename: str = "speed_test_results.json"):
        """Save results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n💾 Results saved to {filename}")

async def main():
    """Main function"""
    validator = SpeedTestValidator()
    await validator.run_comprehensive_test()
    validator.save_results()

if __name__ == "__main__":
    asyncio.run(main()) 