# UpTime Monitor

A comprehensive internet uptime and bandwidth monitoring application with a clean, Notion-style interface.

## Features

- **Real-time Internet Monitoring**: Continuous monitoring of internet connectivity and speed
- **Bandwidth Testing**: Regular speed tests to track internet performance
- **Outage Detection**: Automatic detection and logging of internet outages
- **Historical Data**: Store and visualize long-term connectivity trends
- **Notion-style Interface**: Clean, modern web interface inspired by Notion.com
- **Reports & Analytics**: Generate reports to show ISP performance issues
- **Local Operation**: Runs entirely on your local machine

## Quick Start

### Prerequisites

- Python 3.8+ 
- Node.js 16+
- npm or yarn

### Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd UpTimeMonitor
   ```

2. **Set up Python backend**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up React frontend**
   ```bash
   npm install
   ```

4. **Start the application**
   ```bash
   # Terminal 1: Start backend
   python main.py
   
   # Terminal 2: Start frontend
   npm start
   ```

5. **Access the application**
   - Open your browser to `http://localhost:3000`
   - The backend API runs on `http://localhost:8000`

## Architecture

- **Backend**: Python with FastAPI, SQLite database
- **Frontend**: React with Tailwind CSS for Notion-style UI
- **Monitoring**: Async monitoring service with configurable intervals
- **Data Storage**: SQLite for historical data and analytics

## Configuration

Edit `config.json` to customize:
- Monitoring intervals
- Speed test frequency  
- Alert thresholds
- Data retention policies

## Usage

The application will automatically start monitoring your internet connection. View real-time data and historical trends through the web interface to identify patterns and create reports for your ISP.