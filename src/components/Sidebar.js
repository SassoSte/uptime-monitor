import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Home, 
  Activity, 
  FileText, 
  Settings, 
  Wifi, 
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock
} from 'lucide-react';

const Sidebar = () => {
  const [healthStatus, setHealthStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchHealthStatus = async () => {
    try {
      const response = await fetch('/api/health');
      if (response.ok) {
        const data = await response.json();
        setHealthStatus(data);
      } else {
        setHealthStatus({
          status: 'error',
          monitoring_service: { active: false, message: 'Health check failed' }
        });
      }
    } catch (error) {
      setHealthStatus({
        status: 'error',
        monitoring_service: { active: false, message: 'Cannot connect to backend' }
      });
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchHealthStatus();
    // Check health status every 30 seconds
    const interval = setInterval(fetchHealthStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = () => {
    if (loading) return <Clock className="w-4 h-4 mr-2 animate-spin" />;
    
    switch (healthStatus?.status) {
      case 'healthy':
        return <CheckCircle className="w-4 h-4 mr-2 text-green-400" />;
      case 'warning':
        return <AlertCircle className="w-4 h-4 mr-2 text-yellow-400" />;
      case 'error':
      default:
        return <AlertCircle className="w-4 h-4 mr-2 text-red-400" />;
    }
  };

  const getStatusText = () => {
    if (loading) return 'Checking Status...';
    
    if (healthStatus?.monitoring_service?.active) {
      return 'Monitoring Active';
    } else {
      return 'Monitoring Inactive';
    }
  };

  const getStatusDot = () => {
    if (loading) return 'bg-gray-400 animate-pulse';
    
    switch (healthStatus?.status) {
      case 'healthy':
        return 'bg-green-400 animate-pulse';
      case 'warning':
        return 'bg-yellow-400 animate-pulse';
      case 'error':
      default:
        return 'bg-red-400';
    }
  };

  const navItems = [
    { to: '/', icon: Home, label: 'Dashboard' },
    { to: '/history', icon: Activity, label: 'History' },
    { to: '/reports', icon: FileText, label: 'Reports' },
    { to: '/settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="flex items-center px-6 py-4 border-b border-gray-200">
        <div className="flex items-center">
          <div className="flex items-center justify-center w-8 h-8 bg-blue-600 rounded-lg">
            <Wifi className="w-5 h-5 text-white" />
          </div>
          <div className="ml-3">
            <h1 className="text-lg font-semibold text-gray-900">UpTime Monitor</h1>
            <p className="text-xs text-gray-500">Internet Monitoring</p>
          </div>
        </div>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `nav-item ${isActive ? 'active' : 'text-gray-600'}`
            }
          >
            <item.icon className="w-5 h-5 mr-3" />
            {item.label}
          </NavLink>
        ))}
      </nav>
      
      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <div 
          className="flex items-center text-xs text-gray-500 cursor-pointer hover:text-gray-700" 
          title={healthStatus?.monitoring_service?.message || 'Loading...'}
        >
          {getStatusIcon()}
          <span>{getStatusText()}</span>
          <div className={`ml-auto w-2 h-2 rounded-full ${getStatusDot()}`}></div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;