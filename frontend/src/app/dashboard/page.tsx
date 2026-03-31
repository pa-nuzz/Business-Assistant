'use client';

import { useState, useEffect } from 'react';
import { analytics } from '@/lib/api';
import { Loader2, Check, ArrowRight, MessageSquare, TrendingUp, Target, BarChart3 } from 'lucide-react';
import { SkeletonCard } from '@/components/skeleton';

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
      <div style={{ maxWidth: '960px', margin: '0 auto', padding: '32px 24px' }}>
        <div style={{ marginBottom: '32px' }}>
          <div className="skeleton" style={{ width: '200px', height: '28px', marginBottom: '8px' }} />
          <div className="skeleton" style={{ width: '150px', height: '16px' }} />
        </div>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '16px',
          marginBottom: '32px',
        }}>
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    );
  }

  const profile = data?.profile || {};
  const keyMetrics = profile.key_metrics || {};
  const topTopicsRaw = data?.insights?.top_topics;
  const topTopics: Array<string | { topic: string; frequency?: number }> = Array.isArray(topTopicsRaw) ? topTopicsRaw : [];
  const followups = Array.isArray(data?.followups) ? data.followups : [];
  const goals = profile.goals || [];

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '32px 24px' }}>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{
          fontSize: '24px',
          fontWeight: 500,
          color: 'var(--ink-0)',
          letterSpacing: 'var(--tracking-tight)',
          margin: '0 0 8px',
        }}>
          Dashboard
        </h1>
        {profile.company_name && (
          <p style={{ fontSize: '14px', color: 'var(--ink-2)', margin: 0 }}>
            {profile.company_name}
            {profile.industry && ` • ${profile.industry}`}
          </p>
        )}
      </div>

      {/* Metrics Grid */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
        gap: '16px',
        marginBottom: '32px',
      }}>
        {Object.keys(keyMetrics).length === 0 ? (
          <div style={{
            gridColumn: '1 / -1',
            padding: '48px 40px',
            backgroundColor: 'var(--surface-0)',
            border: '1px solid var(--surface-border)',
            borderRadius: 'var(--r-lg)',
            textAlign: 'center',
          }}>
            <BarChart3 size={32} style={{ color: 'var(--ink-3)', marginBottom: '12px' }} />
            <p style={{ fontSize: '14px', color: 'var(--ink-2)', margin: '0 0 8px', fontWeight: 500 }}>
              No metrics yet
            </p>
            <p style={{ fontSize: '13px', color: 'var(--ink-3)', margin: 0 }}>
              Ask the assistant to track your business metrics
            </p>
          </div>
        ) : (
          Object.entries(keyMetrics).map(([key, value]) => (
            <div
              key={key}
              style={{
                padding: '20px',
                backgroundColor: 'var(--surface-0)',
                border: '1px solid var(--surface-border)',
                borderRadius: 'var(--r-lg)',
              }}
            >
              <p style={{
                fontSize: '12px',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                color: 'var(--ink-3)',
                margin: '0 0 8px',
              }}>
                {METRIC_LABELS[key] || key.replace(/_/g, ' ')}
              </p>
              <p style={{
                fontSize: '28px',
                fontWeight: 500,
                color: 'var(--ink-0)',
                letterSpacing: 'var(--tracking-tight)',
                margin: 0,
              }}>
                {formatMetricValue(key, value)}
              </p>
              <p style={{
                fontSize: '13px',
                color: 'var(--ink-2)',
                margin: '4px 0 0',
              }}>
                from key_metrics
              </p>
            </div>
          ))
        )}
      </div>

      {/* Two Column Layout */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
        gap: '24px',
      }}>
        {/* Top Topics */}
        <div>
          <h2 style={{
            fontSize: '15px',
            fontWeight: 500,
            color: 'var(--ink-0)',
            margin: '0 0 16px',
          }}>
            Recent conversation topics
          </h2>
          {topTopics.length > 0 ? (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {topTopics.map((topicObj, idx) => {
                const topicText = typeof topicObj === 'string' ? topicObj : topicObj.topic;
                const frequency = typeof topicObj === 'object' ? topicObj.frequency : null;
                return (
                  <span
                    key={idx}
                    style={{
                      fontSize: '12px',
                      padding: '4px 10px',
                      backgroundColor: 'var(--surface-2)',
                      color: 'var(--ink-1)',
                      borderRadius: '20px',
                    }}
                    title={frequency ? `Mentioned ${frequency} times` : undefined}
                  >
                    {topicText}
                  </span>
                );
              })}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '24px' }}>
              <MessageSquare size={24} style={{ color: 'var(--ink-3)', marginBottom: '8px' }} />
              <p style={{ fontSize: '14px', color: 'var(--ink-2)', margin: '0 0 4px' }}>
                No topics yet
              </p>
              <p style={{ fontSize: '13px', color: 'var(--ink-3)', margin: 0 }}>
                Start chatting to generate insights
              </p>
            </div>
          )}
        </div>

        {/* Follow-ups */}
        <div>
          <h2 style={{
            fontSize: '15px',
            fontWeight: 500,
            color: 'var(--ink-0)',
            margin: '0 0 16px',
          }}>
            Follow-ups
          </h2>
          {followups.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {followups.map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                    padding: '10px 12px',
                    backgroundColor: 'var(--surface-0)',
                    border: '1px solid var(--surface-border)',
                    borderRadius: 'var(--r-md)',
                  }}
                >
                  <span style={{
                    fontSize: '13px',
                    color: 'var(--ink-3)',
                    fontWeight: 500,
                    minWidth: '20px',
                  }}>
                    {idx + 1}.
                  </span>
                  <p style={{
                    fontSize: '14px',
                    color: 'var(--ink-1)',
                    margin: 0,
                    lineHeight: 1.5,
                  }}>
                    {typeof item === 'string' ? item : item.value}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '24px' }}>
              <Target size={24} style={{ color: 'var(--ink-3)', marginBottom: '8px' }} />
              <p style={{ fontSize: '14px', color: 'var(--ink-2)', margin: '0 0 4px' }}>
                No pending follow-ups
              </p>
              <p style={{ fontSize: '13px', color: 'var(--ink-3)', margin: 0 }}>
                Ask the assistant to track something
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Business Goals */}
      {goals.length > 0 && (
        <div style={{ marginTop: '32px' }}>
          <h2 style={{
            fontSize: '15px',
            fontWeight: 500,
            color: 'var(--ink-0)',
            margin: '0 0 16px',
          }}>
            Business Goals
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {goals.map((goal, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '12px 16px',
                  backgroundColor: 'var(--surface-0)',
                  border: '1px solid var(--surface-border)',
                  borderRadius: 'var(--r-md)',
                }}
              >
                <Check size={16} style={{ color: 'var(--accent-green)', flexShrink: 0 }} />
                <p style={{
                  fontSize: '14px',
                  color: 'var(--ink-1)',
                  margin: 0,
                }}>
                  {goal}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Update Profile Link */}
      <div style={{ marginTop: '32px' }}>
        <a
          href="#"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            fontSize: '14px',
            color: 'var(--accent-blue)',
            textDecoration: 'none',
          }}
        >
          Update profile
          <ArrowRight size={14} />
        </a>
      </div>
    </div>
  );
}
