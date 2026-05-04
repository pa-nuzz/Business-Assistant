"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, LineChart, PieChart, Activity, Zap, Users, TrendingUp } from "lucide-react";
import api from "@/lib/api";
import { toast } from "sonner";

interface EngagementData {
  period_days: number;
  total_actions: number;
  active_days: number;
  engagement_score: number;
  feature_breakdown: Array<{ feature: string; count: number }>;
  daily_activity: Array<{ date: string; count: number }>;
}

interface AIUsageData {
  period_days: number;
  total_calls: number;
  total_tokens: number;
  total_cost: number;
  avg_response_time: number;
  success_rate: number;
  by_model: Array<{ model: string; calls: number; tokens: number; cost: number }>;
}

export function AnalyticsDashboard() {
  const [engagement, setEngagement] = useState<EngagementData | null>(null);
  const [aiUsage, setAiUsage] = useState<AIUsageData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const [engRes, aiRes] = await Promise.all([
        api.get("/api/v1/analytics/engagement/?days=30"),
        api.get("/api/v1/analytics/ai-usage/?days=30"),
      ]);
      setEngagement(engRes.data);
      setAiUsage(aiRes.data);
    } catch {
      toast.error("Failed to load analytics");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Actions</CardTitle>
            <Activity className="w-4 h-4 text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {engagement?.total_actions?.toLocaleString() ?? 0}
            </div>
            <p className="text-xs text-slate-500">Last 30 days</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Days</CardTitle>
            <Users className="w-4 h-4 text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {engagement?.active_days ?? 0}
            </div>
            <p className="text-xs text-slate-500">Out of 30 days</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">AI Calls</CardTitle>
            <Zap className="w-4 h-4 text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {aiUsage?.total_calls?.toLocaleString() ?? 0}
            </div>
            <p className="text-xs text-slate-500">
              {aiUsage?.success_rate?.toFixed(1) ?? 0}% success rate
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">AI Cost</CardTitle>
            <TrendingUp className="w-4 h-4 text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${aiUsage?.total_cost?.toFixed(2) ?? "0.00"}
            </div>
            <p className="text-xs text-slate-500">Last 30 days</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Feature Usage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {engagement?.feature_breakdown?.map((item) => (
                <div key={item.feature} className="flex items-center justify-between">
                  <span className="text-sm capitalize">{item.feature}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-indigo-600 rounded-full"
                        style={{
                          width: `${(item.count / (engagement.total_actions || 1)) * 100}%`,
                        }}
                      />
                    </div>
                    <span className="text-xs text-slate-500 w-8 text-right">
                      {item.count}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">AI by Model</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {aiUsage?.by_model?.map((item) => (
                <div key={item.model} className="flex items-center justify-between">
                  <span className="text-sm">{item.model}</span>
                  <div className="text-xs text-slate-500">
                    {item.calls.toLocaleString()} calls • ${item.cost.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
