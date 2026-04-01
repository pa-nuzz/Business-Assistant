'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { analytics } from '@/lib/api';
import { Loader2, Check, ArrowRight, MessageSquare, TrendingUp, Target, BarChart3 } from 'lucide-react';
import { motion } from 'framer-motion';

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
  };
  followups: Array<{ key: string; value: string }> | string;
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
  const topTopicsRaw = data?.insights?.top_topics;
  const topTopics: Array<string | { topic: string; frequency?: number }> = Array.isArray(topTopicsRaw) ? topTopicsRaw : [];
  const followupsRaw = data?.followups;
  let followups: Array<{ key: string; value: string } | string> = [];
  if (Array.isArray(followupsRaw)) {
    followups = followupsRaw;
  } else if (followupsRaw && typeof followupsRaw === 'object') {
    const followupsObj = followupsRaw as Record<string, any>;
    followups = followupsObj.items || followupsObj.followups || [];
  }
  const goals = profile.goals || [];

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-5xl mx-auto">
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

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {Object.keys(keyMetrics).length === 0 ? (
            <div className="col-span-full p-8 bg-card rounded-xl border border-border text-center">
              <div className="w-12 h-12 rounded-xl bg-muted flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="w-6 h-6 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-medium text-foreground mb-2">No metrics yet</h3>
              <p className="text-sm text-muted-foreground mb-4">Ask AEIOU AI to track your business metrics</p>
              <button
                onClick={() => router.push('/chat')}
                className="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-xl transition-colors"
              >
                Go to Chat
              </button>
            </div>
          ) : (
            Object.entries(keyMetrics).map(([key, value]) => (
              <motion.div
                key={key}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-5 bg-card rounded-xl border border-border hover:border-blue-200 hover:shadow-sm transition-all cursor-pointer group"
              >
                <p className="text-xs uppercase tracking-wide text-muted-foreground mb-2">
                  {METRIC_LABELS[key] || key.replace(/_/g, ' ')}
                </p>
                <p className="text-2xl font-bold text-foreground group-hover:text-blue-600 transition-colors">
                  {formatMetricValue(key, value)}
                </p>
              </motion.div>
            ))
          )}
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
                  <Check className="h-4 w-4 text-green-600 flex-shrink-0" />
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
