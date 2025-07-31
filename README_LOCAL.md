# UpTime Monitor - Local Setup Guide

Your friend's network monitoring application is now set up and ready to run!

## 🚀 Quick Start

### **Option 1: Use the startup script (Recommended)**
```bash
./start_app.sh
```

### **Option 2: Manual startup**
```bash
# Terminal 1: Start backend
source venv/bin/activate
python main.py

# Terminal 2: Start frontend
npm start
```

## 📊 What You'll Get

- **Real-time network monitoring** with ping tests every 30 seconds
- **Speed tests** every 15 minutes
- **Beautiful Notion-style interface** at http://localhost:3000
- **API documentation** at http://localhost:8000/docs
- **Historical data** stored in SQLite database

## 🔧 Configuration

Edit `config.json` to customize:
- **Ping interval**: Currently 30 seconds
- **Speed test frequency**: Currently 15 minutes
- **Target hosts**: Google, Cloudflare, etc.
- **Alert thresholds**: Outage and slow speed detection

## 📈 Features

- **Connectivity monitoring**: Tracks uptime/downtime
- **Speed testing**: Measures download/upload speeds
- **Historical trends**: Visualizes performance over time
- **Outage detection**: Automatically logs connectivity issues
- **ISP reporting**: Generate reports for your internet provider

## 🛠️ Architecture

- **Backend**: Python FastAPI with SQLite database
- **Frontend**: React with Tailwind CSS (Notion-style UI)
- **Monitoring**: Async service with configurable intervals
- **Data**: Local SQLite storage (no cloud dependencies)

## 🎯 Perfect for

- Monitoring your home internet connection
- Tracking ISP performance issues
- Creating reports for customer service
- Understanding network patterns

## 🚨 Troubleshooting

If you encounter issues:
1. Make sure both ports (3000, 8000) are available
2. Check that the virtual environment is activated
3. Verify all dependencies are installed
4. Check the logs in the terminal output

Enjoy monitoring your network! 🌐📊 