"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Sparkles, Check, X, AlertCircle, Clock, 
  FileText, MessageSquare, ArrowRight
} from "lucide-react";
import { Button } from "@/components/ui/button";
import api from "@/lib/api";
import { toast } from "sonner";

interface AITaskSuggestion {
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  due_date?: string;
  confidence: number;
  source_context: string;
  extracted_keywords: string[];
}

interface AITaskSuggestionsProps {
  sourceType: 'chat' | 'document';
  sourceId: string;
  messageContent?: string;
  onTasksCreated?: () => void;
  autoTrigger?: boolean;
}

export function AITaskSuggestions({
  sourceType,
  sourceId,
  messageContent,
  onTasksCreated,
  autoTrigger = false
}: AITaskSuggestionsProps) {
  const [suggestions, setSuggestions] = useState<AITaskSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [createdCount, setCreatedCount] = useState(0);

  const generateSuggestions = async () => {
    setLoading(true);
    try {
      let response;
      if (sourceType === 'chat') {
        response = await api.post(
          `/conversations/${sourceId}/generate-tasks/`,
          { message_content: messageContent }
        );
      } else {
        response = await api.post(`/documents/${sourceId}/generate-tasks/`);
      }
      
      const data = response.data;
      setSuggestions(data.suggestions || []);
      setShowSuggestions(true);
      
      if (data.suggestions?.length === 0) {
        toast.info("No task suggestions found in this content");
      }
    } catch (error) {
      toast.error("Failed to generate task suggestions");
    } finally {
      setLoading(false);
    }
  };

  const createAllTasks = async () => {
    setLoading(true);
    try {
      let response;
      if (sourceType === 'chat') {
        response = await api.post(
          `/conversations/${sourceId}/generate-tasks/?auto_create=true`,
          { message_content: messageContent }
        );
      } else {
        response = await api.post(`/documents/${sourceId}/generate-tasks/?auto_create=true`);
      }
      
      const data = response.data;
      setCreatedCount(data.tasks_created || 0);
      setSuggestions([]);
      setShowSuggestions(false);
      
      if (data.tasks_created > 0) {
        toast.success(`Created ${data.tasks_created} tasks from AI suggestions`);
        onTasksCreated?.();
      }
    } catch (error) {
      toast.error("Failed to create tasks");
    } finally {
      setLoading(false);
    }
  };

  const dismissSuggestions = () => {
    setShowSuggestions(false);
    setSuggestions([]);
  };

  useEffect(() => {
    if (autoTrigger && (messageContent || sourceType === 'document')) {
      generateSuggestions();
    }
  }, [autoTrigger, messageContent, sourceId]);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'text-red-500 bg-red-50';
      case 'high': return 'text-orange-500 bg-orange-50';
      case 'medium': return 'text-yellow-500 bg-yellow-50';
      default: return 'text-blue-500 bg-blue-50';
    }
  };

  const SourceIcon = sourceType === 'chat' ? MessageSquare : FileText;

  if (!showSuggestions && !loading) {
    return (
      <Button
        variant="ghost"
        size="sm"
        onClick={generateSuggestions}
        className="gap-2 text-primary hover:text-primary"
      >
        <Sparkles className="h-4 w-4" />
        <span className="hidden sm:inline">Generate tasks with AI</span>
        <span className="sm:hidden">AI Tasks</span>
      </Button>
    );
  }

  return (
    <AnimatePresence>
      {showSuggestions && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="bg-gradient-to-br from-purple-50 to-blue-50 border border-purple-200 rounded-xl p-4 space-y-3"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center">
                <Sparkles className="h-4 w-4 text-purple-600" />
              </div>
              <div>
                <p className="font-medium text-sm">AI Task Suggestions</p>
                <p className="text-xs text-muted-foreground">
                  Found {suggestions.length} potential tasks
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={dismissSuggestions}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <div className="space-y-2 max-h-60 overflow-y-auto">
            {suggestions.map((suggestion, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white rounded-lg p-3 border border-purple-100 shadow-sm"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">{suggestion.title}</p>
                    <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                      {suggestion.description}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${getPriorityColor(suggestion.priority)}`}>
                        {suggestion.priority}
                      </span>
                      {suggestion.due_date && (
                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {new Date(suggestion.due_date).toLocaleDateString()}
                        </span>
                      )}
                      <span className="text-xs text-muted-foreground">
                        {(suggestion.confidence * 100).toFixed(0)}% match
                      </span>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-purple-200">
            <p className="text-xs text-muted-foreground">
              <SourceIcon className="h-3 w-3 inline mr-1" />
              Generated from {sourceType === 'chat' ? 'chat message' : 'document'}
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={dismissSuggestions}
              >
                Dismiss
              </Button>
              <Button
                size="sm"
                onClick={createAllTasks}
                disabled={loading || suggestions.length === 0}
                className="gap-1"
              >
                {loading ? (
                  <>
                    <div className="h-3 w-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    Create {suggestions.length} Task{suggestions.length !== 1 ? 's' : ''}
                    <ArrowRight className="h-3 w-3" />
                  </>
                )}
              </Button>
            </div>
          </div>
        </motion.div>
      )}

      {loading && suggestions.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="flex items-center gap-2 text-muted-foreground"
        >
          <div className="h-4 w-4 border-2 border-purple-200 border-t-purple-500 rounded-full animate-spin" />
          <span className="text-sm">Analyzing content for tasks...</span>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
