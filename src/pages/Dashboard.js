import React, { useState, useEffect, useMemo } from 'react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Wifi, Zap, Clock, AlertTriangle, RefreshCw, Shield } from 'lucide-react';
import MetricCard from '../components/MetricCard';
import StatusIndicator from '../components/StatusIndicator';
import VPNDashboard from '../components/VPNDashboard';
import { format } from 'date-fns';

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [uptimeChartData, setUptimeChartData] = useState([]);
  const [speedChartData, setSpeedChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [usingRealData, setUsingRealData] = useState(false);
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' or 'vpn'

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
      },
      vpn_status: {
        is_active: false,
        provider: null,
        public_ip: '192.168.1.100',
        confidence: 0.95,
        detection_method: 'ip'
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
        return true;
      } else {
        throw new Error('Chart API not available');
      }
    } catch (error) {
      console.log('Chart API not available, using demo data');
      setUptimeChartData(demoData.uptimeChartData);
      setSpeedChartData(demoData.speedChartData);
      setUsingRealData(false);
      return false;
    }
  };

  const refreshData = async () => {
    setLoading(true);
    setLastUpdated(new Date());
    
    const dashboardSuccess = await fetchDashboardData();
    const chartSuccess = await fetchChartData();
    
    setLoading(false);
    
    if (!dashboardSuccess && !chartSuccess) {
      // If both failed, we're definitely using demo data
      setUsingRealData(false);
    }
  };

  useEffect(() => {
    refreshData();
    
    // Set up auto-refresh every 30 seconds
    const interval = setInterval(refreshData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getUptimeStatus = (uptime) => {
    if (uptime >= 99) return 'excellent';
    if (uptime >= 95) return 'good';
    if (uptime >= 90) return 'fair';
    return 'poor';
  };

  const getSpeedStatus = (speed) => {
    if (speed >= 100) return 'excellent';
    if (speed >= 50) return 'good';
    if (speed >= 25) return 'fair';
    return 'poor';
  };

  const getVPNStatusColor = (isActive) => {
    return isActive ? 'text-green-600' : 'text-gray-600';
  };

  const getVPNStatusIcon = (isActive) => {
    return isActive ? '🔒' : '🔓';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-32 bg-gray-200 rounded"></div>
              ))}
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="h-80 bg-gray-200 rounded"></div>
              <div className="h-80 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Network Monitor</h1>
            <p className="text-gray-600 mt-1">
              Real-time monitoring of your internet connection
              {!usingRealData && (
                <span className="ml-2 text-orange-600 text-sm">
                  (Demo Mode - Backend not connected)
                </span>
              )}
            </p>
          </div>
          <div className="flex items-center space-x-4 mt-4 sm:mt-0">
            <div className="text-sm text-gray-500">
              Last updated: {format(lastUpdated, 'HH:mm:ss')}
            </div>
            <button
              onClick={refreshData}
              disabled={loading}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1 bg-white rounded-lg p-1 mb-6 shadow-sm">
          <button
            onClick={() => setActiveTab('overview')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'overview'
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <Wifi className="w-4 h-4" />
            <span>Overview</span>
          </button>
          <button
            onClick={() => setActiveTab('vpn')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'vpn'
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <Shield className="w-4 h-4" />
            <span>VPN Monitor</span>
          </button>
        </div>

        {activeTab === 'overview' ? (
          <>
            {/* Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <MetricCard
                title="Connection Status"
                value={dashboardData?.current_status || 'unknown'}
                icon={<Wifi className="w-6 h-6" />}
                status={dashboardData?.current_status === 'connected' ? 'good' : 'poor'}
                subtitle={`Latency: ${dashboardData?.current_latency?.toFixed(1) || 'N/A'} ms`}
              />
              
              <MetricCard
                title="24h Uptime"
                value={`${dashboardData?.uptime_24h?.toFixed(1) || 0}%`}
                icon={<Clock className="w-6 h-6" />}
                status={getUptimeStatus(dashboardData?.uptime_24h || 0)}
                subtitle={`${dashboardData?.total_outages_24h || 0} outages`}
              />
              
              <MetricCard
                title="Avg Speed"
                value={`${dashboardData?.avg_speed_24h?.toFixed(1) || 0} Mbps`}
                icon={<Zap className="w-6 h-6" />}
                status={getSpeedStatus(dashboardData?.avg_speed_24h || 0)}
                subtitle="Download speed"
              />

              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <Shield className="w-6 h-6 text-gray-600" />
                    <h3 className="text-lg font-semibold text-gray-800">VPN Status</h3>
                  </div>
                </div>
                
                {dashboardData?.vpn_status ? (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Status:</span>
                      <span className={`font-semibold ${getVPNStatusColor(dashboardData.vpn_status.is_active)}`}>
                        {getVPNStatusIcon(dashboardData.vpn_status.is_active)} {dashboardData.vpn_status.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    
                    {dashboardData.vpn_status.provider && (
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Provider:</span>
                        <span className="font-semibold text-gray-800">
                          {dashboardData.vpn_status.provider.toUpperCase()}
                        </span>
                      </div>
                    )}
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Confidence:</span>
                      <span className="font-semibold text-gray-800">
                        {(dashboardData.vpn_status.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-gray-500 py-4">
                    No VPN data available
                  </div>
                )}
              </div>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Uptime Trend (24h)</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={uptimeChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="timestamp" 
                      tickFormatter={(value) => format(new Date(value), 'HH:mm')}
                    />
                    <YAxis domain={[0, 100]} />
                    <Tooltip 
                      labelFormatter={(value) => format(new Date(value), 'HH:mm:ss')}
                      formatter={(value) => [`${value}%`, 'Uptime']}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#3B82F6" 
                      fill="#3B82F6" 
                      fillOpacity={0.3}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Speed Trend (24h)</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={speedChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="timestamp" 
                      tickFormatter={(value) => format(new Date(value), 'HH:mm')}
                    />
                    <YAxis />
                    <Tooltip 
                      labelFormatter={(value) => format(new Date(value), 'HH:mm:ss')}
                      formatter={(value) => [`${value} Mbps`, 'Speed']}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#10B981" 
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Last Speed Test */}
            {dashboardData?.last_speed_test && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Last Speed Test</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600">
                      {dashboardData.last_speed_test.download_mbps.toFixed(1)}
                    </div>
                    <div className="text-sm text-gray-600">Download (Mbps)</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">
                      {dashboardData.last_speed_test.upload_mbps.toFixed(1)}
                    </div>
                    <div className="text-sm text-gray-600">Upload (Mbps)</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-purple-600">
                      {dashboardData.last_speed_test.ping_ms.toFixed(1)}
                    </div>
                    <div className="text-sm text-gray-600">Ping (ms)</div>
                  </div>
                </div>
                <div className="mt-4 text-center text-sm text-gray-600">
                  Server: {dashboardData.last_speed_test.server_location}
                </div>
              </div>
            )}
          </>
        ) : (
          <VPNDashboard />
        )}
      </div>
    </div>
  );
};

export default Dashboard;