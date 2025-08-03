import React, { useState, useEffect } from 'react';
import {
  SafeAreaView,
  StatusBar,
  StyleSheet,
  View,
  Text,
  Alert,
  Platform,
} from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import NetInfo from 'react-native-netinfo';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Import screens
import DashboardScreen from './src/screens/DashboardScreen';
import HistoryScreen from './src/screens/HistoryScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import AlertsScreen from './src/screens/AlertsScreen';

// Import components
import LoadingScreen from './src/components/LoadingScreen';
import OfflineBanner from './src/components/OfflineBanner';

// Import services
import { ApiService } from './src/services/ApiService';
import { NotificationService } from './src/services/NotificationService';
import { StorageService } from './src/services/StorageService';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

// Configuration
const API_BASE_URL = 'http://192.168.1.100:8000'; // Update with your local IP
const REFRESH_INTERVAL = 30000; // 30 seconds

function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName;

          if (route.name === 'Dashboard') {
            iconName = focused ? 'monitor-dashboard' : 'monitor-dashboard-outline';
          } else if (route.name === 'History') {
            iconName = focused ? 'chart-line' : 'chart-line-variant';
          } else if (route.name === 'Alerts') {
            iconName = focused ? 'bell' : 'bell-outline';
          } else if (route.name === 'Settings') {
            iconName = focused ? 'cog' : 'cog-outline';
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#3b82f6',
        tabBarInactiveTintColor: 'gray',
        tabBarStyle: {
          backgroundColor: '#ffffff',
          borderTopColor: '#e5e7eb',
          paddingBottom: Platform.OS === 'ios' ? 20 : 10,
          paddingTop: 10,
          height: Platform.OS === 'ios' ? 90 : 70,
        },
        headerStyle: {
          backgroundColor: '#3b82f6',
        },
        headerTintColor: '#ffffff',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      })}
    >
      <Tab.Screen 
        name="Dashboard" 
        component={DashboardScreen}
        options={{ title: 'UpTime Monitor' }}
      />
      <Tab.Screen 
        name="History" 
        component={HistoryScreen}
        options={{ title: 'History' }}
      />
      <Tab.Screen 
        name="Alerts" 
        component={AlertsScreen}
        options={{ title: 'Alerts' }}
      />
      <Tab.Screen 
        name="Settings" 
        component={SettingsScreen}
        options={{ title: 'Settings' }}
      />
    </Tab.Navigator>
  );
}

export default function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [isOnline, setIsOnline] = useState(true);
  const [serverStatus, setServerStatus] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    initializeApp();
    setupNetworkListener();
    setupNotificationService();
  }, []);

  const initializeApp = async () => {
    try {
      // Initialize services
      await StorageService.initialize();
      await NotificationService.initialize();
      
      // Check server connectivity
      await checkServerStatus();
      
      // Load cached data
      await loadCachedData();
      
      setIsLoading(false);
    } catch (error) {
      console.error('App initialization error:', error);
      setIsLoading(false);
    }
  };

  const setupNetworkListener = () => {
    NetInfo.addEventListener(state => {
      setIsOnline(state.isConnected);
      
      if (state.isConnected && !serverStatus?.isConnected) {
        checkServerStatus();
      }
    });
  };

  const setupNotificationService = () => {
    NotificationService.requestPermissions();
  };

  const checkServerStatus = async () => {
    try {
      const status = await ApiService.getHealthStatus();
      setServerStatus(status);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Server status check failed:', error);
      setServerStatus({ isConnected: false, error: error.message });
    }
  };

  const loadCachedData = async () => {
    try {
      const cachedData = await StorageService.getCachedData();
      if (cachedData) {
        // Use cached data for initial load
        console.log('Loaded cached data');
      }
    } catch (error) {
      console.error('Failed to load cached data:', error);
    }
  };

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#3b82f6" />
      
      {!isOnline && <OfflineBanner />}
      
      <NavigationContainer>
        <Stack.Navigator>
          <Stack.Screen 
            name="Main" 
            component={TabNavigator}
            options={{ headerShown: false }}
          />
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
}); 