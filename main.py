#!/usr/bin/env python3
"""
UpTime Monitor - Main Application Entry Point

This starts both the FastAPI server and the background monitoring service.
"""

import asyncio
import json
import os
import uvicorn
from backend.api import app
from backend.monitoring import InternetMonitor
from backend.database import init_database
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from config.json"""
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    else:
        logger.warning("config.json not found, using default configuration")
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
            "server": {
                "host": "localhost",
                "port": 8000,
                "debug": True
            }
        }

async def start_monitoring_service(config):
    """Start the background monitoring service"""
    monitor = InternetMonitor(config)
    logger.info("Starting monitoring service...")
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("Monitoring service stopped by user")
    except Exception as e:
        logger.error(f"Monitoring service error: {e}")
    finally:
        await monitor.stop_monitoring()

def start_api_server(config):
    """Start the FastAPI server"""
    server_config = config.get('server', {})
    host = server_config.get('host', 'localhost')
    port = server_config.get('port', 8000)
    debug = server_config.get('debug', True)
    
    logger.info(f"Starting API server on {host}:{port}")
    import uvicorn
    uvicorn.run(
        "backend.api:app", 
        host=host, 
        port=port, 
        log_level="info" if debug else "warning",
        reload=False  # Disable reload to avoid threading issues
    )

async def main():
    """Main application entry point"""
    config = load_config()
    
    # Initialize database
    logger.info("Initializing database...")
    await init_database()
    
    # Create tasks for both monitoring and API server
    logger.info("Starting UpTime Monitor application...")
    
    # Start monitoring service in background
    monitoring_task = asyncio.create_task(start_monitoring_service(config))
    
    # Start API server (this blocks)
    try:
        await asyncio.create_task(
            asyncio.to_thread(start_api_server, config)
        )
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    finally:
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            logger.info("Monitoring service cancelled")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise