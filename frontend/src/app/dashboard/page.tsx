'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { analytics } from '@/lib/api';
import { Loader2, ArrowRight, MessageSquare, TrendingUp, Target, BarChart3 } from 'lucide-react';
import { motion } from 'framer-motion';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

interface BusinessProfile {
  company_name?: string;
  industry?: string;
  key_metrics?: Record<string, number | string>;
  goals?: string[];
}

interface AnalyticsData {
  profile: BusinessProfile;
  insights: {
    top_topics?: string[];
    suggested_focus_areas?: string[];
    [key: string]: any;
  };
  followups: Array<{ key: string; value: string }> | string | { items?: any[]; checklist?: any[]; [key: string]: any };
}

const METRIC_LABELS: Record<string, string> = {
  monthly_revenue: 'Monthly Revenue',
  revenue: 'Revenue',
  customer_count: 'Customers',
  customers: 'Customers',
  mrr: 'MRR',
  arr: 'ARR',
  growth_rate: 'Growth Rate',
  conversion_rate: 'Conversion',
};

const formatMetricValue = (key: string, value: number | string): string => {
  if (typeof value === 'number') {
    if (key.includes('revenue') || key.includes('mrr') || key.includes('arr')) {
      return `$${value.toLocaleString()}`;
    }
    return value.toLocaleString();
  }
  return String(value);
};

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

export default function DashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await analytics.get();
        setData(result);
      } catch (err) {
        console.error('Failed to fetch analytics:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-muted-foreground animate-spin" />
      </div>
    );
  }

  const profile = data?.profile || {};
  const keyMetrics = profile.key_metrics || {};
  const topTopics: Array<string | { topic: string; frequency?: number }> = Array.isArray(data?.insights?.top_topics) 
    ? data!.insights.top_topics 
    : (Array.isArray(data?.insights?.suggested_focus_areas) ? data!.insights.suggested_focus_areas : []);
  const followups: Array<{ key: string; value: string } | string> = Array.isArray(data?.followups) 
    ? data!.followups 
    : (typeof data?.followups === 'object' && data?.followups !== null 
        ? (data.followups.items || data.followups.checklist || []) 
        : []);
  const goals = profile.goals || [];

  // Prepare chart data
  const metricsChartData = Object.entries(keyMetrics).map(([key, value]) => ({
    name: METRIC_LABELS[key] || key.replace(/_/g, ' '),
    value: typeof value === 'number' ? value : 0,
    fullKey: key,
  }));

  const topicsChartData = topTopics.slice(0, 6).map((topic) => ({
    name: typeof topic === 'string' ? topic : topic.topic,
    value: typeof topic === 'object' ? (topic.frequency || 1) : 1,
  }));

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-foreground mb-1">Dashboard</h1>
          {profile.company_name ? (
            <p className="text-sm text-muted-foreground">
              {profile.company_name}
              {profile.industry && ` • ${profile.industry}`}
            </p>
          ) : (
            <p className="text-sm text-muted-foreground">Your business overview</p>
          )}
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Metrics Bar Chart */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-card rounded-xl border border-border p-6"
          >
            <h2 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
              <BarChart3 size={16} className="text-blue-600" />
              Key Metrics
            </h2>
            {metricsChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={metricsChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis 
                    dataKey="name" 
                    tick={{ fontSize: 10 }} 
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #E5E7EB',
                      borderRadius: '8px',
                      fontSize: '12px'
                    }}
                    formatter={(value: number, _name: string, props: { payload: { fullKey: string; name: string } }) => [
                      formatMetricValue(props.payload.fullKey, value),
                      props.payload.name
                    ]}
                  />
                  <Bar dataKey="value" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[250px] flex items-center justify-center">
                <div className="text-center">
                  <BarChart3 className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-sm text-gray-500">No metrics data available</p>
                </div>
              </div>
            )}
          </motion.div>

          {/* Topics Pie Chart */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-card rounded-xl border border-border p-6"
          >
            <h2 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
              <MessageSquare size={16} className="text-blue-600" />
              Conversation Topics
            </h2>
            {topicsChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={topicsChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                    label={({ name }: { name: string }) => name.length > 15 ? name.substring(0, 15) + '...' : name}
                    labelStyle={{ fontSize: '10px' }}
                  >
                    {topicsChartData.map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #E5E7EB',
                      borderRadius: '8px',
                      fontSize: '12px'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[250px] flex items-center justify-center">
                <div className="text-center">
                  <MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-sm text-gray-500">No conversation data available</p>
                </div>
              </div>
            )}
          </motion.div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {Object.entries(keyMetrics).slice(0, 4).map(([key, value], index) => (
            <motion.div
              key={key}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="p-4 bg-card rounded-xl border border-border hover:border-blue-200 hover:shadow-sm transition-all cursor-pointer group"
            >
              <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1">
                {METRIC_LABELS[key] || key.replace(/_/g, ' ')}
              </p>
              <p className="text-xl font-bold text-foreground group-hover:text-blue-600 transition-colors">
                {formatMetricValue(key, value)}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Topics */}
          <div className="p-6 bg-card rounded-xl border border-border">
            <h2 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
              <MessageSquare size={16} className="text-blue-600" />
              Recent conversation topics
            </h2>
            {topTopics.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {topTopics.map((topicObj, idx) => {
                  const topicText = typeof topicObj === 'string' ? topicObj : topicObj.topic;
                  const frequency = typeof topicObj === 'object' ? topicObj.frequency : null;
                  return (
                    <motion.span
                      key={idx}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: idx * 0.05 }}
                      className="text-xs px-3 py-1.5 bg-muted text-muted-foreground rounded-lg border border-border hover:border-blue-300 hover:text-foreground transition-colors cursor-pointer"
                      title={frequency ? `Mentioned ${frequency} times` : undefined}
                    >
                      {topicText}
                    </motion.span>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-6">
                <p className="text-sm text-muted-foreground">Start chatting to generate insights</p>
                <button
                  onClick={() => router.push('/chat')}
                  className="mt-3 px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-xl transition-colors"
                >
                  Start Chat
                </button>
              </div>
            )}
          </div>

          {/* Follow-ups */}
          <div className="p-6 bg-card rounded-xl border border-border">
            <h2 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
              <Target size={16} className="text-blue-600" />
              Follow-ups
            </h2>
            {followups.length > 0 ? (
              <div className="space-y-3">
                {followups.map((item, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className="flex items-start gap-3 p-3 bg-muted rounded-xl border border-border hover:border-blue-200 transition-colors"
                  >
                    <span className="text-sm text-blue-600 font-medium min-w-[24px]">
                      {idx + 1}.
                    </span>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {typeof item === 'string' ? item : item.value}
                    </p>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6">
                <p className="text-sm text-muted-foreground">No pending follow-ups</p>
                <button
                  onClick={() => router.push('/chat')}
                  className="mt-3 px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-xl transition-colors"
                >
                  Go to Chat
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Business Goals */}
        {goals.length > 0 && (
          <div className="mt-6 p-6 bg-card rounded-xl border border-border">
            <h2 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
              <TrendingUp size={16} className="text-blue-600" />
              Business Goals
            </h2>
            <div className="space-y-3">
              {goals.map((goal, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="flex items-center gap-3 p-3 bg-muted rounded-xl"
                >
                  <svg className="h-4 w-4 text-green-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <p className="text-sm text-muted-foreground">{goal}</p>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Update Profile Link */}
        <div className="mt-8">
          <button
            onClick={() => router.push('/settings')}
            className="inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 transition-colors"
          >
            Update profile
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
