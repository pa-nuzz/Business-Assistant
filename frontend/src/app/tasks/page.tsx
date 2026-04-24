'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { tasks } from '@/lib/api';
import { 
  Plus, 
  CheckCircle2, 
  Circle, 
  Clock, 
  AlertCircle,
  Check,
  LayoutGrid,
  List
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { KanbanBoard } from '@/components/kanban-board';
import { toast } from 'sonner';
import { PageSkeleton } from '@/components/loading-skeletons';

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

const STATUS_LABELS: Record<string, string> = {
  todo: 'To Do',
  in_progress: 'In Progress',
  review: 'In Review',
  done: 'Done',
};

const STATUS_ORDER = ['todo', 'in_progress', 'review', 'done'];

export default function TasksPage() {
  const router = useRouter();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [allTasks, setAllTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNewTaskModal, setShowNewTaskModal] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newTaskPriority, setNewTaskPriority] = useState('medium');
  const [viewMode, setViewMode] = useState<'list' | 'kanban'>('list');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const pageSize = 20;

  // Set page title
  useEffect(() => {
    document.title = 'Tasks | AEIOU AI';
  }, []);

  useEffect(() => {
    fetchDashboard();
  }, [currentPage]);

  const fetchDashboard = async () => {
    try {
      const [dashboard, tasksList] = await Promise.all([
        tasks.getDashboard(),
        tasks.list(undefined, currentPage, pageSize)
      ]);
      setDashboardData(dashboard);
      setAllTasks(tasksList.results || []);
      setTotalPages(tasksList.total_pages || 1);
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
      toast.success('Task created successfully');
      setNewTaskTitle('');
      setShowNewTaskModal(false);
      fetchDashboard();
    } catch (err) {
      console.error('Failed to create task:', err);
      toast.error('Failed to create task');
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
        return <Circle size={18} className="text-slate-400" />;
    }
  };

  if (loading) {
    return <PageSkeleton type="tasks" />;
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 mb-1">Tasks</h1>
            <p className="text-sm text-slate-600">Manage your work and stay organized</p>
          </div>
          <div className="flex items-center gap-3">
            {/* View Toggle */}
            <div className="flex items-center bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('list')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                  viewMode === 'list' 
                    ? 'bg-white text-gray-900 shadow-sm' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <List size={16} />
                <span className="hidden sm:inline">List</span>
              </button>
              <button
                onClick={() => setViewMode('kanban')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                  viewMode === 'kanban' 
                    ? 'bg-white text-gray-900 shadow-sm' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <LayoutGrid size={16} />
                <span className="hidden sm:inline">Board</span>
              </button>
            </div>
            <motion.button
              onClick={() => setShowNewTaskModal(true)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl transition-all duration-200 shadow-sm"
            >
              <Plus size={18} />
              <span className="hidden sm:inline">New Task</span>
            </motion.button>
          </div>
        </div>

        {/* Stats Overview */}
        {dashboardData && (
          <div className="grid grid-cols-4 gap-4 mb-8">
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-5 bg-card rounded-xl border border-border"
            >
              <div className="text-3xl font-bold text-slate-900">
                {dashboardData.counts.by_status.todo || 0}
              </div>
              <div className="text-sm text-slate-500">To Do</div>
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
              <div className="text-sm text-slate-500">In Progress</div>
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
              <div className="text-sm text-slate-500">High Priority</div>
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
              <div className="text-sm text-slate-500">Completed</div>
            </motion.div>
          </div>
        )}

        {/* Tasks Content - List or Kanban View */}
        {viewMode === 'kanban' ? (
          <div className="mb-8">
            <KanbanBoard tasks={allTasks} onUpdate={fetchDashboard} />
          </div>
        ) : (
          <>
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
                      <span className="ml-3 flex-1 text-sm text-slate-900">{task.title}</span>
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
                <h2 className="text-lg font-semibold text-slate-900 mb-4">Today</h2>
                <div className="space-y-2">
                  {dashboardData.today.map((task) => (
                    <TaskCard key={task.id} task={task} getPriorityColor={getPriorityColor} getPriorityBg={getPriorityBg} getStatusIcon={getStatusIcon} onUpdate={fetchDashboard} />
                  ))}
                </div>
              </div>
            )}

            {/* Upcoming Tasks */}
            {dashboardData?.upcoming && dashboardData.upcoming.length > 0 && (
              <div className="mb-8">
                <h2 className="text-lg font-semibold text-slate-900 mb-4">Upcoming</h2>
                <div className="space-y-2">
                  {dashboardData.upcoming.map((task) => (
                    <TaskCard key={task.id} task={task} getPriorityColor={getPriorityColor} getPriorityBg={getPriorityBg} getStatusIcon={getStatusIcon} onUpdate={fetchDashboard} />
                  ))}
                </div>
              </div>
            )}

            {/* All Tasks Grouped by Status */}
            {allTasks.length > 0 && (
              <div className="mt-8">
                <h2 className="text-lg font-semibold text-slate-900 mb-4">All Tasks</h2>
                <div className="space-y-6">
                  {STATUS_ORDER.map((status) => {
                    const statusTasks = allTasks.filter((t) => t.status === status);
                    if (statusTasks.length === 0) return null;
                    return (
                      <div key={status}>
                        <h3 className="text-sm font-medium text-slate-500 mb-3 uppercase tracking-wide">
                          {STATUS_LABELS[status]} ({statusTasks.length})
                        </h3>
                        <div className="space-y-2">
                          {statusTasks.map((task) => (
                            <TaskCard 
                              key={task.id} 
                              task={task} 
                              getPriorityColor={getPriorityColor} 
                              getPriorityBg={getPriorityBg} 
                              getStatusIcon={getStatusIcon} 
                              onUpdate={fetchDashboard} 
                            />
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </>
        )}

        {/* Pagination */}
        {allTasks.length > 0 && (
          <div className="mt-8 flex items-center justify-between">
            <p className="text-sm text-slate-500">
              Page {currentPage} of {totalPages}
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="px-4 py-2 text-sm font-medium text-slate-900 bg-card border border-border rounded-lg hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="px-4 py-2 text-sm font-medium text-slate-900 bg-card border border-border rounded-lg hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Next
              </button>
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
            {/* Animated illustration: 3 empty checkbox outlines */}
            <div className="relative w-24 h-24 mx-auto mb-6">
              <div className="absolute top-0 left-4 w-10 h-10 border-2 border-blue-200 rounded-md transform -rotate-6" />
              <div className="absolute top-3 left-6 w-10 h-10 border-2 border-blue-300 rounded-md transform rotate-3" />
              <div className="absolute top-6 left-8 w-10 h-10 border-2 border-blue-400 rounded-md transform rotate-12" />
            </div>
            <h2 className="text-xl font-semibold text-slate-900 mb-2">No tasks yet</h2>
            <p className="text-sm text-slate-600 mb-6">Create your first task or let AI extract tasks from your conversations</p>
            <div className="flex items-center justify-center gap-3">
              <motion.button
                onClick={() => setShowNewTaskModal(true)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl transition-colors shadow-sm"
              >
                Create task
              </motion.button>
              <motion.button
                onClick={() => router.push('/chat')}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="px-4 py-2 border border-gray-300 hover:border-gray-400 text-gray-700 text-sm font-medium rounded-xl transition-colors"
              >
                Import from chat
              </motion.button>
            </div>
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
              <h2 className="text-xl font-semibold text-slate-900 mb-6">Create New Task</h2>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Task Title *
                </label>
                <input
                  type="text"
                  value={newTaskTitle}
                  onChange={(e) => setNewTaskTitle(e.target.value)}
                  placeholder="What needs to be done?"
                  className="w-full px-4 py-2.5 bg-background border border-border rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-300 focus:ring-2 focus:ring-blue-100"
                  onKeyDown={(e) => e.key === 'Enter' && handleCreateTask()}
                  autoFocus
                />
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-700 mb-2">
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
                          : 'bg-transparent border-border text-slate-600 hover:text-slate-900'
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
                  className="px-4 py-2 text-sm text-slate-600 hover:text-slate-900 transition-colors"
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
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
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
  const [localStatus, setLocalStatus] = useState(task.status);
  
  // Update local status when task prop changes
  useEffect(() => {
    setLocalStatus(task.status);
  }, [task.status]);

  const handleComplete = async () => {
    if (localStatus === 'done') return;
    
    setIsCompleting(true);
    try {
      await tasks.complete(task.id);
      setLocalStatus('done');
      toast.success('Task completed!');
      onUpdate();
    } catch (err) {
      console.error('Failed to complete task:', err);
      toast.error('Failed to complete task');
    } finally {
      setIsCompleting(false);
    }
  };

  const isDone = localStatus === 'done';

  return (
    <motion.div 
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex items-center p-4 rounded-xl border transition-all duration-200 ${
        isDone 
          ? 'bg-green-50/50 border-green-100' 
          : 'bg-card border-border hover:border-blue-200 hover:shadow-sm'
      }`}
    >
      <motion.button
        onClick={handleComplete}
        disabled={isCompleting || isDone}
        whileHover={{ scale: isDone ? 1 : 1.1 }}
        whileTap={{ scale: isDone ? 1 : 0.9 }}
        className={`flex items-center justify-center w-6 h-6 rounded-full border-2 transition-all duration-200 ${
          isDone
            ? 'bg-green-500 border-green-500 cursor-default'
            : 'border-muted-foreground hover:border-green-500 hover:bg-green-50'
        }`}
      >
        <Check size={14} className={isDone ? 'text-white' : 'text-green-600 opacity-0 group-hover:opacity-100'} />
      </motion.button>

      <span className={`ml-3 flex-1 text-sm ${isDone ? 'text-slate-400 line-through' : 'text-slate-900'}`}>
        {task.title}
      </span>
      
      {isDone && (
        <span className="mr-2 px-2 py-0.5 text-xs font-medium text-green-600 bg-green-100 rounded-full">
          Done
        </span>
      )}

      {task.tags.length > 0 && !isDone && (
        <div className="flex gap-1 mr-3">
          {task.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="px-2 py-1 text-xs bg-muted text-slate-600 rounded-md"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {!isDone && (
        <span
          className={`px-2.5 py-1 text-xs font-medium rounded-md capitalize ${getPriorityBg(task.priority)}`}
          style={{ color: getPriorityColor(task.priority) }}
        >
          {task.priority}
        </span>
      )}
    </motion.div>
  );
}
