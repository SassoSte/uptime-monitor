import React, { useState, useEffect } from 'react';
import { Download, FileText, Calendar, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';
import { format, subDays } from 'date-fns';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const Reports = () => {
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [reportDays, setReportDays] = useState(7);

  const generateReport = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/report?days=${reportDays}`);
      const data = await response.json();
      setReportData(data);
    } catch (error) {
      console.error('Error generating report:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    generateReport();
  }, [reportDays]);

  const exportReport = async (format) => {
    if (!reportData) return;
    
    const exportData = {
      ...reportData,
      generated_at: new Date().toISOString(),
      format: format
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `uptime-report-${format(new Date(), 'yyyy-MM-dd')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getSeverityData = () => {
    if (!reportData?.outages) return [];
    
    const severityCounts = reportData.outages.reduce((acc, outage) => {
      acc[outage.severity] = (acc[outage.severity] || 0) + 1;
      return acc;
    }, {});

    return Object.entries(severityCounts).map(([severity, count]) => ({
      name: severity,
      value: count,
      color: severity === 'complete' ? '#ef4444' : severity === 'partial' ? '#f59e0b' : '#8b5cf6'
    }));
  };

  if (loading && !reportData) {
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
              <h1 className="text-3xl font-bold text-gray-900">Internet Monitoring Report</h1>
              <p className="text-gray-500 mt-1">
                Comprehensive analysis of your internet performance and reliability
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <select
                value={reportDays}
                onChange={(e) => setReportDays(parseInt(e.target.value))}
                className="btn-secondary"
              >
                <option value={1}>Last Day</option>
                <option value={7}>Last Week</option>
                <option value={30}>Last Month</option>
                <option value={90}>Last 3 Months</option>
              </select>
              
              <button
                onClick={() => exportReport('json')}
                className="btn-primary"
                disabled={!reportData}
              >
                <Download className="w-4 h-4 mr-2" />
                Export Report
              </button>
            </div>
          </div>

          {reportData && (
            <>
              {/* Report Summary */}
              <div className="notion-card p-6">
                <div className="flex items-center mb-4">
                  <FileText className="w-6 h-6 text-blue-600 mr-3" />
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">Report Summary</h2>
                    <p className="text-gray-500">
                      {format(new Date(reportData.period.start), 'MMM dd, yyyy')} - {format(new Date(reportData.period.end), 'MMM dd, yyyy')}
                    </p>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className={`text-3xl font-bold ${
                      reportData.summary.overall_uptime_percentage >= 99 ? 'text-green-600' :
                      reportData.summary.overall_uptime_percentage >= 95 ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {reportData.summary.overall_uptime_percentage}%
                    </div>
                    <div className="text-sm text-gray-500">Overall Uptime</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600">
                      {reportData.summary.avg_download_speed_mbps} Mbps
                    </div>
                    <div className="text-sm text-gray-500">Avg Download Speed</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-3xl font-bold text-purple-600">
                      {reportData.summary.total_outages}
                    </div>
                    <div className="text-sm text-gray-500">Total Outages</div>
                  </div>
                </div>
              </div>

              {/* Key Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="notion-card p-6 text-center">
                  <TrendingUp className="w-8 h-8 text-green-600 mx-auto mb-3" />
                  <div className="text-2xl font-bold text-gray-900">
                    {reportData.summary.avg_latency_ms} ms
                  </div>
                  <div className="text-sm text-gray-500">Average Latency</div>
                </div>
                
                <div className="notion-card p-6 text-center">
                  <TrendingUp className="w-8 h-8 text-blue-600 mx-auto mb-3" />
                  <div className="text-2xl font-bold text-gray-900">
                    {reportData.summary.max_download_speed_mbps} Mbps
                  </div>
                  <div className="text-sm text-gray-500">Peak Download Speed</div>
                </div>
                
                <div className="notion-card p-6 text-center">
                  <AlertTriangle className="w-8 h-8 text-red-600 mx-auto mb-3" />
                  <div className="text-2xl font-bold text-gray-900">
                    {reportData.summary.total_outage_duration_minutes} min
                  </div>
                  <div className="text-sm text-gray-500">Total Downtime</div>
                </div>
                
                <div className="notion-card p-6 text-center">
                  <TrendingUp className="w-8 h-8 text-yellow-600 mx-auto mb-3" />
                  <div className="text-2xl font-bold text-gray-900">
                    {reportData.summary.avg_upload_speed_mbps} Mbps
                  </div>
                  <div className="text-sm text-gray-500">Avg Upload Speed</div>
                </div>
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Outage Severity Distribution */}
                {getSeverityData().length > 0 && (
                  <div className="notion-card p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Outage Severity Distribution</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={getSeverityData()}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {getSeverityData().map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Speed Range Distribution */}
                <div className="notion-card p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Overview</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Minimum Speed</span>
                      <span className="font-semibold">{reportData.summary.min_download_speed_mbps} Mbps</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Average Speed</span>
                      <span className="font-semibold">{reportData.summary.avg_download_speed_mbps} Mbps</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Maximum Speed</span>
                      <span className="font-semibold">{reportData.summary.max_download_speed_mbps} Mbps</span>
                    </div>
                    <div className="pt-4 border-t">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Average Latency</span>
                        <span className="font-semibold">{reportData.summary.avg_latency_ms} ms</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Recommendations */}
              <div className="notion-card p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommendations</h3>
                <div className="space-y-3">
                  {reportData.recommendations.map((recommendation, index) => (
                    <div key={index} className="flex items-start">
                      <CheckCircle className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{recommendation}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recent Outages */}
              {reportData.outages.length > 0 && (
                <div className="notion-card">
                  <div className="notion-card-header">
                    <h3 className="text-lg font-semibold text-gray-900">Recent Outages</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="table-header">Start Time</th>
                          <th className="table-header">Duration</th>
                          <th className="table-header">Severity</th>
                          <th className="table-header">Status</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {reportData.outages.slice(0, 10).map((outage) => (
                          <tr key={outage.id} className="table-row">
                            <td className="table-cell">
                              {format(new Date(outage.start_time), 'MMM dd, HH:mm')}
                            </td>
                            <td className="table-cell">
                              {outage.duration_seconds ? `${Math.round(outage.duration_seconds / 60)}m` : 'Ongoing'}
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
                              <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                outage.is_resolved ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                              }`}>
                                {outage.is_resolved ? 'Resolved' : 'Ongoing'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Reports;