'use client';

import { useState, useEffect } from 'react';
import { tasks } from '@/lib/api';
import { 
  Plus, 
  CheckCircle2, 
  Circle, 
  Clock, 
  AlertCircle,
  Check
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface Task {
  id: string;
  title: string;
  status: 'todo' | 'in_progress' | 'review' | 'done';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  due_date?: string;
  assignee?: string;
  tags: string[];
}

interface DashboardData {
  counts: {
    total: number;
    by_status: Record<string, number>;
    by_priority: Record<string, number>;
  };
  overdue: Array<Task & { days_overdue: number }>;
  today: Task[];
  upcoming: Task[];
}

export default function TasksPage() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showNewTaskModal, setShowNewTaskModal] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newTaskPriority, setNewTaskPriority] = useState('medium');

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const data = await tasks.getDashboard();
      setDashboardData(data);
    } catch (err) {
      console.error('Failed to fetch dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTask = async () => {
    if (!newTaskTitle.trim()) return;
    
    try {
      await tasks.create({
        title: newTaskTitle,
        priority: newTaskPriority,
      });
      setNewTaskTitle('');
      setShowNewTaskModal(false);
      fetchDashboard();
    } catch (err) {
      console.error('Failed to create task:', err);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return '#ef4444';
      case 'high': return '#f97316';
      case 'medium': return '#eab308';
      case 'low': return '#22c55e';
      default: return '#8a8a8f';
    }
  };

  const getPriorityBg = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-50';
      case 'high': return 'bg-orange-50';
      case 'medium': return 'bg-amber-50';
      case 'low': return 'bg-green-50';
      default: return 'bg-gray-50';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'done':
        return <CheckCircle2 size={18} className="text-green-600" />;
      case 'in_progress':
        return <Clock size={18} className="text-blue-600" />;
      case 'review':
        return <AlertCircle size={18} className="text-orange-600" />;
      default:
        return <Circle size={18} className="text-muted-foreground" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-10 h-10 border-3 border-muted border-t-blue-600 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-foreground mb-1">Tasks</h1>
            <p className="text-sm text-muted-foreground">Manage your work and stay organized</p>
          </div>
          <motion.button
            onClick={() => setShowNewTaskModal(true)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl transition-all duration-200 shadow-sm"
          >
            <Plus size={18} />
            New Task
          </motion.button>
        </div>

        {/* Stats Overview */}
        {dashboardData && (
          <div className="grid grid-cols-4 gap-4 mb-8">
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-5 bg-card rounded-xl border border-border"
            >
              <div className="text-3xl font-bold text-foreground">
                {dashboardData.counts.by_status.todo || 0}
              </div>
              <div className="text-sm text-muted-foreground">To Do</div>
            </motion.div>
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
              className="p-5 bg-card rounded-xl border border-border"
            >
              <div className="text-3xl font-bold text-blue-600">
                {dashboardData.counts.by_status.in_progress || 0}
              </div>
              <div className="text-sm text-muted-foreground">In Progress</div>
            </motion.div>
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="p-5 bg-card rounded-xl border border-border"
            >
              <div className="text-3xl font-bold text-orange-600">
                {(dashboardData.counts.by_priority.high || 0) + (dashboardData.counts.by_priority.urgent || 0)}
              </div>
              <div className="text-sm text-muted-foreground">High Priority</div>
            </motion.div>
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
              className="p-5 bg-card rounded-xl border border-border"
            >
              <div className="text-3xl font-bold text-green-600">
                {dashboardData.counts.by_status.done || 0}
              </div>
              <div className="text-sm text-muted-foreground">Completed</div>
            </motion.div>
          </div>
        )}

        {/* Overdue Tasks */}
        {dashboardData?.overdue && dashboardData.overdue.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-red-600 mb-4 flex items-center gap-2">
              <AlertCircle size={20} />
              Overdue ({dashboardData.overdue.length})
            </h2>
            <div className="space-y-2">
              {dashboardData.overdue.map((task) => (
                <motion.div
                  key={task.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center p-4 bg-red-50 border border-red-100 rounded-xl"
                >
                  {getStatusIcon(task.status)}
                  <span className="ml-3 flex-1 text-sm text-foreground">{task.title}</span>
                  <span className="text-xs text-red-600 font-medium">
                    {task.days_overdue} days overdue
                  </span>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Today's Tasks */}
        {dashboardData?.today && dashboardData.today.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-foreground mb-4">Today</h2>
            <div className="space-y-2">
              {dashboardData.today.map((task) => (
                <TaskCard key={task.id} task={task} getPriorityColor={getPriorityColor} getPriorityBg={getPriorityBg} getStatusIcon={getStatusIcon} onUpdate={fetchDashboard} />
              ))}
            </div>
          </div>
        )}

        {/* Upcoming Tasks */}
        {dashboardData?.upcoming && dashboardData.upcoming.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold text-foreground mb-4">Upcoming</h2>
            <div className="space-y-2">
              {dashboardData.upcoming.map((task) => (
                <TaskCard key={task.id} task={task} getPriorityColor={getPriorityColor} getPriorityBg={getPriorityBg} getStatusIcon={getStatusIcon} onUpdate={fetchDashboard} />
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {dashboardData && 
         dashboardData.today.length === 0 && 
         dashboardData.upcoming.length === 0 && 
         dashboardData.overdue.length === 0 && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-20"
          >
            <div className="w-20 h-20 rounded-2xl bg-muted flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 size={40} className="text-muted-foreground" />
            </div>
            <p className="text-lg font-medium text-foreground mb-1">No tasks yet</p>
            <p className="text-sm text-muted-foreground">Create your first task to get started</p>
          </motion.div>
        )}
      </div>

      {/* New Task Modal */}
      <AnimatePresence>
        {showNewTaskModal && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowNewTaskModal(false)}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-card rounded-2xl border border-border shadow-2xl z-50 p-6"
            >
              <h2 className="text-xl font-semibold text-foreground mb-6">Create New Task</h2>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-muted-foreground mb-2">
                  Task Title *
                </label>
                <input
                  type="text"
                  value={newTaskTitle}
                  onChange={(e) => setNewTaskTitle(e.target.value)}
                  placeholder="What needs to be done?"
                  className="w-full px-4 py-2.5 bg-background border border-border rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-blue-300 focus:ring-2 focus:ring-blue-100"
                  onKeyDown={(e) => e.key === 'Enter' && handleCreateTask()}
                  autoFocus
                />
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-muted-foreground mb-2">
                  Priority
                </label>
                <div className="flex gap-2">
                  {['low', 'medium', 'high', 'urgent'].map((p) => (
                    <motion.button
                      key={p}
                      onClick={() => setNewTaskPriority(p)}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className={`px-4 py-2 text-sm rounded-lg border transition-all duration-200 capitalize ${
                        newTaskPriority === p 
                          ? `${getPriorityBg(p)} border-current` 
                          : 'bg-transparent border-border text-muted-foreground hover:text-foreground'
                      }`}
                      style={{
                        borderColor: newTaskPriority === p ? getPriorityColor(p) : undefined,
                        color: newTaskPriority === p ? getPriorityColor(p) : undefined,
                      }}
                    >
                      {p}
                    </motion.button>
                  ))}
                </div>
              </div>

              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setShowNewTaskModal(false)}
                  className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Cancel
                </button>
                <motion.button
                  onClick={handleCreateTask}
                  disabled={!newTaskTitle.trim()}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-xl transition-colors disabled:opacity-50 shadow-sm"
                >
                  Create Task
                </motion.button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

// Task Card Component
function TaskCard({ 
  task, 
  getPriorityColor, 
  getPriorityBg,
  getStatusIcon,
  onUpdate 
}: { 
  task: Task; 
  getPriorityColor: (p: string) => string;
  getPriorityBg: (p: string) => string;
  getStatusIcon: (s: string) => React.ReactNode;
  onUpdate: () => void;
}) {
  const [isCompleting, setIsCompleting] = useState(false);

  const handleComplete = async () => {
    setIsCompleting(true);
    try {
      await tasks.complete(task.id);
      onUpdate();
    } catch (err) {
      console.error('Failed to complete task:', err);
    } finally {
      setIsCompleting(false);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center p-4 bg-card rounded-xl border border-border hover:border-blue-200 hover:shadow-sm transition-all duration-200"
    >
      <motion.button
        onClick={handleComplete}
        disabled={isCompleting}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        className="flex items-center justify-center w-6 h-6 rounded-full border-2 border-muted-foreground hover:border-green-500 hover:bg-green-50 transition-all duration-200 disabled:opacity-50 group"
      >
        <Check size={14} className="text-green-600 opacity-0 group-hover:opacity-100 transition-opacity" />
      </motion.button>

      <span className="ml-3 flex-1 text-sm text-foreground">{task.title}</span>

      {task.tags.length > 0 && (
        <div className="flex gap-1 mr-3">
          {task.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="px-2 py-1 text-xs bg-muted text-muted-foreground rounded-md"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      <span
        className={`px-2.5 py-1 text-xs font-medium rounded-md capitalize ${getPriorityBg(task.priority)}`}
        style={{ color: getPriorityColor(task.priority) }}
      >
        {task.priority}
      </span>
    </motion.div>
  );
}
