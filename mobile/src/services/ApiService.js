import axios from 'react-native-axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Configuration
const API_BASE_URL = 'http://192.168.1.100:8000'; // Update with your local IP
const API_TIMEOUT = 10000; // 10 seconds

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.message);
    return Promise.reject(error);
  }
);

export class ApiService {
  static async getHealthStatus() {
    try {
      const response = await apiClient.get('/api/health');
      return response.data;
    } catch (error) {
      throw new Error(`Health check failed: ${error.message}`);
    }
  }

  static async getDashboardStats() {
    try {
      const response = await apiClient.get('/api/dashboard');
      
      // Cache the data for offline use
      await AsyncStorage.setItem('dashboard_stats', JSON.stringify(response.data));
      await AsyncStorage.setItem('dashboard_stats_timestamp', new Date().toISOString());
      
      return response.data;
    } catch (error) {
      // Try to return cached data if available
      const cachedData = await AsyncStorage.getItem('dashboard_stats');
      if (cachedData) {
        console.log('Using cached dashboard data');
        return JSON.parse(cachedData);
      }
      throw new Error(`Failed to load dashboard stats: ${error.message}`);
    }
  }

  static async getConnectivityTests(hours = 24) {
    try {
      const response = await apiClient.get(`/api/connectivity?hours=${hours}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to load connectivity tests: ${error.message}`);
    }
  }

  static async getSpeedTests(hours = 24) {
    try {
      const response = await apiClient.get(`/api/speed-tests?hours=${hours}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to load speed tests: ${error.message}`);
    }
  }

  static async getOutages(days = 7) {
    try {
      const response = await apiClient.get(`/api/outages?days=${days}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to load outages: ${error.message}`);
    }
  }

  static async getUptimeChartData(hours = 24) {
    try {
      const response = await apiClient.get(`/api/charts/uptime?hours=${hours}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to load uptime chart data: ${error.message}`);
    }
  }

  static async getSpeedChartData(hours = 24, metric = 'download') {
    try {
      const response = await apiClient.get(`/api/charts/speed?hours=${hours}&metric=${metric}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to load speed chart data: ${error.message}`);
    }
  }

  static async generateReport(days = 7) {
    try {
      const response = await apiClient.get(`/api/report?days=${days}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to generate report: ${error.message}`);
    }
  }

  static async getConfig() {
    try {
      const response = await apiClient.get('/api/config');
      return response.data;
    } catch (error) {
      throw new Error(`Failed to load config: ${error.message}`);
    }
  }

  static async saveConfig(config) {
    try {
      const response = await apiClient.post('/api/config', config);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to save config: ${error.message}`);
    }
  }

  static async cleanupDatabase() {
    try {
      const response = await apiClient.post('/api/cleanup');
      return response.data;
    } catch (error) {
      throw new Error(`Failed to cleanup database: ${error.message}`);
    }
  }

  // Helper method to get your local IP address
  static async discoverLocalIP() {
    try {
      // Try common local IP ranges
      const commonIPs = [
        '192.168.1.100',
        '192.168.1.101',
        '192.168.0.100',
        '192.168.0.101',
        '10.0.0.100',
        '10.0.0.101',
      ];

      for (const ip of commonIPs) {
        try {
          const response = await axios.get(`http://${ip}:8000/api/health`, {
            timeout: 2000,
          });
          if (response.status === 200) {
            console.log(`Found server at: ${ip}`);
            return ip;
          }
        } catch (error) {
          // Continue to next IP
        }
      }

      throw new Error('Could not discover local server IP');
    } catch (error) {
      throw new Error(`IP discovery failed: ${error.message}`);
    }
  }

  // Method to update API base URL
  static updateBaseURL(newURL) {
    apiClient.defaults.baseURL = newURL;
    console.log(`API base URL updated to: ${newURL}`);
  }

  // Method to test connection
  static async testConnection() {
    try {
      const startTime = Date.now();
      const response = await apiClient.get('/api/health');
      const endTime = Date.now();
      
      return {
        success: true,
        responseTime: endTime - startTime,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
      };
    }
  }

  // Method to get cached data
  static async getCachedData() {
    try {
      const [dashboardStats, timestamp] = await Promise.all([
        AsyncStorage.getItem('dashboard_stats'),
        AsyncStorage.getItem('dashboard_stats_timestamp'),
      ]);

      if (dashboardStats && timestamp) {
        const dataAge = Date.now() - new Date(timestamp).getTime();
        const maxAge = 5 * 60 * 1000; // 5 minutes

        if (dataAge < maxAge) {
          return JSON.parse(dashboardStats);
        }
      }

      return null;
    } catch (error) {
      console.error('Failed to get cached data:', error);
      return null;
    }
  }

  // Method to clear cache
  static async clearCache() {
    try {
      await AsyncStorage.multiRemove([
        'dashboard_stats',
        'dashboard_stats_timestamp',
      ]);
      console.log('Cache cleared successfully');
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
  }
}

export default ApiService; 