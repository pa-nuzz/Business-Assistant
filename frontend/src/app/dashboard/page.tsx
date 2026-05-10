'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { analytics, tasks as tasksApi, user } from '@/lib/api';
import Image from 'next/image';
import {
  MessageSquare, CheckSquare, FileText, Settings,
  TrendingUp, ArrowRight, Clock, ArrowUpRight,
  Plus, RefreshCw, AlertTriangle
} from 'lucide-react';
import { motion } from 'framer-motion';

interface TaskSummary {
  total: number;
  todo: number;
  in_progress: number;
  completed: number;
  overdue: number;
}

interface AnalyticsData {
  profile?: {
    company_name?: string;
    industry?: string;
  };
  executive_summary?: string;
  forecast?: {
    velocity: string | number;
    backlog_clearance_days: number;
  };
  proactive_alerts?: Array<{
    title: string;
    message: string;
    severity: 'high' | 'medium' | 'low';
  }>;
  summary?: {
    total_documents?: number;
    total_conversations?: number;
    total_messages?: number;
  };
}

export default function DashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [taskStats, setTaskStats] = useState<TaskSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [greeting, setGreeting] = useState('');
  const [username, setUsername] = useState('');

  useEffect(() => {
    document.title = 'Dashboard | AEIOU AI';
    const h = new Date().getHours();
    if (h < 12) setGreeting('Good morning');
    else if (h < 17) setGreeting('Good afternoon');
    else setGreeting('Good evening');

    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [analyticsRes, statsRes, userRes] = await Promise.allSettled([
        analytics.get(),
        tasksApi.getStats(),
        user.getInfo(),
      ]);
      if (analyticsRes.status === 'fulfilled') setData(analyticsRes.value);
      if (statsRes.status === 'fulfilled') setTaskStats(statsRes.value);
      if (userRes.status === 'fulfilled') setUsername(userRes.value?.username || '');
    } catch { /* silent */ }
    finally { setLoading(false); }
  };

  const companyName = data?.profile?.company_name || null;
  const alerts = data?.proactive_alerts || [];
  const highAlerts = alerts.filter(a => a.severity === 'high');
  const hasWorkspaceActivity = Boolean(
    (taskStats?.total ?? 0) > 0 ||
    (data?.summary?.total_documents ?? 0) > 0 ||
    (data?.summary?.total_conversations ?? 0) > 0 ||
    (data?.summary?.total_messages ?? 0) > 0
  );

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-5xl mx-auto px-6 py-10">

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="flex items-start justify-between mb-10"
        >
          <div className="flex items-center gap-4">
            <Image
              src="/logos/core.svg"
              alt="AEIOU AI"
              width={44}
              height={44}
              className="shrink-0"
              priority
            />
            <div>
              <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">
                {greeting}{username ? `, ${username}` : ''}
              </h1>
              {companyName && (
                <p className="text-sm text-slate-500 mt-0.5">{companyName}</p>
              )}
            </div>
          </div>
          <button
            onClick={() => router.push('/chat')}
            className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors"
          >
            <MessageSquare className="w-4 h-4" />
            New chat
          </button>
        </motion.div>

        {/* Urgent alerts */}
        {highAlerts.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 bg-red-50 border border-red-100 rounded-lg flex items-start gap-3"
          >
            <AlertTriangle className="w-4 h-4 text-red-500 mt-0.5 shrink-0" />
            <div>
              {highAlerts.map((alert, i) => (
                <p key={i} className="text-sm text-red-800 font-medium">
                  {alert.message}
                </p>
              ))}
            </div>
          </motion.div>
        )}

        {/* Quick actions */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-8"
        >
          {[
            {
              label: 'AI Chat',
              desc: 'Ask Aiden anything',
              href: '/chat',
              icon: MessageSquare,
            },
            {
              label: 'Tasks',
              desc: 'Manage your work',
              href: '/tasks',
              icon: CheckSquare,
            },
            {
              label: 'Documents',
              desc: 'Upload & query files',
              href: '/documents',
              icon: FileText,
            },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.href}
                onClick={() => router.push(item.href)}
                className="group flex items-center gap-4 p-4 bg-white border border-slate-200 rounded-xl hover:border-slate-300 hover:shadow-sm transition-all text-left"
              >
                <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center group-hover:bg-slate-200 transition-colors">
                  <Icon className="w-5 h-5 text-slate-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-900">{item.label}</p>
                  <p className="text-xs text-slate-500">{item.desc}</p>
                </div>
                <ArrowUpRight className="w-4 h-4 text-slate-300 group-hover:text-slate-500 transition-colors" />
              </button>
            );
          })}
        </motion.div>

        {/* Stats row */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8"
        >
          {[
            { label: 'To do', value: taskStats?.todo ?? 0, accent: false },
            { label: 'In progress', value: taskStats?.in_progress ?? 0, accent: false },
            { label: 'Completed', value: taskStats?.completed ?? 0, accent: false },
            { label: 'Overdue', value: taskStats?.overdue ?? 0, accent: (taskStats?.overdue ?? 0) > 0 },
          ].map((stat) => (
            <div
              key={stat.label}
              className={`p-4 rounded-xl border ${
                stat.accent
                  ? 'bg-red-50 border-red-100'
                  : 'bg-slate-50 border-slate-100'
              }`}
            >
              <p className={`text-2xl font-semibold ${
                stat.accent ? 'text-red-600' : 'text-slate-900'
              }`}>
                {stat.value}
              </p>
              <p className={`text-xs mt-1 ${
                stat.accent ? 'text-red-500' : 'text-slate-500'
              }`}>
                {stat.label}
              </p>
            </div>
          ))}
        </motion.div>

        {/* Main content */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

          {/* Left: AI Summary */}
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="lg:col-span-3 bg-white border border-slate-200 rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-medium text-slate-900">Intelligence Summary</h2>
              <button
                onClick={fetchData}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-md hover:bg-slate-100 transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>

            {loading ? (
              <div className="space-y-3">
                <div className="h-4 bg-slate-100 rounded animate-pulse w-3/4" />
                <div className="h-4 bg-slate-100 rounded animate-pulse w-1/2" />
              </div>
            ) : data?.executive_summary ? (
              <p className="text-sm text-slate-600 leading-relaxed">
                {data.executive_summary}
              </p>
            ) : (
              <div className="text-center py-8">
                <p className="text-sm text-slate-500 mb-3">
                  Start a conversation or upload documents to get personalized insights.
                </p>
                <button
                  onClick={() => router.push('/chat')}
                  className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 bg-slate-100 rounded-lg hover:bg-slate-200 transition-colors"
                >
                  <MessageSquare className="w-4 h-4" />
                  Start chatting
                </button>
              </div>
            )}

            {!loading && !hasWorkspaceActivity && (
              <div className="mt-5 pt-5 border-t border-slate-100">
                <h3 className="text-sm font-medium text-slate-900 mb-3">First workspace win</h3>
                <div className="grid gap-2">
                  {[
                    { label: 'Upload a business document', detail: 'Give Aiden real context to summarize and query.', href: '/documents', icon: FileText },
                    { label: 'Create your first task', detail: 'Track one concrete outcome for today.', href: '/tasks', icon: CheckSquare },
                    { label: 'Ask Aiden for next steps', detail: 'Turn your current priority into a short action plan.', href: '/chat', icon: MessageSquare },
                  ].map((step) => {
                    const Icon = step.icon;
                    return (
                      <button
                        key={step.label}
                        onClick={() => router.push(step.href)}
                        className="flex items-start gap-3 p-3 rounded-lg border border-slate-100 hover:border-slate-200 hover:bg-slate-50 text-left transition-colors"
                      >
                        <Icon className="w-4 h-4 text-slate-500 mt-0.5 shrink-0" />
                        <span>
                          <span className="block text-sm font-medium text-slate-800">{step.label}</span>
                          <span className="block text-xs text-slate-500 mt-0.5">{step.detail}</span>
                        </span>
                        <ArrowRight className="w-3.5 h-3.5 text-slate-300 ml-auto mt-0.5 shrink-0" />
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Forecast mini-card */}
            {data?.forecast && (
              <div className="mt-5 pt-5 border-t border-slate-100 flex items-center gap-6">
                <div>
                  <p className="text-xs text-slate-500">Velocity</p>
                  <p className="text-lg font-semibold text-slate-900 flex items-center gap-1">
                    {data.forecast.velocity}
                    <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
                  </p>
                </div>
                <div className="w-px h-8 bg-slate-100" />
                <div>
                  <p className="text-xs text-slate-500">Backlog clearance</p>
                  <p className="text-lg font-semibold text-slate-900">
                    {data.forecast.backlog_clearance_days}d
                  </p>
                </div>
              </div>
            )}
          </motion.div>

          {/* Right: Quick links */}
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="lg:col-span-2 flex flex-col gap-3"
          >
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <h3 className="text-sm font-medium text-slate-900 mb-3">Quick actions</h3>
              <div className="space-y-2">
                {[
                  { label: 'Create a task', icon: Plus, href: '/tasks', action: 'new' },
                  { label: 'Upload a document', icon: FileText, href: '/documents' },
                  { label: 'Account settings', icon: Settings, href: '/settings' },
                ].map((link) => {
                  const Icon = link.icon;
                  return (
                    <button
                      key={link.label}
                      onClick={() => router.push(link.href)}
                      className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors text-left"
                    >
                      <Icon className="w-4 h-4 text-slate-400" />
                      {link.label}
                      <ArrowRight className="w-3.5 h-3.5 text-slate-300 ml-auto" />
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Alerts */}
            {alerts.length > 0 && (
              <div className="bg-white border border-slate-200 rounded-xl p-5">
                <h3 className="text-sm font-medium text-slate-900 mb-3">
                  Alerts
                  <span className="ml-2 text-xs text-slate-400 font-normal">{alerts.length}</span>
                </h3>
                <div className="space-y-2">
                  {alerts.slice(0, 4).map((alert, i) => (
                    <div
                      key={i}
                      className={`flex items-start gap-2.5 p-3 rounded-lg text-xs ${
                        alert.severity === 'high'
                          ? 'bg-red-50 text-red-700'
                          : alert.severity === 'medium'
                          ? 'bg-amber-50 text-amber-700'
                          : 'bg-slate-50 text-slate-600'
                      }`}
                    >
                      <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                      <span className="leading-relaxed">{alert.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        </div>

        {/* Footer */}
        <div className="mt-10 flex items-center justify-center gap-2 text-slate-300">
          <Clock className="w-3 h-3" />
          <span className="text-[10px] font-medium uppercase tracking-widest">
            {new Date().toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
          </span>
        </div>

      </div>
    </div>
  );
}
