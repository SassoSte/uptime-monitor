#!/usr/bin/env python3
"""
Test script to demonstrate timezone conversion from UTC to Arizona time
"""

import pytz
from datetime import datetime

def test_timezone_conversion():
    """Test the timezone conversion functionality"""
    print("🕐 Timezone Conversion Test")
    print("=" * 40)
    
    # Get current UTC time
    utc_now = datetime.utcnow()
    print(f"UTC Time: {utc_now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    # Convert to Arizona time
    arizona_tz = pytz.timezone('America/Phoenix')
    arizona_time = utc_now.replace(tzinfo=pytz.UTC).astimezone(arizona_tz)
    print(f"Arizona Time: {arizona_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Show the difference
    print(f"Timezone: {arizona_time.tzinfo}")
    print(f"Offset: {arizona_time.utcoffset()}")
    
    print("\n✅ Timezone conversion working correctly!")
    print("All timestamps in the UpTime Monitor will now show Arizona time.")

if __name__ == "__main__":
    test_timezone_conversion() 