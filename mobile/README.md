# 📱 UpTime Monitor Mobile App

A React Native mobile application for remote monitoring of your UpTime Monitor system. Get real-time alerts and monitoring data on your iOS or Android device.

## ✨ **Features**

- **📊 Real-time Dashboard**: Live monitoring data with beautiful charts
- **🔔 Push Notifications**: Instant alerts for outages and performance issues
- **📈 Historical Data**: View trends and performance over time
- **🌐 Offline Support**: Cached data for when you're away from home
- **⚙️ Customizable Alerts**: Configure notification thresholds
- **🎨 Beautiful UI**: Modern, intuitive interface optimized for mobile

## 🚀 **Quick Start**

### Prerequisites

1. **Node.js 16+** and **npm**
2. **React Native CLI**
3. **Xcode** (for iOS) or **Android Studio** (for Android)
4. **Your UpTime Monitor backend running** on your local network

### Installation

1. **Install React Native CLI** (if not already installed):
   ```bash
   npm install -g @react-native-community/cli
   ```

2. **Navigate to the mobile directory**:
   ```bash
   cd mobile
   ```

3. **Install dependencies**:
   ```bash
   npm install
   ```

4. **iOS Setup** (macOS only):
   ```bash
   cd ios
   pod install
   cd ..
   ```

5. **Configure your local IP address**:
   - Open `src/services/ApiService.js`
   - Update `API_BASE_URL` with your computer's local IP address
   - Example: `http://192.168.1.100:8000`

## 📱 **Running the App**

### iOS (macOS only)
```bash
npm run ios
```

### Android
```bash
npm run android
```

### Start Metro Bundler
```bash
npm start
```

## 🔧 **Configuration**

### **1. Local Network Setup**

**Find your computer's IP address:**
```bash
# macOS/Linux
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows
ipconfig | findstr "IPv4"
```

**Update the API URL:**
Edit `src/services/ApiService.js`:
```javascript
const API_BASE_URL = 'http://YOUR_IP_ADDRESS:8000';
```

### **2. Notification Settings**

The app includes comprehensive notification settings:
- **Outage Alerts**: Get notified when internet goes down
- **Speed Alerts**: Alert when speeds drop below threshold
- **Uptime Alerts**: Notify when uptime falls below 95%
- **Daily Reports**: Scheduled daily performance summaries

### **3. Offline Mode**

The app automatically caches data for offline viewing:
- Last dashboard data is stored locally
- Historical data available offline
- Automatic sync when connection restored

## 📊 **App Screens**

### **Dashboard**
- Real-time connection status
- Current speed metrics
- 24-hour uptime summary
- Interactive charts
- Recent outage timeline

### **History**
- Detailed connectivity logs
- Speed test history
- Outage events with duration
- Performance trends

### **Alerts**
- Notification history
- Alert settings configuration
- Custom thresholds
- Alert statistics

### **Settings**
- Server configuration
- Notification preferences
- Data retention settings
- App preferences

## 🔔 **Push Notifications**

### **Types of Alerts**
1. **Outage Detection**: When internet connection is lost
2. **Recovery Notification**: When connection is restored
3. **Speed Alerts**: When speeds drop below threshold
4. **Uptime Alerts**: When uptime falls below 95%
5. **Daily Reports**: Scheduled performance summaries

### **Notification Permissions**
The app will request notification permissions on first launch. Grant permissions to receive alerts.

## 🛠️ **Troubleshooting**

### **Connection Issues**
1. **Check IP Address**: Ensure the API_BASE_URL is correct
2. **Network Access**: Make sure your phone can reach your computer
3. **Firewall**: Allow port 8000 through your firewall
4. **Backend Running**: Ensure your UpTime Monitor backend is running

### **Build Issues**
1. **Clean Build**: 
   ```bash
   # iOS
   cd ios && xcodebuild clean && cd ..
   
   # Android
   cd android && ./gradlew clean && cd ..
   ```

2. **Reset Metro Cache**:
   ```bash
   npm start -- --reset-cache
   ```

3. **Reinstall Dependencies**:
   ```bash
   rm -rf node_modules
   npm install
   ```

### **Common Issues**

**"Network request failed"**
- Check your IP address configuration
- Ensure backend is running on port 8000
- Verify network connectivity

**"Cannot connect to development server"**
- Make sure Metro bundler is running
- Check if ports are blocked by firewall
- Try using USB debugging for Android

## 📱 **Building for Production**

### **iOS App Store**
```bash
# Build for release
cd ios
xcodebuild -workspace UpTimeMonitor.xcworkspace -scheme UpTimeMonitor -configuration Release -destination generic/platform=iOS -archivePath UpTimeMonitor.xcarchive archive
```

### **Android Play Store**
```bash
# Build APK
cd android
./gradlew assembleRelease

# Build AAB (recommended for Play Store)
./gradlew bundleRelease
```

## 🔒 **Security Considerations**

- **Local Network Only**: The app connects to your local network
- **No External Data**: All data stays on your local network
- **Secure Storage**: Sensitive data is stored securely on device
- **Permission Control**: Minimal permissions required

## 📈 **Performance Features**

- **Efficient Caching**: Smart data caching for offline use
- **Background Sync**: Automatic data updates when connected
- **Optimized Charts**: Smooth, responsive data visualization
- **Memory Management**: Efficient memory usage for long-running sessions

## 🎯 **Arizona Timezone Support**

Just like your web dashboard, the mobile app displays all times in **Arizona time (MST/MDT)** for consistency.

## 📞 **Support**

If you encounter issues:
1. Check the troubleshooting section above
2. Verify your backend is running correctly
3. Check network connectivity between devices
4. Review the console logs for error messages

## 🚀 **Future Enhancements**

- **Geographic Monitoring**: Monitor multiple locations
- **Advanced Analytics**: Machine learning insights
- **Custom Dashboards**: Personalized monitoring views
- **Integration**: Connect with other smart home devices

---

**Your UpTime Monitor is now mobile-ready with real-time alerts and monitoring! 📱** 