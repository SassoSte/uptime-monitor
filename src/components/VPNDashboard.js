import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const VPNDashboard = () => {
  const [vpnStatus, setVpnStatus] = useState(null);
  const [vpnStats, setVpnStats] = useState(null);
  const [vpnHistory, setVpnHistory] = useState([]);
  const [speedImpact, setSpeedImpact] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchVPNData();
    const interval = setInterval(fetchVPNData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchVPNData = async () => {
    try {
      setLoading(true);
      const [statusRes, statsRes, historyRes, impactRes] = await Promise.all([
        fetch('/api/vpn/status'),
        fetch('/api/vpn/stats?hours=24'),
        fetch('/api/vpn/history?hours=24'),
        fetch('/api/vpn/speed-impact?hours=24')
      ]);

      if (statusRes.ok) {
        const statusData = await statusRes.json();
        setVpnStatus(statusData);
      }

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setVpnStats(statsData);
      }

      if (historyRes.ok) {
        const historyData = await historyRes.json();
        setVpnHistory(historyData);
      }

      if (impactRes.ok) {
        const impactData = await impactRes.json();
        setSpeedImpact(impactData);
      }

      setError(null);
    } catch (err) {
      setError('Failed to fetch VPN data');
      console.error('VPN data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getVPNStatusColor = (isActive) => {
    return isActive ? 'text-green-600' : 'text-gray-600';
  };

  const getVPNStatusIcon = (isActive) => {
    return isActive ? '🔒' : '🔓';
  };

  const formatDuration = (minutes) => {
    if (minutes < 60) return `${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  const formatConfidence = (confidence) => {
    return `${(confidence * 100).toFixed(0)}%`;
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const prepareChartData = () => {
    if (!vpnHistory.length) return null;

    const labels = vpnHistory.slice(-48).map(entry => 
      new Date(entry.timestamp).toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    );

    const data = vpnHistory.slice(-48).map(entry => entry.is_active ? 1 : 0);

    return {
      labels,
      datasets: [
        {
          label: 'VPN Status',
          data,
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.1,
          pointRadius: 0,
        },
      ],
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: 'VPN Status Over Time',
        color: '#374151',
        font: {
          size: 14,
          weight: 'bold',
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 1,
        ticks: {
          stepSize: 1,
          callback: function(value) {
            return value === 1 ? 'Active' : 'Inactive';
          },
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
      },
      x: {
        grid: {
          display: false,
        },
        ticks: {
          maxTicksLimit: 8,
        },
      },
    },
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center text-red-600">
          <div className="text-2xl mb-2">⚠️</div>
          <div className="font-semibold">{error}</div>
          <button 
            onClick={fetchVPNData}
            className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Current VPN Status */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Current VPN Status</h2>
        
        {vpnStatus ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Status</p>
                  <p className={`text-lg font-semibold ${getVPNStatusColor(vpnStatus.is_active)}`}>
                    {getVPNStatusIcon(vpnStatus.is_active)} {vpnStatus.is_active ? 'Active' : 'Inactive'}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div>
                <p className="text-sm text-gray-600">Provider</p>
                <p className="text-lg font-semibold text-gray-800">
                  {vpnStatus.provider ? vpnStatus.provider.toUpperCase() : 'Unknown'}
                </p>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div>
                <p className="text-sm text-gray-600">Public IP</p>
                <p className="text-lg font-semibold text-gray-800 font-mono">
                  {vpnStatus.public_ip || 'Unknown'}
                </p>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div>
                <p className="text-sm text-gray-600">Confidence</p>
                <p className={`text-lg font-semibold ${getConfidenceColor(vpnStatus.confidence)}`}>
                  {formatConfidence(vpnStatus.confidence)}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center text-gray-500 py-8">
            No VPN status data available
          </div>
        )}
      </div>

      {/* VPN Usage Statistics */}
      {vpnStats && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">24-Hour VPN Usage</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <div>
                <p className="text-sm text-blue-600">Total Usage</p>
                <p className="text-2xl font-bold text-blue-800">
                  {formatDuration(vpnStats.total_time_minutes)}
                </p>
              </div>
            </div>

            <div className="bg-green-50 rounded-lg p-4">
              <div>
                <p className="text-sm text-green-600">Usage Percentage</p>
                <p className="text-2xl font-bold text-green-800">
                  {vpnStats.usage_percentage.toFixed(1)}%
                </p>
              </div>
            </div>

            <div className="bg-purple-50 rounded-lg p-4">
              <div>
                <p className="text-sm text-purple-600">Connections</p>
                <p className="text-2xl font-bold text-purple-800">
                  {vpnStats.connection_count}
                </p>
              </div>
            </div>

            <div className="bg-orange-50 rounded-lg p-4">
              <div>
                <p className="text-sm text-orange-600">Avg Confidence</p>
                <p className="text-2xl font-bold text-orange-800">
                  {formatConfidence(vpnStats.avg_confidence)}
                </p>
              </div>
            </div>
          </div>

          {vpnStats.providers_used.length > 0 && (
            <div className="mt-4">
              <p className="text-sm text-gray-600 mb-2">Providers Used:</p>
              <div className="flex flex-wrap gap-2">
                {vpnStats.providers_used.map((provider, index) => (
                  <span 
                    key={index}
                    className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                  >
                    {provider.toUpperCase()}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Speed Impact Analysis */}
      {speedImpact && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Speed Impact Analysis</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-red-50 rounded-lg p-4">
              <div>
                <p className="text-sm text-red-600">VPN Tests</p>
                <p className="text-2xl font-bold text-red-800">
                  {speedImpact.vpn_tests_count}
                </p>
              </div>
            </div>

            <div className="bg-green-50 rounded-lg p-4">
              <div>
                <p className="text-sm text-green-600">No VPN Tests</p>
                <p className="text-2xl font-bold text-green-800">
                  {speedImpact.no_vpn_tests_count}
                </p>
              </div>
            </div>

            <div className="bg-blue-50 rounded-lg p-4">
              <div>
                <p className="text-sm text-blue-600">VPN Avg Speed</p>
                <p className="text-2xl font-bold text-blue-800">
                  {speedImpact.vpn_avg_speed_mbps.toFixed(1)} Mbps
                </p>
              </div>
            </div>

            <div className="bg-purple-50 rounded-lg p-4">
              <div>
                <p className="text-sm text-purple-600">No VPN Avg Speed</p>
                <p className="text-2xl font-bold text-purple-800">
                  {speedImpact.no_vpn_avg_speed_mbps.toFixed(1)} Mbps
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-lg font-semibold text-gray-800">Speed Impact</p>
                <p className="text-sm text-gray-600">
                  {speedImpact.impact_description}
                </p>
              </div>
              <div className="text-right">
                <p className={`text-2xl font-bold ${
                  speedImpact.speed_impact_percentage > 15 ? 'text-red-600' : 'text-green-600'
                }`}>
                  {speedImpact.speed_impact_percentage.toFixed(1)}%
                </p>
                <p className="text-sm text-gray-600">reduction</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* VPN Status Chart */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">VPN Status Timeline</h2>
        
        {vpnHistory.length > 0 ? (
          <div className="h-64">
            <Line data={prepareChartData()} options={chartOptions} />
          </div>
        ) : (
          <div className="text-center text-gray-500 py-8">
            No VPN history data available
          </div>
        )}
      </div>

      {/* Recent VPN Events */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Recent VPN Events</h2>
        
        <div className="space-y-2">
          {vpnHistory.slice(0, 10).map((event, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div className="flex items-center space-x-3">
                <span className={`text-lg ${event.is_active ? 'text-green-600' : 'text-gray-400'}`}>
                  {event.is_active ? '🔒' : '🔓'}
                </span>
                <div>
                  <p className="font-medium text-gray-800">
                    {event.is_active ? 'Connected' : 'Disconnected'}
                  </p>
                  <p className="text-sm text-gray-600">
                    {event.provider ? event.provider.toUpperCase() : 'Unknown Provider'}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-600">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </p>
                <p className="text-xs text-gray-500">
                  {new Date(event.timestamp).toLocaleDateString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default VPNDashboard; 