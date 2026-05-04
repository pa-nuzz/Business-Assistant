"use client";

import { useState, useRef } from "react";
import { motion, useDragControls, PanInfo } from "framer-motion";
import { Check, Trash2, MoreHorizontal, GripHorizontal } from "lucide-react";
import { usePermission } from "@/hooks/use-permission";

interface MobileTask {
  id: string;
  title: string;
  priority: string;
  status: string;
  assignee?: string;
  dueDate?: string;
}

interface MobileKanbanProps {
  tasks: MobileTask[];
  workspaceId?: string;
  onStatusChange: (taskId: string, newStatus: string) => void;
  onDelete: (taskId: string) => void;
  onTaskClick: (taskId: string) => void;
}

const COLUMNS = [
  { id: "todo", label: "To Do", color: "bg-slate-200" },
  { id: "in_progress", label: "In Progress", color: "bg-blue-200" },
  { id: "done", label: "Done", color: "bg-green-200" },
];

export function MobileKanban({
  tasks,
  workspaceId,
  onStatusChange,
  onDelete,
  onTaskClick,
}: MobileKanbanProps) {
  const [activeColumn, setActiveColumn] = useState(1); // Start with middle column
  const { isMember } = usePermission({ workspaceId });
  const [swipedTask, setSwipedTask] = useState<string | null>(null);
  const swipeStart = useRef<number>(0);

  const tasksByStatus = (status: string) =>
    tasks.filter((t) => t.status === status);

  const handleSwipeStart = (taskId: string, x: number) => {
    swipeStart.current = x;
    setSwipedTask(null);
  };

  const handleSwipeMove = (taskId: string, info: PanInfo) => {
    const diff = info.offset.x;
    if (Math.abs(diff) > 60) {
      setSwipedTask(taskId);
    }
  };

  const handleSwipeEnd = (task: MobileTask, info: PanInfo) => {
    const diff = info.offset.x;
    const velocity = info.velocity.x;

    // Swipe right to complete
    if (diff > 80 || velocity > 500) {
      if (task.status !== "done") {
        onStatusChange(task.id, "done");
        hapticFeedback("success");
      }
    }
    // Swipe left to delete
    else if (diff < -80 || velocity < -500) {
      if (isMember) {
        onDelete(task.id);
        hapticFeedback("error");
      }
    }

    setSwipedTask(null);
  };

  return (
    <div className="h-screen flex flex-col bg-slate-50">
      {/* Column tabs */}
      <div className="flex border-b bg-white">
        {COLUMNS.map((col, index) => (
          <button
            key={col.id}
            onClick={() => setActiveColumn(index)}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              activeColumn === index
                ? "text-indigo-600 border-b-2 border-indigo-600"
                : "text-slate-500"
            }`}
          >
            {col.label}
            <span className="ml-1 text-xs text-slate-400">
              ({tasksByStatus(col.id).length})
            </span>
          </button>
        ))}
      </div>

      {/* Task list */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {tasksByStatus(COLUMNS[activeColumn].id).map((task) => (
          <motion.div
            key={task.id}
            drag="x"
            dragConstraints={{ left: 0, right: 0 }}
            dragElastic={0.3}
            onDragStart={(_, info) => handleSwipeStart(task.id, info.point.x)}
            onDrag={(_, info) => handleSwipeMove(task.id, info)}
            onDragEnd={(_, info) => handleSwipeEnd(task, info)}
            onTap={() => onTaskClick(task.id)}
            className={`relative bg-white rounded-lg shadow-sm border p-4 ${
              swipedTask === task.id ? "z-10" : ""
            }`}
            initial={{ x: 0 }}
            animate={{
              x:
                swipedTask === task.id
                  ? undefined
                  : 0,
            }}
          >
            {/* Swipe action indicators */}
            <div className="absolute inset-y-0 left-0 w-16 bg-green-500 rounded-l-lg flex items-center justify-center opacity-0 pointer-events-none">
              <Check className="text-white" />
            </div>
            <div className="absolute inset-y-0 right-0 w-16 bg-red-500 rounded-r-lg flex items-center justify-center opacity-0 pointer-events-none">
              <Trash2 className="text-white" />
            </div>

            <div className="flex items-start gap-3">
              <GripHorizontal className="w-5 h-5 text-slate-300 mt-0.5" />
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-medium text-slate-900 truncate">
                  {task.title}
                </h3>
                <div className="flex items-center gap-2 mt-1.5">
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      task.priority === "high"
                        ? "bg-red-100 text-red-700"
                        : task.priority === "medium"
                        ? "bg-yellow-100 text-yellow-700"
                        : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {task.priority}
                  </span>
                  {task.dueDate && (
                    <span className="text-xs text-slate-400">
                      {task.dueDate}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Swipe hint */}
            <div className="mt-2 text-[10px] text-slate-400 text-center flex items-center justify-center gap-1">
              <span>Swipe right</span>
              <Check className="w-3 h-3" />
              <span>complete</span>
              <span className="mx-1">|</span>
              <span>Swipe left</span>
              <Trash2 className="w-3 h-3" />
            </div>
          </motion.div>
        ))}

        {tasksByStatus(COLUMNS[activeColumn].id).length === 0 && (
          <div className="text-center py-12 text-slate-400">
            <p className="text-sm">No tasks in {COLUMNS[activeColumn].label}</p>
            <p className="text-xs mt-1">Swipe to move tasks between columns</p>
          </div>
        )}
      </div>
    </div>
  );
}

function hapticFeedback(type: "success" | "error" | "light" = "light") {
  if (typeof navigator !== "undefined" && "vibrate" in navigator) {
    switch (type) {
      case "success":
        navigator.vibrate([50, 30, 50]);
        break;
      case "error":
        navigator.vibrate([100, 50, 100]);
        break;
      default:
        navigator.vibrate(20);
    }
  }
}
