import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircle2, 
  Circle, 
  Clock, 
  AlertCircle,
  GripVertical,
  Trash2
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
}

interface KanbanBoardProps {
  tasks: Task[];
  onUpdate: () => void;
}

const COLUMNS = [
  { id: 'todo', label: 'To Do', color: 'bg-gray-100', icon: Circle },
  { id: 'in_progress', label: 'In Progress', color: 'bg-blue-50', icon: Clock },
  { id: 'review', label: 'Review', color: 'bg-orange-50', icon: AlertCircle },
  { id: 'done', label: 'Done', color: 'bg-green-50', icon: CheckCircle2 },
];

const getPriorityColor = (priority: string) => {
  switch (priority) {
    case 'urgent': return 'bg-red-100 text-red-700 border-red-200';
    case 'high': return 'bg-orange-100 text-orange-700 border-orange-200';
    case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
    case 'low': return 'bg-green-100 text-green-700 border-green-200';
    default: return 'bg-gray-100 text-gray-700 border-gray-200';
  }
};

export function KanbanBoard({ tasks, onUpdate }: KanbanBoardProps) {
  const [activeTask, setActiveTask] = useState<string | null>(null);

  const handleDragEnd = async (taskId: string, newStatus: string) => {
    try {
      await tasksApi.update(taskId, { status: newStatus });
      toast.success(`Task moved to ${COLUMNS.find(c => c.id === newStatus)?.label}`);
      onUpdate();
    } catch (err) {
      toast.error('Failed to move task');
    }
  };

  const handleDelete = async (taskId: string) => {
    if (!confirm('Are you sure you want to delete this task?')) return;
    
    try {
      await tasksApi.delete(taskId);
      toast.success('Task deleted');
      onUpdate();
    } catch (err) {
      toast.error('Failed to delete task');
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {COLUMNS.map((column) => {
        const columnTasks = tasks.filter((t) => t.status === column.id);
        const Icon = column.icon;

        return (
          <motion.div
            key={column.id}
            layout
            className={`${column.color} rounded-xl p-4 min-h-[400px]`}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Icon className="w-5 h-5 text-gray-600" />
                <h3 className="font-semibold text-gray-700">{column.label}</h3>
              </div>
              <span className="text-xs font-medium text-gray-500 bg-white px-2 py-1 rounded-full">
                {columnTasks.length}
              </span>
            </div>

            <div className="space-y-3">
              <AnimatePresence mode="popLayout">
                {columnTasks.map((task) => (
                  <motion.div
                    key={task.id}
                    layout
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    whileHover={{ y: -2, boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                    draggable
                    onDragStart={() => setActiveTask(task.id)}
                    onDragEnd={(e: any) => {
                      const dropTarget = document.elementFromPoint(e.clientX, e.clientY);
                      const columnElement = dropTarget?.closest('[data-column-id]');
                      if (columnElement) {
                        const newStatus = columnElement.getAttribute('data-column-id');
                        if (newStatus && newStatus !== task.status) {
                          handleDragEnd(task.id, newStatus);
                        }
                      }
                      setActiveTask(null);
                    }}
                    className={`bg-white rounded-lg p-3 shadow-sm border border-gray-200 cursor-move ${
                      activeTask === task.id ? 'opacity-50 rotate-2' : ''
                    }`}
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
                  </motion.div>
                ))}
              </AnimatePresence>
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
