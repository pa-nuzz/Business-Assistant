'use client';

import { useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence, Reorder } from 'framer-motion';
import { 
  CheckCircle2, 
  Circle, 
  Clock, 
  AlertCircle,
  GripVertical,
  Trash2,
  User,
  Calendar,
  AlertTriangle,
  Layers
} from 'lucide-react';
import { tasks as tasksApi } from '@/lib/api';
import { toast } from 'sonner';

interface Task {
  id: string;
  title: string;
  status: 'todo' | 'in_progress' | 'review' | 'done';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  due_date?: string;
  assignee?: string;
  tags: string[];
  swimlane?: string;
}

interface KanbanBoardProps {
  tasks: Task[];
  onUpdate: () => void;
  columnLimits?: Record<string, number>; // WIP limits per column
  enableSwimlanes?: boolean;
}

const COLUMNS = [
  { id: 'todo', label: 'To Do', color: 'bg-gray-100', icon: Circle, limit: 10 },
  { id: 'in_progress', label: 'In Progress', color: 'bg-blue-50', icon: Clock, limit: 5 },
  { id: 'review', label: 'Review', color: 'bg-orange-50', icon: AlertCircle, limit: 8 },
  { id: 'done', label: 'Done', color: 'bg-green-50', icon: CheckCircle2, limit: null },
];

const SWIMLANES = ['Standard', 'Urgent', 'Backlog'];

const getPriorityColor = (priority: string) => {
  switch (priority) {
    case 'urgent': return 'bg-red-100 text-red-700 border-red-200';
    case 'high': return 'bg-orange-100 text-orange-700 border-orange-200';
    case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
    case 'low': return 'bg-green-100 text-green-700 border-green-200';
    default: return 'bg-gray-100 text-gray-700 border-gray-200';
  }
};

const getPriorityOrder = (priority: string) => {
  switch (priority) {
    case 'urgent': return 0;
    case 'high': return 1;
    case 'medium': return 2;
    case 'low': return 3;
    default: return 4;
  }
};

