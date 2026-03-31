'use client';

import { useState, useEffect } from 'react';
import { profile } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';

export default function ProfileForm() {
  const [formData, setFormData] = useState({
    company_name: '',
    industry: '',
    company_size: '',
    description: '',
    goals: '',
    key_metrics: '{}',
  });
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    profile.get().then((data) => {
      setFormData({
        ...data,
        key_metrics: JSON.stringify(data.key_metrics || {}, null, 2),
      });
    }).catch(() => {
      // No profile yet
    });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await profile.update({
        ...formData,
        key_metrics: JSON.parse(formData.key_metrics),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      alert('Failed to save profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Business Profile</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium">Company Name</label>
            <Input
              value={formData.company_name}
              onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
            />
          </div>
          
          <div>
            <label className="text-sm font-medium">Industry</label>
            <Input
              value={formData.industry}
              onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
              placeholder="e.g., SaaS, Retail, Consulting"
            />
          </div>
          
          <div>
            <label className="text-sm font-medium">Company Size</label>
            <Input
              value={formData.company_size}
              onChange={(e) => setFormData({ ...formData, company_size: e.target.value })}
              placeholder="e.g., 10-50 employees"
            />
          </div>
          
          <div>
            <label className="text-sm font-medium">Description</label>
            <Textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="What does your business do?"
            />
          </div>
          
          <div>
            <label className="text-sm font-medium">Goals</label>
            <Textarea
              value={formData.goals}
              onChange={(e) => setFormData({ ...formData, goals: e.target.value })}
              placeholder="What are your main business goals?"
            />
          </div>
          
          <div>
            <label className="text-sm font-medium">Key Metrics (JSON)</label>
            <Textarea
              value={formData.key_metrics}
              onChange={(e) => setFormData({ ...formData, key_metrics: e.target.value })}
              placeholder='{"monthly_revenue": 50000, "customer_count": 100}'
              className="font-mono text-sm"
            />
          </div>
          
          <Button type="submit" disabled={loading}>
            {loading ? 'Saving...' : saved ? 'Saved!' : 'Save Profile'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
