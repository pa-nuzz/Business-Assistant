"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  X, MessageCircle, CheckSquare, Clock, FileText, 
  MessageSquare, Send, Play, Square, Plus, Trash2,
  Edit2, MoreHorizontal, Calendar, User, Link as LinkIcon
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import api from "@/lib/api";
import { toast } from "sonner";

interface TaskDetailPanelProps {
  taskId: string;
  isOpen: boolean;
  onClose: () => void;
  onUpdate?: () => void;
}

interface TaskDetails {
  id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  due_date?: string;
  assignee?: string;
  comments: Comment[];
  subtasks: Subtask[];
  time_entries: TimeEntry[];
  linked_documents: Document[];
  linked_conversations: Conversation[];
  total_time_logged: number;
  subtasks_completed: number;
  subtasks_total: number;
}

interface Comment {
  id: string;
  content: string;
  author: string;
  created_at: string;
  is_edited: boolean;
  mentions: string[];
  replies: Reply[];
}

interface Reply {
  id: string;
  content: string;
  author: string;
  created_at: string;
  is_edited: boolean;
}

interface Subtask {
  id: string;
  title: string;
  description: string;
  status: 'todo' | 'in_progress' | 'done';
  assignee?: string;
  due_date?: string;
}

interface TimeEntry {
  id: string;
  user: string;
  start_time: string;
  end_time?: string;
  duration_minutes: number;
  description: string;
  is_manual: boolean;
}

interface Document {
  id: string;
  title: string;
  file_type: string;
}

interface Conversation {
  id: string;
  title: string;
}

