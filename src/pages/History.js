import React, { useState, useEffect } from 'react';
import { Calendar, Clock, Wifi, Zap, Filter } from 'lucide-react';
import { format, subDays } from 'date-fns';
import StatusIndicator from '../components/StatusIndicator';

const History = () => {
  const [connectivityData, setConnectivityData] = useState([]);
  const [speedTestData, setSpeedTestData] = useState([]);
  const [outageData, setOutageData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('24'); // hours
  const [activeTab, setActiveTab] = useState('connectivity');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [connectivityResponse, speedResponse, outageResponse] = await Promise.all([
        fetch(`/api/connectivity?hours=${timeRange}`),
        fetch(`/api/speed-tests?hours=${timeRange}`),
        fetch(`/api/outages?days=${Math.ceil(timeRange / 24)}`)
      ]);

      const connectivity = await connectivityResponse.json();
      const speed = await speedResponse.json();
      const outages = await outageResponse.json();

      setConnectivityData(connectivity);
      setSpeedTestData(speed);
      setOutageData(outages);
    } catch (error) {
      console.error('Error fetching history data:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, [timeRange]);

  const formatDuration = (seconds) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h`;
  };

  const ConnectivityTable = () => (
    <div className="table-container">
      <div className="notion-card-header">
        <h3 className="text-lg font-semibold text-gray-900">Connectivity Tests</h3>
        <p className="text-sm text-gray-500">Recent connectivity test results</p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="table-header">Time</th>
              <th className="table-header">Host</th>
              <th className="table-header">Status</th>
              <th className="table-header">Latency</th>
              <th className="table-header">Type</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {connectivityData.slice(0, 50).map((test) => (
              <tr key={test.id} className="table-row">
                <td className="table-cell">
                  {format(new Date(test.timestamp), 'MMM dd, HH:mm:ss')}
                </td>
                <td className="table-cell font-mono text-sm">
                  {test.target_host}
                </td>
                <td className="table-cell">
                  <StatusIndicator 
                    status={test.is_connected ? 'connected' : 'disconnected'} 
                    size="sm" 
                  />
                </td>
                <td className="table-cell">
                  {test.latency_ms ? `${test.latency_ms.toFixed(1)}ms` : 'N/A'}
                </td>
                <td className="table-cell">
                  <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">
                    {test.test_type.toUpperCase()}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const SpeedTestTable = () => (
    <div className="table-container">
      <div className="notion-card-header">
        <h3 className="text-lg font-semibold text-gray-900">Speed Tests</h3>
        <p className="text-sm text-gray-500">Internet speed test results</p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="table-header">Time</th>
              <th className="table-header">Download</th>
              <th className="table-header">Upload</th>
              <th className="table-header">Ping</th>
              <th className="table-header">Server</th>
              <th className="table-header">Status</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {speedTestData.map((test) => (
              <tr key={test.id} className="table-row">
                <td className="table-cell">
                  {format(new Date(test.timestamp), 'MMM dd, HH:mm:ss')}
                </td>
                <td className="table-cell">
                  <span className="font-semibold text-blue-600">
                    {test.download_mbps ? `${test.download_mbps.toFixed(1)} Mbps` : 'N/A'}
                  </span>
                </td>
                <td className="table-cell">
                  <span className="font-semibold text-green-600">
                    {test.upload_mbps ? `${test.upload_mbps.toFixed(1)} Mbps` : 'N/A'}
                  </span>
                </td>
                <td className="table-cell">
                  {test.ping_ms ? `${test.ping_ms.toFixed(0)}ms` : 'N/A'}
                </td>
                <td className="table-cell text-xs">
                  {test.server_location || 'Unknown'}
                </td>
                <td className="table-cell">
                  <StatusIndicator 
                    status={test.success ? 'connected' : 'disconnected'} 
                    size="sm" 
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const OutageTable = () => (
    <div className="table-container">
      <div className="notion-card-header">
        <h3 className="text-lg font-semibold text-gray-900">Outage Events</h3>
        <p className="text-sm text-gray-500">Detected internet outages and disruptions</p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="table-header">Start Time</th>
              <th className="table-header">End Time</th>
              <th className="table-header">Duration</th>
              <th className="table-header">Severity</th>
              <th className="table-header">Status</th>
              <th className="table-header">Description</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {outageData.map((outage) => (
              <tr key={outage.id} className="table-row">
                <td className="table-cell">
                  {format(new Date(outage.start_time), 'MMM dd, HH:mm:ss')}
                </td>
                <td className="table-cell">
                  {outage.end_time 
                    ? format(new Date(outage.end_time), 'MMM dd, HH:mm:ss')
                    : 'Ongoing'
                  }
                </td>
                <td className="table-cell">
                  {outage.duration_seconds 
                    ? formatDuration(outage.duration_seconds)
                    : 'Ongoing'
                  }
                </td>
                <td className="table-cell">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    outage.severity === 'complete' ? 'bg-red-100 text-red-800' :
                    outage.severity === 'partial' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-orange-100 text-orange-800'
                  }`}>
                    {outage.severity}
                  </span>
                </td>
                <td className="table-cell">
                  <StatusIndicator 
                    status={outage.is_resolved ? 'connected' : 'disconnected'} 
                    size="sm" 
                  />
                </td>
                <td className="table-cell text-sm">
                  {outage.description || 'No description'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex-1 p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          <div className="loading-skeleton h-8 w-64"></div>
          <div className="loading-skeleton h-96"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto custom-scrollbar">
      <div className="p-8">
        <div className="max-w-7xl mx-auto space-y-8">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Monitoring History</h1>
              <p className="text-gray-500 mt-1">
                Detailed history of connectivity tests, speed tests, and outages
              </p>
            </div>
            
            {/* Time Range Filter */}
            <div className="flex items-center space-x-4">
              <Filter className="w-5 h-5 text-gray-400" />
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="btn-secondary"
              >
                <option value="1">Last Hour</option>
                <option value="24">Last 24 Hours</option>
                <option value="168">Last Week</option>
                <option value="720">Last Month</option>
              </select>
            </div>
          </div>

          {/* Tabs */}
          <div className="notion-card p-0">
            <div className="border-b border-gray-200">
              <nav className="flex space-x-8 px-6 py-4">
                {[
                  { id: 'connectivity', label: 'Connectivity', icon: Wifi, count: connectivityData.length },
                  { id: 'speed', label: 'Speed Tests', icon: Zap, count: speedTestData.length },
                  { id: 'outages', label: 'Outages', icon: Clock, count: outageData.length }
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center py-2 px-1 border-b-2 text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <tab.icon className="w-4 h-4 mr-2" />
                    {tab.label}
                    <span className="ml-2 bg-gray-100 text-gray-600 px-2 py-1 rounded-full text-xs">
                      {tab.count}
                    </span>
                  </button>
                ))}
              </nav>
            </div>
          </div>

          {/* Tab Content */}
          <div>
            {activeTab === 'connectivity' && <ConnectivityTable />}
            {activeTab === 'speed' && <SpeedTestTable />}
            {activeTab === 'outages' && <OutageTable />}
          </div>
        </div>
      </div>
    </div>
  );
};

export default History;