import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Alert,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { LineChart } from 'react-native-chart-kit';
import { Dimensions } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import Shimmer from 'react-native-shimmer';

// Import components
import StatusCard from '../components/StatusCard';
import MetricCard from '../components/MetricCard';
import SpeedGauge from '../components/SpeedGauge';
import OutageTimeline from '../components/OutageTimeline';

// Import services
import { ApiService } from '../services/ApiService';
import { NotificationService } from '../services/NotificationService';

const { width } = Dimensions.get('window');

export default function DashboardScreen() {
  const [dashboardData, setDashboardData] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);
  const refreshIntervalRef = useRef(null);

  useEffect(() => {
    loadDashboardData();
    setupAutoRefresh();
    
    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, []);

  const setupAutoRefresh = () => {
    // Refresh data every 30 seconds
    refreshIntervalRef.current = setInterval(() => {
      loadDashboardData(false);
    }, 30000);
  };

  const loadDashboardData = async (showLoading = true) => {
    try {
      if (showLoading) {
        setIsLoading(true);
      }

      // Load dashboard stats
      const stats = await ApiService.getDashboardStats();
      setDashboardData(stats);
      setLastUpdate(new Date());

      // Load chart data
      const uptimeData = await ApiService.getUptimeChartData(24);
      const speedData = await ApiService.getSpeedChartData(24);
      
      setChartData({
        uptime: uptimeData,
        speed: speedData,
      });

      // Check for critical alerts
      checkForAlerts(stats);

    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      Alert.alert('Error', 'Failed to load monitoring data. Please check your connection.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const checkForAlerts = (stats) => {
    if (stats.uptime_24h < 95) {
      NotificationService.showNotification(
        'Low Uptime Alert',
        `Your internet uptime is ${stats.uptime_24h.toFixed(1)}% in the last 24 hours.`
      );
    }

    if (stats.avg_speed_24h && stats.avg_speed_24h < 10) {
      NotificationService.showNotification(
        'Slow Speed Alert',
        `Your average speed is ${stats.avg_speed_24h.toFixed(1)} Mbps.`
      );
    }
  };

  const onRefresh = () => {
    setIsRefreshing(true);
    loadDashboardData(false);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected':
        return '#10b981';
      case 'disconnected':
        return '#ef4444';
      case 'warning':
        return '#f59e0b';
      default:
        return '#6b7280';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'connected':
        return 'wifi';
      case 'disconnected':
        return 'wifi-off';
      case 'warning':
        return 'wifi-strength-2';
      default:
        return 'wifi-strength-1';
    }
  };

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <ScrollView contentContainerStyle={styles.loadingContainer}>
          <Shimmer>
            <View style={styles.shimmerCard} />
          </Shimmer>
          <Shimmer>
            <View style={styles.shimmerCard} />
          </Shimmer>
          <Shimmer>
            <View style={styles.shimmerCard} />
          </Shimmer>
        </ScrollView>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={isRefreshing} onRefresh={onRefresh} />
        }
      >
        {/* Header with last update */}
        <View style={styles.header}>
          <Text style={styles.lastUpdate}>
            Last updated: {lastUpdate ? lastUpdate.toLocaleTimeString() : 'Never'}
          </Text>
        </View>

        {/* Current Status Card */}
        {dashboardData && (
          <StatusCard
            status={dashboardData.current_status}
            uptime={dashboardData.uptime_24h}
            latency={dashboardData.current_latency}
            color={getStatusColor(dashboardData.current_status)}
            icon={getStatusIcon(dashboardData.current_status)}
          />
        )}

        {/* Speed Metrics */}
        {dashboardData?.last_speed_test && (
          <View style={styles.speedSection}>
            <Text style={styles.sectionTitle}>Current Speed</Text>
            <View style={styles.speedCards}>
              <SpeedGauge
                title="Download"
                value={dashboardData.last_speed_test.download_mbps}
                unit="Mbps"
                color="#3b82f6"
              />
              <SpeedGauge
                title="Upload"
                value={dashboardData.last_speed_test.upload_mbps}
                unit="Mbps"
                color="#10b981"
              />
            </View>
          </View>
        )}

        {/* Key Metrics */}
        <View style={styles.metricsSection}>
          <Text style={styles.sectionTitle}>24-Hour Summary</Text>
          <View style={styles.metricsGrid}>
            <MetricCard
              title="Uptime"
              value={`${dashboardData?.uptime_24h?.toFixed(1) || 0}%`}
              icon="clock-outline"
              color="#3b82f6"
            />
            <MetricCard
              title="Avg Speed"
              value={`${dashboardData?.avg_speed_24h?.toFixed(1) || 0} Mbps`}
              icon="speedometer"
              color="#10b981"
            />
            <MetricCard
              title="Outages"
              value={dashboardData?.total_outages_24h || 0}
              icon="alert-circle-outline"
              color="#ef4444"
            />
            <MetricCard
              title="Latency"
              value={`${dashboardData?.current_latency?.toFixed(1) || 0} ms`}
              icon="timer-outline"
              color="#f59e0b"
            />
          </View>
        </View>

        {/* Uptime Chart */}
        {chartData?.uptime && (
          <View style={styles.chartSection}>
            <Text style={styles.sectionTitle}>Uptime Trend (24h)</Text>
            <LineChart
              data={{
                labels: ['6h ago', '12h ago', '18h ago', 'Now'],
                datasets: [{
                  data: chartData.uptime.map(point => point.value),
                }],
              }}
              width={width - 40}
              height={200}
              chartConfig={{
                backgroundColor: '#ffffff',
                backgroundGradientFrom: '#ffffff',
                backgroundGradientTo: '#ffffff',
                decimalPlaces: 0,
                color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`,
                labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                style: {
                  borderRadius: 16,
                },
                propsForDots: {
                  r: '6',
                  strokeWidth: '2',
                  stroke: '#3b82f6',
                },
              }}
              bezier
              style={styles.chart}
            />
          </View>
        )}

        {/* Recent Outages */}
        <View style={styles.outagesSection}>
          <Text style={styles.sectionTitle}>Recent Outages</Text>
          <OutageTimeline hours={24} />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 20,
  },
  loadingContainer: {
    padding: 20,
  },
  shimmerCard: {
    height: 120,
    backgroundColor: '#e5e7eb',
    borderRadius: 12,
    marginBottom: 16,
  },
  header: {
    marginBottom: 20,
  },
  lastUpdate: {
    fontSize: 12,
    color: '#6b7280',
    textAlign: 'center',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 16,
  },
  speedSection: {
    marginBottom: 24,
  },
  speedCards: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metricsSection: {
    marginBottom: 24,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  chartSection: {
    marginBottom: 24,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  outagesSection: {
    marginBottom: 24,
  },
}); 