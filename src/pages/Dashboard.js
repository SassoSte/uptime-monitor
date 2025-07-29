import React, { useState, useEffect, useMemo } from 'react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Wifi, Zap, Clock, AlertTriangle, RefreshCw } from 'lucide-react';
import MetricCard from '../components/MetricCard';
import StatusIndicator from '../components/StatusIndicator';
import { format } from 'date-fns';

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [uptimeChartData, setUptimeChartData] = useState([]);
  const [speedChartData, setSpeedChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [usingRealData, setUsingRealData] = useState(false);

  // Memoized demo data to avoid recreating Date objects repeatedly
  const demoData = useMemo(() => ({
    dashboardData: {
      current_status: 'connected',
      uptime_24h: 97.8,
      avg_speed_24h: 125.6,
      total_outages_24h: 2,
      current_latency: 32.5,
      last_speed_test: {
        download_mbps: 128.4,
        upload_mbps: 15.2,
        ping_ms: 28,
        server_location: 'Seattle, WA, United States'
      }
    },
    uptimeChartData: [
      { timestamp: new Date(Date.now() - 23*60*60*1000).toISOString(), value: 100 },
      { timestamp: new Date(Date.now() - 22*60*60*1000).toISOString(), value: 98.5 },
      { timestamp: new Date(Date.now() - 21*60*60*1000).toISOString(), value: 95.2 },
      { timestamp: new Date(Date.now() - 20*60*60*1000).toISOString(), value: 0 },
      { timestamp: new Date(Date.now() - 19*60*60*1000).toISOString(), value: 0 },
      { timestamp: new Date(Date.now() - 18*60*60*1000).toISOString(), value: 100 },
      { timestamp: new Date(Date.now() - 17*60*60*1000).toISOString(), value: 100 },
      { timestamp: new Date(Date.now() - 16*60*60*1000).toISOString(), value: 100 },
      { timestamp: new Date(Date.now() - 15*60*60*1000).toISOString(), value: 100 },
      { timestamp: new Date(Date.now() - 14*60*60*1000).toISOString(), value: 100 },
      { timestamp: new Date(Date.now() - 13*60*60*1000).toISOString(), value: 98.1 },
      { timestamp: new Date(Date.now() - 12*60*60*1000).toISOString(), value: 97.8 },
      { timestamp: new Date(Date.now() - 11*60*60*1000).toISOString(), value: 100 },
      { timestamp: new Date(Date.now() - 10*60*60*1000).toISOString(), value: 100 },
      { timestamp: new Date(Date.now() - 9*60*60*1000).toISOString(), value: 100 },
      { timestamp: new Date(Date.now() - 8*60*60*1000).toISOString(), value: 100 },
      { timestamp: new Date(Date.now() - 7*60*60*1000).toISOString(), value: 100 },
      { timestamp: new Date(Date.now() - 6*60*60*1000).toISOString(), value: 100 },
      { timestamp: new Date(Date.now() - 5*60*60*1000).toISOString(), value: 100 },
      { timestamp: new Date(Date.now() - 4*60*60*1000).toISOString(), value: 100 },
      { timestamp: new Date(Date.now() - 3*60*60*1000).toISOString(), value: 100 },
      { timestamp: new Date(Date.now() - 2*60*60*1000).toISOString(), value: 100 },
      { timestamp: new Date(Date.now() - 1*60*60*1000).toISOString(), value: 100 },
      { timestamp: new Date().toISOString(), value: 100 }
    ],
    speedChartData: [
      { timestamp: new Date(Date.now() - 6*60*60*1000).toISOString(), value: 118.2 },
      { timestamp: new Date(Date.now() - 5*60*60*1000).toISOString(), value: 125.8 },
      { timestamp: new Date(Date.now() - 4*60*60*1000).toISOString(), value: 132.1 },
      { timestamp: new Date(Date.now() - 3*60*60*1000).toISOString(), value: 128.9 },
      { timestamp: new Date(Date.now() - 2*60*60*1000).toISOString(), value: 115.4 },
      { timestamp: new Date(Date.now() - 1*60*60*1000).toISOString(), value: 142.7 },
      { timestamp: new Date().toISOString(), value: 128.4 }
    ]
  }), []); // Empty dependency array means this will only be calculated once

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/dashboard');
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
        setUsingRealData(true);
        return true;
      } else {
        throw new Error('API not available');
      }
    } catch (error) {
      console.log('Backend not available, using demo data');
      setDashboardData(demoData.dashboardData);
      setUsingRealData(false);
      return false;
    }
  };

  const fetchChartData = async () => {
    try {
      const [uptimeResponse, speedResponse] = await Promise.all([
        fetch('/api/charts/uptime?hours=24'),
        fetch('/api/charts/speed?hours=24&metric=download')
      ]);
      
      if (uptimeResponse.ok && speedResponse.ok) {
        const uptimeData = await uptimeResponse.json();
        const speedData = await speedResponse.json();
        
        setUptimeChartData(uptimeData);
        setSpeedChartData(speedData);
        setUsingRealData(true);
      } else {
        throw new Error('API not available');
      }
    } catch (error) {
      console.log('Chart API not available, using demo data');
      setUptimeChartData(demoData.uptimeChartData);
      setSpeedChartData(demoData.speedChartData);
      setUsingRealData(false);
    }
  };

  const refreshData = async () => {
    setLoading(true);
    await Promise.all([fetchDashboardData(), fetchChartData()]);
    setLastUpdated(new Date());
    setLoading(false);
  };

  useEffect(() => {
    refreshData();
    
    // Auto-refresh every 2 minutes instead of 30 seconds to reduce CPU usage
    const interval = setInterval(refreshData, 120000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !dashboardData) {
    return (
      <div className="flex-1 p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          <div className="loading-skeleton h-8 w-64"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="loading-skeleton h-32"></div>
            ))}
          </div>
          <div className="loading-skeleton h-96"></div>
        </div>
      </div>
    );
  }

  const getUptimeStatus = (uptime) => {
    if (uptime >= 99) return 'good';
    if (uptime >= 95) return 'warning';
    return 'error';
  };

  const getSpeedStatus = (speed) => {
    if (!speed) return 'normal';
    if (speed >= 50) return 'good';
    if (speed >= 10) return 'warning';
    return 'error';
  };

  return (
    <div className="flex-1 overflow-auto custom-scrollbar">
      <div className="p-8">
        <div className="max-w-7xl mx-auto space-y-8">
          {/* Connection Status Banner */}
          <div className={`rounded-lg p-4 border ${
            usingRealData 
              ? 'bg-green-50 border-green-200' 
              : 'bg-blue-50 border-blue-200'
          }`}>
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                  usingRealData ? 'bg-green-600' : 'bg-blue-600'
                }`}>
                  <span className="text-white text-sm font-medium">
                    {usingRealData ? '🌐' : '✨'}
                  </span>
                </div>
              </div>
              <div className="ml-3">
                <h3 className={`text-sm font-medium ${
                  usingRealData ? 'text-green-800' : 'text-blue-800'
                }`}>
                  {usingRealData ? 'Live Monitoring Active' : 'Demo Mode'}
                </h3>
                <p className={`text-sm ${
                  usingRealData ? 'text-green-600' : 'text-blue-600'
                }`}>
                  {usingRealData 
                    ? 'Showing real-time data from your internet connection'
                    : 'Backend starting up... Using sample data for now'
                  }
                </p>
              </div>
            </div>
          </div>

          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Internet Monitor Dashboard</h1>
              <p className="text-gray-500 mt-1">
                {usingRealData 
                  ? 'Real-time monitoring of your internet connection and performance'
                  : 'Demo interface - Connect backend for live monitoring'
                }
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-500">
                Last updated: {format(lastUpdated, 'HH:mm:ss')}
              </div>
              <button 
                onClick={refreshData}
                className="btn-secondary"
                disabled={loading}
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                {usingRealData ? 'Refresh Data' : 'Check Backend'}
              </button>
            </div>
          </div>

          {/* Status Overview */}
          <div className="notion-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Current Status</h2>
                <p className="text-gray-500">
                  {usingRealData 
                    ? 'Your internet connection status right now'
                    : 'Sample connection status'
                  }
                </p>
              </div>
              <StatusIndicator status={dashboardData.current_status} size="lg" />
            </div>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard
              title="24h Uptime"
              value={dashboardData.uptime_24h}
              unit="%"
              icon={Wifi}
              status={getUptimeStatus(dashboardData.uptime_24h)}
            />
            
            <MetricCard
              title="Average Speed"
              value={dashboardData.avg_speed_24h || 0}
              unit="Mbps"
              icon={Zap}
              status={getSpeedStatus(dashboardData.avg_speed_24h)}
            />
            
            <MetricCard
              title="Current Latency"
              value={dashboardData.current_latency || 0}
              unit="ms"
              icon={Clock}
              status={dashboardData.current_latency > 100 ? 'warning' : 'good'}
            />
            
            <MetricCard
              title="Outages (24h)"
              value={dashboardData.total_outages_24h}
              icon={AlertTriangle}
              status={dashboardData.total_outages_24h > 0 ? 'error' : 'good'}
            />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Uptime Chart */}
            <div className="chart-container">
              <div className="chart-header">
                <h3 className="text-lg font-semibold text-gray-900">24-Hour Uptime</h3>
                <div className="text-sm text-gray-500">
                  {usingRealData ? 'Live data' : 'Sample data'}
                </div>
              </div>
              <div className="chart-content">
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={uptimeChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis 
                      dataKey="timestamp" 
                      tickFormatter={(value) => format(new Date(value), 'HH:mm')}
                      stroke="#6b7280"
                    />
                    <YAxis 
                      domain={[0, 100]}
                      stroke="#6b7280"
                    />
                    <Tooltip 
                      labelFormatter={(value) => format(new Date(value), 'MMM dd, HH:mm')}
                      formatter={(value) => [`${value.toFixed(1)}%`, 'Uptime']}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#3b82f6" 
                      fill="#dbeafe"
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Speed Chart */}
            <div className="chart-container">
              <div className="chart-header">
                <h3 className="text-lg font-semibold text-gray-900">Download Speed</h3>
                <div className="text-sm text-gray-500">
                  {usingRealData ? 'Live speed tests' : 'Sample tests'}
                </div>
              </div>
              <div className="chart-content">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={speedChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis 
                      dataKey="timestamp" 
                      tickFormatter={(value) => format(new Date(value), 'HH:mm')}
                      stroke="#6b7280"
                    />
                    <YAxis stroke="#6b7280" />
                    <Tooltip 
                      labelFormatter={(value) => format(new Date(value), 'MMM dd, HH:mm')}
                      formatter={(value) => [`${value.toFixed(1)} Mbps`, 'Download Speed']}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#10b981" 
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Recent Speed Test */}
          {dashboardData.last_speed_test && (
            <div className="notion-card p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                {usingRealData ? 'Latest Speed Test' : 'Sample Speed Test Results'}
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {dashboardData.last_speed_test.download_mbps?.toFixed(1) || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-500">Download (Mbps)</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {dashboardData.last_speed_test.upload_mbps?.toFixed(1) || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-500">Upload (Mbps)</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-600">
                    {dashboardData.last_speed_test.ping_ms?.toFixed(0) || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-500">Ping (ms)</div>
                </div>
              </div>
              {dashboardData.last_speed_test.server_location && (
                <div className="mt-4 text-sm text-gray-500 text-center">
                  Server: {dashboardData.last_speed_test.server_location}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;