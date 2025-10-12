'use client';

import React, { useState, useEffect } from 'react';
import { BarChart3, Users, FileText, Search, Activity, TrendingUp, Calendar, Download } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/useToast';
import { analyticsAPI } from '@/services/api';
import { ErrorBoundary } from '@/components/ErrorBoundary';

interface UserActivityData {
  login_activity: Array<{ date: string; logins: number }>;
  upload_activity: Array<{ date: string; uploads: number; total_size: number }>;
  qa_activity: Array<{ date: string; sessions: number; unique_users: number }>;
  search_activity: Array<{ date: string; searches: number }>;
  user_metrics: {
    total_users: number;
    active_users: number;
    avg_user_age_days: number;
  };
  period_days: number;
}

interface SystemMetricsData {
  api_performance: Array<{
    endpoint: string;
    avg_response_time: number;
    min_response_time: number;
    max_response_time: number;
    sample_count: number;
  }>;
  error_rates: Array<{ date: string; errors: number }>;
  database_metrics: Array<{
    metric: string;
    avg_value: number;
    max_value: number;
  }>;
  storage_metrics: {
    total_storage_bytes: number;
    total_files: number;
    avg_file_size_bytes: number;
  };
  period_hours: number;
}

const AnalyticsPage: React.FC = () => {
  return (
    <ErrorBoundary>
      <AnalyticsPageContent />
    </ErrorBoundary>
  );
};

const AnalyticsPageContent: React.FC = () => {
  const { user } = useAuth();
  const { error: showError } = useToast();
  const [userActivityData, setUserActivityData] = useState<UserActivityData | null>(null);
  const [systemMetricsData, setSystemMetricsData] = useState<SystemMetricsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'7' | '30' | '90'>('30');

  useEffect(() => {
    if (user?.role?.includes('admin') || user?.role === 'superadmin') {
      loadAnalyticsData();
    }
  }, [user, timeRange]);

  const loadAnalyticsData = async () => {
    try {
      setIsLoading(true);
      const days = parseInt(timeRange);

      const [userActivity, systemMetrics] = await Promise.all([
        analyticsAPI.getUserActivity(days),
        analyticsAPI.getSystemMetrics(days * 24) // Convert days to hours
      ]);

      setUserActivityData(userActivity);
      setSystemMetricsData(systemMetrics);
    } catch (error) {
      console.error('Failed to load analytics:', error);
      showError('Failed to load analytics data');
    } finally {
      setIsLoading(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const exportData = (data: any, filename: string) => {
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!user || (!user.role?.includes('admin') && user.role !== 'superadmin')) {
    return (
      <div className="min-h-screen bg-gray-50 p-6 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h1>
          <p className="text-gray-600">You need admin privileges to view analytics.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Analytics Dashboard</h1>
              <p className="text-gray-600">Comprehensive insights into user activity and system performance</p>
            </div>
            <div className="flex items-center gap-4">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value as '7' | '30' | '90')}
                className="px-4 py-2 border border-gray-300 rounded-lg"
              >
                <option value="7">Last 7 days</option>
                <option value="30">Last 30 days</option>
                <option value="90">Last 90 days</option>
              </select>
              <button
                onClick={() => exportData({ userActivityData, systemMetricsData }, 'analytics_data')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
              >
                <Download className="h-4 w-4" />
                Export Data
              </button>
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        ) : (
          <>
            {/* Key Metrics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center">
                  <Users className="h-8 w-8 text-blue-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Users</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {userActivityData?.user_metrics.total_users || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center">
                  <Activity className="h-8 w-8 text-green-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Active Users</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {userActivityData?.user_metrics.active_users || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center">
                  <FileText className="h-8 w-8 text-purple-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Documents</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {systemMetricsData?.storage_metrics.total_files || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center">
                  <TrendingUp className="h-8 w-8 text-orange-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Storage Used</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatBytes(systemMetricsData?.storage_metrics.total_storage_bytes || 0)}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* User Activity Chart */}
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">User Activity Trends</h3>
                <div className="space-y-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Daily Logins</h4>
                    <div className="h-32 flex items-end space-x-1">
                      {userActivityData?.login_activity.slice(-7).map((item, index) => (
                        <div key={index} className="flex-1 flex flex-col items-center">
                          <div
                            className="w-full bg-blue-500 rounded-t"
                            style={{ height: `${Math.max((item.logins / Math.max(...userActivityData.login_activity.map(d => d.logins))) * 100, 5)}%` }}
                          ></div>
                          <span className="text-xs text-gray-500 mt-1">
                            {new Date(item.date).toLocaleDateString('en-US', { weekday: 'short' })}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* System Performance Chart */}
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">API Performance</h3>
                <div className="space-y-4">
                  {systemMetricsData?.api_performance.map((metric, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{metric.endpoint}</p>
                        <p className="text-xs text-gray-500">
                          {metric.sample_count} requests
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold text-gray-900">
                          {metric.avg_response_time}ms
                        </p>
                        <p className="text-xs text-gray-500">
                          {metric.min_response_time}-{metric.max_response_time}ms
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Detailed Tables */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Recent Activity Table */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {userActivityData?.qa_activity.slice(-5).map((item, index) => (
                      <div key={index} className="flex items-center justify-between py-2">
                        <div className="flex items-center gap-3">
                          <Search className="h-5 w-5 text-gray-400" />
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              {item.sessions} QA Sessions
                            </p>
                            <p className="text-xs text-gray-500">
                              {item.unique_users} unique users
                            </p>
                          </div>
                        </div>
                        <span className="text-sm text-gray-500">
                          {new Date(item.date).toLocaleDateString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* System Health Table */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">System Health</h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Avg File Size</span>
                      <span className="text-sm font-medium text-gray-900">
                        {formatBytes(systemMetricsData?.storage_metrics.avg_file_size_bytes || 0)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">User Engagement</span>
                      <span className="text-sm font-medium text-gray-900">
                        {userActivityData?.user_metrics.avg_user_age_days || 0} days avg
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Error Rate</span>
                      <span className="text-sm font-medium text-gray-900">
                        {systemMetricsData?.error_rates.reduce((sum, item) => sum + item.errors, 0) || 0} errors
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default AnalyticsPage;