export function KanbanBoard({ 
  tasks, 
  onUpdate, 
  columnLimits = {},
  enableSwimlanes = false 
}: KanbanBoardProps) {
  const [draggedTask, setDraggedTask] = useState<string | null>(null);
  const [dropTarget, setDropTarget] = useState<string | null>(null);
  const [optimisticTasks, setOptimisticTasks] = useState<Task[] | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);

  // Use optimistic tasks if available, otherwise use props
  const displayTasks = optimisticTasks || tasks;

  // Sort tasks by priority within each column
  const sortedTasks = useMemo(() => {
    return [...displayTasks].sort((a, b) => {
      const statusOrder = ['todo', 'in_progress', 'review', 'done'];
      const statusDiff = statusOrder.indexOf(a.status) - statusOrder.indexOf(b.status);
      if (statusDiff !== 0) return statusDiff;
      
      // Within same status, sort by priority (urgent first)
      const priorityDiff = getPriorityOrder(a.priority) - getPriorityOrder(b.priority);
      if (priorityDiff !== 0) return priorityDiff;
      
      // Then by swimlane if enabled
      if (enableSwimlanes && a.swimlane !== b.swimlane) {
        return (a.swimlane || '').localeCompare(b.swimlane || '');
      }
      
      return 0;
    });
  }, [displayTasks, enableSwimlanes]);

  const handleDragStart = (taskId: string) => {
    setDraggedTask(taskId);
  };

  const handleDragOver = (columnId: string) => {
    setDropTarget(columnId);
  };

  const handleDragEnd = useCallback(async (taskId: string, newStatus: string) => {
    const task = displayTasks.find(t => t.id === taskId);
    if (!task || task.status === newStatus) {
      setDraggedTask(null);
      setDropTarget(null);
      return;
    }

    // Check WIP limits
    const column = COLUMNS.find(c => c.id === newStatus);
    const limit = columnLimits[newStatus] || column?.limit;
    const columnTaskCount = displayTasks.filter(t => t.status === newStatus).length;
    
    if (limit && columnTaskCount >= limit) {
      toast.error(`${column?.label} is at capacity (${limit} tasks). Move a task out first.`);
      setDraggedTask(null);
      setDropTarget(null);
      return;
    }

    // Optimistic update
    const originalTasks = displayTasks;
    const updatedTasks = displayTasks.map(t => 
      t.id === taskId ? { ...t, status: newStatus as Task['status'] } : t
    );
    setOptimisticTasks(updatedTasks);
    setIsUpdating(true);

    try {
      await tasksApi.update(taskId, { status: newStatus });
      toast.success(`Task moved to ${column?.label}`);
      onUpdate();
    } catch {
      // Rollback on error
      setOptimisticTasks(originalTasks);
      toast.error('Failed to move task - changes reverted');
    } finally {
      setIsUpdating(false);
      setDraggedTask(null);
      setDropTarget(null);
    }
  }, [displayTasks, columnLimits, onUpdate]);

  const handleDelete = async (taskId: string) => {
    if (!confirm('Are you sure you want to delete this task?')) return;
    
    // Optimistic delete
    const originalTasks = displayTasks;
    setOptimisticTasks(displayTasks.filter(t => t.id !== taskId));
    
    try {
      await tasksApi.delete(taskId);
      toast.success('Task deleted');
      onUpdate();
    } catch {
      setOptimisticTasks(originalTasks);
      toast.error('Failed to delete task');
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {COLUMNS.map((column) => {
        const columnTasks = sortedTasks.filter((t) => t.status === column.id);
        const Icon = column.icon;
        const isDropTarget = dropTarget === column.id;
        const limit = columnLimits[column.id] || column.limit;
        const isAtLimit = limit && columnTasks.length >= limit;

        return (
          <motion.div
            key={column.id}
            layout
            data-column={column.id}
            className={`${column.color} rounded-xl p-4 min-h-[400px] transition-all ${
              isDropTarget ? 'ring-2 ring-primary ring-offset-2' : ''
            } ${isAtLimit && isDropTarget ? 'ring-red-400 bg-red-50/50' : ''}`}
            onDragOver={(e) => {
              e.preventDefault();
              handleDragOver(column.id);
            }}
            onDragLeave={() => setDropTarget(null)}
            onDrop={(e) => {
              e.preventDefault();
              const taskId = e.dataTransfer.getData('taskId');
              if (taskId) handleDragEnd(taskId, column.id);
            }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Icon className="w-5 h-5 text-gray-600" />
                <h3 className="font-semibold text-gray-700">{column.label}</h3>
              </div>
              <div className="flex items-center gap-2">
                {isAtLimit && (
                  <AlertTriangle className="w-4 h-4 text-red-500" />
                )}
                <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                  isAtLimit ? 'bg-red-100 text-red-700' : 'bg-white text-gray-500'
                }`}>
                  {columnTasks.length}{limit ? `/${limit}` : ''}
                </span>
              </div>
            </div>

            <div className="space-y-3">
              {columnTasks.map((task) => (
                <div
                  key={task.id}
                  className={`bg-white rounded-lg p-3 shadow-sm border border-gray-200 cursor-move transition-all animate-in fade-in slide-in-from-top-2 ${
                    draggedTask === task.id ? 'opacity-50 rotate-2 scale-95' : ''
                  } ${isUpdating ? 'pointer-events-none' : 'hover:shadow-md'}`}
                  draggable={!isUpdating}
                  onDragStart={(e: React.DragEvent<HTMLDivElement>) => {
                    setDraggedTask(task.id);
                    e.dataTransfer.setData('taskId', task.id);
                    e.dataTransfer.effectAllowed = 'move';
                  }}
                  onDragEnd={() => {
                    setDraggedTask(null);
                    setDropTarget(null);
                  }}
                >
                  <div className="flex items-start gap-2">
                    <GripVertical className="w-4 h-4 text-gray-400 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-800 truncate">
                        {task.title}
                      </p>
                      {task.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {task.tags.slice(0, 2).map((tag) => (
                            <span
                              key={tag}
                              className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                      <div className="flex items-center justify-between mt-2">
                        <span className={`text-[10px] px-2 py-0.5 rounded-full border ${getPriorityColor(task.priority)}`}>
                          {task.priority}
                        </span>
                        <button
                          onClick={() => handleDelete(task.id)}
                          className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Drop zone indicator */}
            <div 
              data-column-id={column.id}
              className="mt-3 border-2 border-dashed border-gray-300 rounded-lg p-4 text-center text-xs text-gray-400 hover:border-gray-400 hover:text-gray-500 transition-colors"
            >
              Drop here
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
