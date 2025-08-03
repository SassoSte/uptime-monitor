import PushNotification from 'react-native-push-notification';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

export class NotificationService {
  static isInitialized = false;

  static async initialize() {
    if (this.isInitialized) return;

    try {
      // Configure push notifications
      PushNotification.configure({
        // (optional) Called when Token is generated (iOS and Android)
        onRegister: function (token) {
          console.log('TOKEN:', token);
          AsyncStorage.setItem('push_token', token);
        },

        // (required) Called when a remote or local notification is opened or received
        onNotification: function (notification) {
          console.log('NOTIFICATION:', notification);
        },

        // (optional) Called when the user fails to register for remote notifications. Typically occurs when APNS is having issues, or the device is a simulator. (iOS)
        onRegistrationError: function (err) {
          console.error('Registration error:', err.message, err);
        },

        // IOS ONLY (optional): default: all - Permissions to register.
        permissions: {
          alert: true,
          badge: true,
          sound: true,
        },

        // Should the initial notification be popped automatically
        popInitialNotification: true,

        /**
         * (optional) default: true
         * - false: it will not be called (only if `popInitialNotification` is true)
         * - true: it will be called every time a notification is opened or received
         */
        requestPermissions: Platform.OS === 'ios',
      });

      // Create notification channel for Android
      if (Platform.OS === 'android') {
        PushNotification.createChannel(
          {
            channelId: 'uptime-monitor',
            channelName: 'UpTime Monitor',
            channelDescription: 'Internet monitoring alerts',
            playSound: true,
            soundName: 'default',
            importance: 4,
            vibrate: true,
          },
          (created) => console.log(`Notification channel created: ${created}`)
        );
      }

      this.isInitialized = true;
      console.log('Notification service initialized');
    } catch (error) {
      console.error('Failed to initialize notification service:', error);
    }
  }

  static async requestPermissions() {
    try {
      if (Platform.OS === 'ios') {
        const authStatus = await PushNotification.requestPermissions();
        console.log('Notification permissions:', authStatus);
        return authStatus;
      }
    } catch (error) {
      console.error('Failed to request notification permissions:', error);
    }
  }

  static showNotification(title, message, data = {}) {
    try {
      PushNotification.localNotification({
        channelId: 'uptime-monitor',
        title: title,
        message: message,
        data: data,
        playSound: true,
        soundName: 'default',
        importance: 'high',
        priority: 'high',
        vibrate: true,
        vibration: 300,
        autoCancel: true,
        largeIcon: 'ic_launcher',
        smallIcon: 'ic_notification',
        bigText: message,
        subText: 'UpTime Monitor',
        color: '#3b82f6',
        number: 10,
        actions: ['View', 'Dismiss'],
      });

      console.log(`Notification sent: ${title} - ${message}`);
    } catch (error) {
      console.error('Failed to show notification:', error);
    }
  }

  static showOutageNotification(duration, timestamp) {
    const title = 'Internet Outage Detected';
    const message = `Your internet connection has been down for ${duration} minutes.`;
    
    this.showNotification(title, message, {
      type: 'outage',
      duration: duration,
      timestamp: timestamp,
    });
  }

  static showRecoveryNotification(duration) {
    const title = 'Internet Connection Restored';
    const message = `Your internet connection is back online after ${duration} minutes of downtime.`;
    
    this.showNotification(title, message, {
      type: 'recovery',
      duration: duration,
    });
  }

  static showSpeedAlert(currentSpeed, threshold) {
    const title = 'Slow Internet Speed';
    const message = `Your current speed is ${currentSpeed} Mbps, below the ${threshold} Mbps threshold.`;
    
    this.showNotification(title, message, {
      type: 'speed_alert',
      currentSpeed: currentSpeed,
      threshold: threshold,
    });
  }

  static showUptimeAlert(uptime) {
    const title = 'Low Uptime Alert';
    const message = `Your internet uptime is ${uptime.toFixed(1)}% in the last 24 hours.`;
    
    this.showNotification(title, message, {
      type: 'uptime_alert',
      uptime: uptime,
    });
  }

  static schedulePeriodicNotification() {
    try {
      // Schedule a daily summary notification
      PushNotification.localNotificationSchedule({
        channelId: 'uptime-monitor',
        title: 'Daily Internet Report',
        message: 'Check your daily internet performance summary',
        date: new Date(Date.now() + 24 * 60 * 60 * 1000), // 24 hours from now
        repeatType: 'day',
        allowWhileIdle: true,
        data: {
          type: 'daily_summary',
        },
      });
    } catch (error) {
      console.error('Failed to schedule periodic notification:', error);
    }
  }

  static cancelAllNotifications() {
    try {
      PushNotification.cancelAllLocalNotifications();
      console.log('All notifications cancelled');
    } catch (error) {
      console.error('Failed to cancel notifications:', error);
    }
  }

  static cancelNotification(id) {
    try {
      PushNotification.cancelLocalNotification(id);
      console.log(`Notification ${id} cancelled`);
    } catch (error) {
      console.error('Failed to cancel notification:', error);
    }
  }

  static getScheduledNotifications() {
    return new Promise((resolve, reject) => {
      PushNotification.getScheduledLocalNotifications((notifications) => {
        resolve(notifications);
      });
    });
  }

  static async saveNotificationSettings(settings) {
    try {
      await AsyncStorage.setItem('notification_settings', JSON.stringify(settings));
      console.log('Notification settings saved');
    } catch (error) {
      console.error('Failed to save notification settings:', error);
    }
  }

  static async getNotificationSettings() {
    try {
      const settings = await AsyncStorage.getItem('notification_settings');
      return settings ? JSON.parse(settings) : this.getDefaultSettings();
    } catch (error) {
      console.error('Failed to get notification settings:', error);
      return this.getDefaultSettings();
    }
  }

  static getDefaultSettings() {
    return {
      outages: {
        enabled: true,
        minDuration: 1, // minutes
      },
      speed: {
        enabled: true,
        threshold: 10, // Mbps
      },
      uptime: {
        enabled: true,
        threshold: 95, // percentage
      },
      daily: {
        enabled: true,
        time: '09:00', // 9 AM
      },
      sound: true,
      vibration: true,
    };
  }

  static async logNotification(title, message, data = {}) {
    try {
      const notifications = await this.getNotificationLog();
      const newNotification = {
        id: Date.now().toString(),
        title,
        message,
        data,
        timestamp: new Date().toISOString(),
      };

      notifications.unshift(newNotification);
      
      // Keep only last 100 notifications
      if (notifications.length > 100) {
        notifications.splice(100);
      }

      await AsyncStorage.setItem('notification_log', JSON.stringify(notifications));
    } catch (error) {
      console.error('Failed to log notification:', error);
    }
  }

  static async getNotificationLog() {
    try {
      const log = await AsyncStorage.getItem('notification_log');
      return log ? JSON.parse(log) : [];
    } catch (error) {
      console.error('Failed to get notification log:', error);
      return [];
    }
  }

  static async clearNotificationLog() {
    try {
      await AsyncStorage.removeItem('notification_log');
      console.log('Notification log cleared');
    } catch (error) {
      console.error('Failed to clear notification log:', error);
    }
  }
}

export default NotificationService; 