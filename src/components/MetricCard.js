import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

const MetricCard = ({ 
  title, 
  value, 
  unit = '', 
  change = null, 
  changeType = 'neutral',
  icon: Icon,
  status = 'normal'
}) => {
  const getStatusStyle = () => {
    switch (status) {
      case 'good':
        return 'border-green-200 bg-green-50';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50';
      case 'error':
        return 'border-red-200 bg-red-50';
      default:
        return 'border-gray-200 bg-white';
    }
  };

  const getChangeIcon = () => {
    switch (changeType) {
      case 'positive':
        return <TrendingUp className="w-3 h-3" />;
      case 'negative':
        return <TrendingDown className="w-3 h-3" />;
      default:
        return <Minus className="w-3 h-3" />;
    }
  };

  const formatValue = (val) => {
    if (typeof val === 'number') {
      if (val >= 1000) {
        return (val / 1000).toFixed(1) + 'K';
      }
      return val.toFixed(1);
    }
    return val;
  };

  return (
    <div className={`metric-card ${getStatusStyle()}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        {Icon && <Icon className="w-5 h-5 text-gray-400" />}
      </div>
      
      <div className="space-y-1">
        <div className="flex items-baseline">
          <span className="metric-value">{formatValue(value)}</span>
          {unit && <span className="text-sm text-gray-500 ml-1">{unit}</span>}
        </div>
        
        {change !== null && (
          <div className={`metric-change ${changeType}`}>
            {getChangeIcon()}
            <span className="ml-1">
              {change > 0 ? '+' : ''}{change}%
            </span>
            <span className="text-gray-500 ml-1">vs last hour</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default MetricCard;