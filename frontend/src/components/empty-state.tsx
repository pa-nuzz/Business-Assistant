import { FileText, MessageSquare, BarChart3, FolderOpen, Upload } from 'lucide-react';

interface EmptyStateProps {
  icon: 'documents' | 'chat' | 'dashboard' | 'folder' | 'upload';
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

const icons = {
  documents: FileText,
  chat: MessageSquare,
  dashboard: BarChart3,
  folder: FolderOpen,
  upload: Upload,
};

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  const Icon = icons[icon];
  
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
        <Icon className="h-8 w-8 text-gray-400" />
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-500 max-w-sm mb-4">{description}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="px-4 py-2 bg-black text-white text-sm rounded-lg hover:bg-gray-800 transition-all hover:scale-105"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
