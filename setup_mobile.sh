#!/bin/bash
# UpTime Monitor Mobile App Setup Script
# This script helps set up and configure the React Native mobile app

echo "📱 Setting up UpTime Monitor Mobile App..."
echo ""

# Set up environment for macOS with Homebrew
export PATH="/opt/homebrew/bin:$PATH"

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -d "mobile" ]; then
    echo "❌ Error: Please run this script from the UpTimeMonitor directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected: main.py and mobile/ directory"
    exit 1
fi

echo "✅ Directory check passed"

# Check Node.js
echo "📦 Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Installing via Homebrew..."
    brew install node
else
    echo "✅ Node.js found: $(node --version)"
fi

# Check React Native CLI
echo "📦 Checking React Native CLI..."
if ! command -v react-native &> /dev/null; then
    echo "📦 Installing React Native CLI..."
    npm install -g @react-native-community/cli
else
    echo "✅ React Native CLI found"
fi

# Navigate to mobile directory
cd mobile

# Install dependencies
echo "📦 Installing mobile app dependencies..."
npm install

# iOS setup (macOS only)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Setting up iOS dependencies..."
    if [ -d "ios" ]; then
        cd ios
        pod install
        cd ..
        echo "✅ iOS setup complete"
    else
        echo "⚠️  iOS directory not found - skipping iOS setup"
    fi
else
    echo "⚠️  Not on macOS - skipping iOS setup"
fi

# Get local IP address
echo "🌐 Detecting local IP address..."
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')

if [ -z "$LOCAL_IP" ]; then
    echo "❌ Could not detect local IP address"
    echo "   Please manually update src/services/ApiService.js with your IP"
else
    echo "✅ Detected local IP: $LOCAL_IP"
    
    # Update API service with local IP
    API_SERVICE_FILE="src/services/ApiService.js"
    if [ -f "$API_SERVICE_FILE" ]; then
        # Create backup
        cp "$API_SERVICE_FILE" "${API_SERVICE_FILE}.backup"
        
        # Update IP address
        sed -i.bak "s|http://192.168.1.100:8000|http://$LOCAL_IP:8000|g" "$API_SERVICE_FILE"
        
        echo "✅ Updated API service with local IP: $LOCAL_IP"
        echo "   Backup saved as: ${API_SERVICE_FILE}.backup"
    else
        echo "⚠️  API service file not found - please update manually"
    fi
fi

echo ""
echo "✅ Mobile app setup complete!"
echo ""
echo "🚀 Next steps:"
echo ""
echo "1. Start your UpTime Monitor backend:"
echo "   cd .. && ./start_app_quiet.sh"
echo ""
echo "2. Start the mobile app:"
echo "   # For iOS (macOS only):"
echo "   npm run ios"
echo ""
echo "   # For Android:"
echo "   npm run android"
echo ""
echo "   # Start Metro bundler:"
echo "   npm start"
echo ""
echo "📱 Mobile app features:"
echo "   - Real-time monitoring dashboard"
echo "   - Push notifications for outages"
echo "   - Speed and uptime alerts"
echo "   - Offline data caching"
echo "   - Arizona timezone support"
echo ""
echo "🔧 Configuration:"
echo "   - Edit src/services/ApiService.js to change server IP"
echo "   - Configure notifications in the app settings"
echo "   - Customize alert thresholds"
echo "" 