export function TaskDetailPanel({ taskId, isOpen, onClose, onUpdate }: TaskDetailPanelProps) {
  const [details, setDetails] = useState<TaskDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [newComment, setNewComment] = useState('');
  const [newSubtask, setNewSubtask] = useState('');
  const [activeTimer, setActiveTimer] = useState<TimeEntry | null>(null);
  const [timerRunning, setTimerRunning] = useState(false);

  useEffect(() => {
    if (isOpen && taskId) {
      fetchTaskDetails();
      fetchActiveTimer();
    }
  }, [isOpen, taskId]);

  const fetchTaskDetails = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/tasks/${taskId}/details/`);
      setDetails(response.data);
    } catch (error) {
      toast.error('Failed to load task details');
    } finally {
      setLoading(false);
    }
  };

  const fetchActiveTimer = async () => {
    try {
      const response = await api.get('/tasks/timer/active/');
      if (response.data.active !== false && response.data.task_id === taskId) {
        setActiveTimer(response.data);
        setTimerRunning(true);
      }
    } catch (error) {
      // No active timer
    }
  };

  const addComment = async () => {
    if (!newComment.trim()) return;
    
    try {
      await api.post(`/tasks/${taskId}/comments/add/`, { content: newComment });
      setNewComment('');
      fetchTaskDetails();
      onUpdate?.();
    } catch (error) {
      toast.error('Failed to add comment');
    }
  };

  const addSubtask = async () => {
    if (!newSubtask.trim()) return;
    
    try {
      await api.post(`/tasks/${taskId}/subtasks/add/`, { title: newSubtask });
      setNewSubtask('');
      fetchTaskDetails();
      onUpdate?.();
    } catch (error) {
      toast.error('Failed to add subtask');
    }
  };

  const updateSubtask = async (subtaskId: string, status: string) => {
    try {
      await api.patch(`/tasks/subtasks/${subtaskId}/update/`, { status });
      fetchTaskDetails();
      onUpdate?.();
    } catch (error) {
      toast.error('Failed to update subtask');
    }
  };

  const startTimer = async () => {
    try {
      const response = await api.post(`/tasks/${taskId}/timer/start/`);
      if (response.data.error) {
        toast.error(response.data.error);
        return;
      }
      setActiveTimer(response.data);
      setTimerRunning(true);
      toast.success('Timer started');
    } catch (error) {
      toast.error('Failed to start timer');
    }
  };

  const stopTimer = async () => {
    if (!activeTimer) return;
    
    try {
      await api.post(`/tasks/timer/${activeTimer.id}/stop/`);
      setTimerRunning(false);
      setActiveTimer(null);
      fetchTaskDetails();
      toast.success('Timer stopped');
    } catch (error) {
      toast.error('Failed to stop timer');
    }
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'done': return 'bg-green-100 text-green-700';
      case 'in_progress': return 'bg-blue-100 text-blue-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className="fixed inset-y-0 right-0 w-full md:w-[600px] bg-background border-l shadow-2xl z-50 flex flex-col"
      >
        {/* Header */}
        <div className="h-16 border-b flex items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${getStatusColor(details?.status || 'todo')}`} />
            <h2 className="font-semibold truncate max-w-md">
              {loading ? 'Loading...' : details?.title}
            </h2>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
          <TabsList className="mx-6 mt-4 justify-start">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="comments">
              Comments
              {(details?.comments?.length || 0) > 0 && (
                <span className="ml-1 text-xs bg-muted px-1.5 py-0.5 rounded">
                  {details?.comments?.length || 0}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger value="subtasks">
              Subtasks
              {(details?.subtasks_total || 0) > 0 && (
                <span className="ml-1 text-xs bg-muted px-1.5 py-0.5 rounded">
                  {details?.subtasks_completed || 0}/{details?.subtasks_total || 0}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger value="time">Time</TabsTrigger>
          </TabsList>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {loading ? (
              <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-20 bg-muted rounded animate-pulse" />
                ))}
              </div>
            ) : !details ? (
              <p className="text-muted-foreground">Failed to load task details</p>
            ) : (
              <>
                <TabsContent value="overview" className="mt-0 space-y-6">
                  {/* Description */}
                  <div>
                    <h3 className="text-sm font-medium mb-2">Description</h3>
                    <p className="text-sm text-muted-foreground">
                      {details.description || 'No description'}
                    </p>
                  </div>

                  {/* Quick Stats */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-muted rounded-lg p-3">
                      <div className="flex items-center gap-2 text-muted-foreground mb-1">
                        <Clock className="h-4 w-4" />
                        <span className="text-xs">Time Logged</span>
                      </div>
                      <p className="text-lg font-semibold">
                        {formatDuration(details.total_time_logged)}
                      </p>
                    </div>
                    <div className="bg-muted rounded-lg p-3">
                      <div className="flex items-center gap-2 text-muted-foreground mb-1">
                        <CheckSquare className="h-4 w-4" />
                        <span className="text-xs">Subtasks</span>
                      </div>
                      <p className="text-lg font-semibold">
                        {details.subtasks_completed}/{details.subtasks_total}
                      </p>
                    </div>
                  </div>

                  {/* Timer Control */}
                  <div className="flex items-center justify-between bg-primary/5 rounded-lg p-4">
                    <div>
                      <p className="font-medium">Time Tracking</p>
                      <p className="text-sm text-muted-foreground">
                        {timerRunning ? 'Timer is running' : 'Start tracking your time'}
                      </p>
                    </div>
                    <Button
                      variant={timerRunning ? 'destructive' : 'default'}
                      size="sm"
                      onClick={timerRunning ? stopTimer : startTimer}
                      className="gap-2"
                    >
                      {timerRunning ? (
                        <>
                          <Square className="h-4 w-4" />
                          Stop
                        </>
                      ) : (
                        <>
                          <Play className="h-4 w-4" />
                          Start
                        </>
                      )}
                    </Button>
                  </div>

                  {/* Linked Resources */}
                  {(details.linked_documents.length > 0 || details.linked_conversations.length > 0) && (
                    <div>
                      <h3 className="text-sm font-medium mb-3">Linked Resources</h3>
                      <div className="space-y-2">
                        {details.linked_documents.map((doc) => (
                          <div key={doc.id} className="flex items-center gap-2 text-sm">
                            <FileText className="h-4 w-4 text-muted-foreground" />
                            <span>{doc.title}</span>
                          </div>
                        ))}
                        {details.linked_conversations.map((conv) => (
                          <div key={conv.id} className="flex items-center gap-2 text-sm">
                            <MessageSquare className="h-4 w-4 text-muted-foreground" />
                            <span>{conv.title}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="comments" className="mt-0 space-y-4">
                  {/* Add Comment */}
                  <div className="flex gap-2">
                    <Textarea
                      placeholder="Add a comment..."
                      value={newComment}
                      onChange={(e) => setNewComment(e.target.value)}
                      className="min-h-[80px]"
                    />
                    <Button 
                      size="icon" 
                      className="shrink-0"
                      onClick={addComment}
                      disabled={!newComment.trim()}
                    >
                      <Send className="h-4 w-4" />
                    </Button>
                  </div>

                  {/* Comments List */}
                  <div className="space-y-4">
                    {details.comments.map((comment) => (
                      <div key={comment.id} className="bg-muted rounded-lg p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-medium">
                              {comment.author[0].toUpperCase()}
                            </div>
                            <div>
                              <p className="font-medium text-sm">{comment.author}</p>
                              <p className="text-xs text-muted-foreground">
                                {new Date(comment.created_at).toLocaleString()}
                                {comment.is_edited && ' (edited)'}
                              </p>
                            </div>
                          </div>
                        </div>
                        <p className="text-sm">{comment.content}</p>
                        
                        {/* Replies */}
                        {comment.replies.length > 0 && (
                          <div className="mt-3 ml-8 space-y-2">
                            {comment.replies.map((reply) => (
                              <div key={reply.id} className="bg-background rounded-lg p-3 text-sm">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="font-medium">{reply.author}</span>
                                  <span className="text-xs text-muted-foreground">
                                    {new Date(reply.created_at).toLocaleString()}
                                  </span>
                                </div>
                                <p>{reply.content}</p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="subtasks" className="mt-0 space-y-4">
                  {/* Add Subtask */}
                  <div className="flex gap-2">
                    <Input
                      placeholder="Add a subtask..."
                      value={newSubtask}
                      onChange={(e) => setNewSubtask(e.target.value)}
                    />
                    <Button 
                      size="icon"
                      onClick={addSubtask}
                      disabled={!newSubtask.trim()}
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>

                  {/* Subtasks List */}
                  <div className="space-y-2">
                    {details.subtasks.map((subtask) => (
                      <div 
                        key={subtask.id}
                        className="flex items-center gap-3 p-3 bg-muted rounded-lg"
                      >
                        <button
                          onClick={() => updateSubtask(subtask.id, subtask.status === 'done' ? 'todo' : 'done')}
                          className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                            subtask.status === 'done'
                              ? 'bg-green-500 border-green-500'
                              : 'border-gray-300 hover:border-primary'
                          }`}
                        >
                          {subtask.status === 'done' && (
                            <CheckSquare className="h-3 w-3 text-white" />
                          )}
                        </button>
                        <div className="flex-1">
                          <p className={`text-sm ${subtask.status === 'done' ? 'line-through text-muted-foreground' : ''}`}>
                            {subtask.title}
                          </p>
                          {subtask.assignee && (
                            <p className="text-xs text-muted-foreground">
                              Assigned to {subtask.assignee}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="time" className="mt-0 space-y-4">
                  {/* Time Entries */}
                  <div className="space-y-2">
                    {details.time_entries.map((entry) => (
                      <div 
                        key={entry.id}
                        className="flex items-center justify-between p-3 bg-muted rounded-lg"
                      >
                        <div>
                          <p className="text-sm font-medium">
                            {formatDuration(entry.duration_minutes)}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(entry.start_time).toLocaleDateString()}
                            {entry.is_manual && ' (manual)'}
                          </p>
                          {entry.description && (
                            <p className="text-xs text-muted-foreground mt-1">
                              {entry.description}
                            </p>
                          )}
                        </div>
                        <Button 
                          variant="ghost" 
                          size="icon"
                          onClick={async () => {
                            try {
                              await api.delete(`/tasks/time/${entry.id}/delete/`);
                              fetchTaskDetails();
                            } catch {
                              toast.error('Failed to delete entry');
                            }
                          }}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </TabsContent>
              </>
            )}
          </div>
        </Tabs>
      </motion.div>
    </AnimatePresence>
  );
}
