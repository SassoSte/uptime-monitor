import React from 'react';
import { Wifi, WifiOff, AlertTriangle, HelpCircle } from 'lucide-react';

const StatusIndicator = ({ status, size = 'md', showText = true }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          icon: Wifi,
          text: 'Connected',
          className: 'status-connected',
          dotColor: 'bg-green-500'
        };
      case 'disconnected':
        return {
          icon: WifiOff,
          text: 'Disconnected',
          className: 'status-disconnected',
          dotColor: 'bg-red-500'
        };
      case 'warning':
        return {
          icon: AlertTriangle,
          text: 'Issues Detected',
          className: 'status-warning',
          dotColor: 'bg-yellow-500'
        };
      default:
        return {
          icon: HelpCircle,
          text: 'Unknown',
          className: 'status-unknown',
          dotColor: 'bg-gray-400'
        };
    }
  };

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return {
          container: 'px-2 py-1 text-xs',
          icon: 'w-3 h-3',
          dot: 'w-2 h-2'
        };
      case 'lg':
        return {
          container: 'px-4 py-3 text-base',
          icon: 'w-6 h-6',
          dot: 'w-3 h-3'
        };
      default:
        return {
          container: 'px-3 py-2 text-sm',
          icon: 'w-4 h-4',
          dot: 'w-2.5 h-2.5'
        };
    }
  };

  const config = getStatusConfig();
  const sizeClasses = getSizeClasses();
  const Icon = config.icon;

  if (!showText) {
    return (
      <div className={`flex items-center justify-center w-8 h-8 rounded-full ${config.className}`}>
        <div className={`${config.dotColor} ${sizeClasses.dot} rounded-full`}></div>
      </div>
    );
  }

  return (
    <div className={`inline-flex items-center rounded-full border ${config.className} ${sizeClasses.container}`}>
      <Icon className={`${sizeClasses.icon} mr-2`} />
      <span className="font-medium">{config.text}</span>
    </div>
  );
};

export default StatusIndicator;