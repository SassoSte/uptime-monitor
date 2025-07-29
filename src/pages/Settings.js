import React, { useState, useEffect } from 'react';
import { Save, RefreshCw, Server, Clock, Target, Database, Bell } from 'lucide-react';
import toast from 'react-hot-toast';

const Settings = () => {
  const [config, setConfig] = useState({
    monitoring: {
      ping_interval_seconds: 30,
      speed_test_interval_minutes: 15,
      connectivity_timeout_seconds: 10,
      max_retries: 3
    },
    targets: {
      ping_hosts: ['8.8.8.8', '1.1.1.1', 'google.com'],
      dns_servers: ['8.8.8.8', '1.1.1.1']
    },
    database: {
      retention_days: 90
    },
    alerts: {
      outage_threshold_seconds: 60,
      slow_speed_threshold_mbps: 10
    }
  });
  
  const [loading, setLoading] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  const updateConfig = (section, key, value) => {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }));
    setHasChanges(true);
  };

  const updateArrayConfig = (section, key, index, value) => {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: prev[section][key].map((item, i) => i === index ? value : item)
      }
    }));
    setHasChanges(true);
  };

  const addArrayItem = (section, key, defaultValue = '') => {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: [...prev[section][key], defaultValue]
      }
    }));
    setHasChanges(true);
  };

  const removeArrayItem = (section, key, index) => {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: prev[section][key].filter((_, i) => i !== index)
      }
    }));
    setHasChanges(true);
  };

  const saveConfig = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save configuration');
      }

      setHasChanges(false);
      toast.success('Settings saved successfully!');
    } catch (error) {
      toast.error(`Failed to save settings: ${error.message}`);
      console.error('Error saving config:', error);
    }
    setLoading(false);
  };

  const resetConfig = () => {
    const defaultConfig = {
      monitoring: {
        ping_interval_seconds: 30,
        speed_test_interval_minutes: 15,
        connectivity_timeout_seconds: 10,
        max_retries: 3
      },
      targets: {
        ping_hosts: ['8.8.8.8', '1.1.1.1', 'google.com'],
        dns_servers: ['8.8.8.8', '1.1.1.1']
      },
      database: {
        retention_days: 90
      },
      alerts: {
        outage_threshold_seconds: 60,
        slow_speed_threshold_mbps: 10
      }
    };
    setConfig(defaultConfig);
    setHasChanges(true);
    toast.success('Settings reset to defaults');
  };

  useEffect(() => {
    // Load config from backend API
    const loadConfig = async () => {
      try {
        const response = await fetch('/api/config');
        if (response.ok) {
          const serverConfig = await response.json();
          setConfig(serverConfig);
        } else {
          console.error('Failed to load config from server');
          // Keep the default config that's already set
        }
      } catch (error) {
        console.error('Error loading config from server:', error);
        // Keep the default config that's already set
      }
    };

    loadConfig();
  }, []);

  return (
    <div className="flex-1 overflow-auto custom-scrollbar">
      <div className="p-8">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
              <p className="text-gray-500 mt-1">
                Configure monitoring parameters and system settings
              </p>
            </div>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={resetConfig}
                className="btn-secondary"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Reset to Defaults
              </button>
              
              <button
                onClick={saveConfig}
                disabled={!hasChanges || loading}
                className="btn-primary"
              >
                <Save className="w-4 h-4 mr-2" />
                {loading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>

          {/* Monitoring Settings */}
          <div className="notion-card">
            <div className="notion-card-header">
              <div className="flex items-center">
                <Clock className="w-5 h-5 text-blue-600 mr-3" />
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Monitoring Configuration</h2>
                  <p className="text-sm text-gray-500">Configure monitoring intervals and timeouts</p>
                </div>
              </div>
            </div>
            
            <div className="notion-card-content space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Ping Interval (seconds)
                  </label>
                  <input
                    type="number"
                    min="10"
                    max="300"
                    value={config.monitoring.ping_interval_seconds}
                    onChange={(e) => updateConfig('monitoring', 'ping_interval_seconds', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">How often to ping test hosts</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Speed Test Interval (minutes)
                  </label>
                  <input
                    type="number"
                    min="5"
                    max="120"
                    value={config.monitoring.speed_test_interval_minutes}
                    onChange={(e) => updateConfig('monitoring', 'speed_test_interval_minutes', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">How often to run speed tests</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Connection Timeout (seconds)
                  </label>
                  <input
                    type="number"
                    min="5"
                    max="30"
                    value={config.monitoring.connectivity_timeout_seconds}
                    onChange={(e) => updateConfig('monitoring', 'connectivity_timeout_seconds', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Timeout for connectivity tests</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Retries
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={config.monitoring.max_retries}
                    onChange={(e) => updateConfig('monitoring', 'max_retries', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Retry attempts for failed tests</p>
                </div>
              </div>
            </div>
          </div>

          {/* Target Hosts */}
          <div className="notion-card">
            <div className="notion-card-header">
              <div className="flex items-center">
                <Target className="w-5 h-5 text-green-600 mr-3" />
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Target Hosts</h2>
                  <p className="text-sm text-gray-500">Configure hosts and servers for testing</p>
                </div>
              </div>
            </div>
            
            <div className="notion-card-content space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Ping Test Hosts
                </label>
                <div className="space-y-2">
                  {config.targets.ping_hosts.map((host, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <input
                        type="text"
                        value={host}
                        onChange={(e) => updateArrayConfig('targets', 'ping_hosts', index, e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Host or IP address"
                      />
                      <button
                        onClick={() => removeArrayItem('targets', 'ping_hosts', index)}
                        className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-md"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={() => addArrayItem('targets', 'ping_hosts', '')}
                    className="btn-secondary"
                  >
                    Add Host
                  </button>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  DNS Servers
                </label>
                <div className="space-y-2">
                  {config.targets.dns_servers.map((server, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <input
                        type="text"
                        value={server}
                        onChange={(e) => updateArrayConfig('targets', 'dns_servers', index, e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="DNS server IP"
                      />
                      <button
                        onClick={() => removeArrayItem('targets', 'dns_servers', index)}
                        className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-md"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={() => addArrayItem('targets', 'dns_servers', '')}
                    className="btn-secondary"
                  >
                    Add DNS Server
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Database Settings */}
          <div className="notion-card">
            <div className="notion-card-header">
              <div className="flex items-center">
                <Database className="w-5 h-5 text-purple-600 mr-3" />
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Database Configuration</h2>
                  <p className="text-sm text-gray-500">Data retention and storage settings</p>
                </div>
              </div>
            </div>
            
            <div className="notion-card-content">
              <div className="max-w-md">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Data Retention (days)
                </label>
                <input
                  type="number"
                  min="7"
                  max="365"
                  value={config.database.retention_days}
                  onChange={(e) => updateConfig('database', 'retention_days', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">How long to keep monitoring data</p>
              </div>
            </div>
          </div>

          {/* Database Management */}
          <div className="notion-card">
            <div className="notion-card-header">
              <div className="flex items-center">
                <Server className="w-5 h-5 text-red-600 mr-3" />
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Database Management</h2>
                  <p className="text-sm text-gray-500">Manual database maintenance operations</p>
                </div>
              </div>
            </div>
            
            <div className="notion-card-content space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <Database className="w-5 h-5 text-blue-600 mt-0.5" />
                  </div>
                  <div className="ml-3 flex-1">
                    <h3 className="text-sm font-medium text-blue-800">Database Cleanup</h3>
                    <p className="text-sm text-blue-700 mt-1">
                      Remove monitoring data older than {config.database.retention_days} days. 
                      The system automatically cleans up data daily, but you can trigger manual cleanup here.
                    </p>
                    <div className="mt-3">
                      <button
                        onClick={async () => {
                          if (window.confirm(`This will permanently delete monitoring data older than ${config.database.retention_days} days. Continue?`)) {
                            try {
                              toast.loading('Cleaning up database...', { id: 'cleanup' });
                              const response = await fetch('/api/cleanup', { method: 'POST' });
                              const result = await response.json();
                              
                              if (response.ok) {
                                toast.success(
                                  `Cleanup completed! Removed ${result.deleted_records.total} old records.`,
                                  { id: 'cleanup', duration: 5000 }
                                );
                              } else {
                                throw new Error(result.detail || 'Cleanup failed');
                              }
                            } catch (error) {
                              toast.error(`Cleanup failed: ${error.message}`, { id: 'cleanup' });
                            }
                          }
                        }}
                        className="btn-secondary text-sm"
                      >
                        <Database className="w-4 h-4 mr-2" />
                        Clean Up Database Now
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Alert Settings */}
          <div className="notion-card">
            <div className="notion-card-header">
              <div className="flex items-center">
                <Bell className="w-5 h-5 text-orange-600 mr-3" />
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Alert Thresholds</h2>
                  <p className="text-sm text-gray-500">Configure when to trigger alerts</p>
                </div>
              </div>
            </div>
            
            <div className="notion-card-content">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Outage Threshold (seconds)
                  </label>
                  <input
                    type="number"
                    min="10"
                    max="300"
                    value={config.alerts.outage_threshold_seconds}
                    onChange={(e) => updateConfig('alerts', 'outage_threshold_seconds', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Minimum duration to consider an outage</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Slow Speed Threshold (Mbps)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={config.alerts.slow_speed_threshold_mbps}
                    onChange={(e) => updateConfig('alerts', 'slow_speed_threshold_mbps', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Speed below which to alert</p>
                </div>
              </div>
            </div>
          </div>

          {/* Status */}
          {hasChanges && (
            <div className="notion-card p-4 bg-yellow-50 border-yellow-200">
              <p className="text-sm text-yellow-800">
                You have unsaved changes. Click "Save Changes" to apply your settings.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;