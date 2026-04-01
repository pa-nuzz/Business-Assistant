'use client';

import { useState, useCallback } from 'react';
import { Upload, File, X } from 'lucide-react';
import { toast } from 'sonner';

interface FileUploadZoneProps {
  onUpload: (files: File[]) => void;
  acceptedTypes?: string[];
  maxSizeMB?: number;
}

export function FileUploadZone({ 
  onUpload, 
  acceptedTypes = ['.pdf', '.docx', '.txt'],
  maxSizeMB = 10 
}: FileUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const validateFile = (file: File): boolean => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    const acceptedExts = acceptedTypes.map(t => t.replace('.', ''));
    
    if (!ext || !acceptedExts.includes(ext)) {
      toast.error(`${file.name}: Invalid file type. Accepted: ${acceptedTypes.join(', ')}`);
      return false;
    }
    
    if (file.size > maxSizeMB * 1024 * 1024) {
      toast.error(`${file.name}: File too large. Max size: ${maxSizeMB}MB`);
      return false;
    }
    
    return true;
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    const validFiles = files.filter(validateFile);
    
    if (validFiles.length > 0) {
      setSelectedFiles(prev => [...prev, ...validFiles]);
    }
  }, [onUpload, acceptedTypes, maxSizeMB]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const validFiles = files.filter(validateFile);
    
    if (validFiles.length > 0) {
      setSelectedFiles(prev => [...prev, ...validFiles]);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpload = () => {
    if (selectedFiles.length === 0) {
      toast.error('Please select files to upload');
      return;
    }
    onUpload(selectedFiles);
    setSelectedFiles([]);
  };

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-xl p-8 transition-all ${
          isDragging 
            ? 'border-black bg-gray-50 scale-[1.02]' 
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input
          type="file"
          multiple
          accept={acceptedTypes.join(',')}
          onChange={handleFileSelect}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        <div className="flex flex-col items-center gap-3 text-center">
          <div className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
            isDragging ? 'bg-black text-white' : 'bg-gray-100 text-gray-500'
          }`}>
            <Upload size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-900">
              {isDragging ? 'Drop files here' : 'Drag and drop files here'}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              or click to browse • {acceptedTypes.join(', ')} • Max {maxSizeMB}MB
            </p>
          </div>
        </div>
      </div>

      {/* Selected Files */}
      {selectedFiles.length > 0 && (
        <div className="bg-gray-50 rounded-lg p-4 space-y-2">
          <p className="text-sm font-medium text-gray-900 mb-3">
            Selected files ({selectedFiles.length})
          </p>
          {selectedFiles.map((file, index) => (
            <div 
              key={index}
              className="flex items-center justify-between bg-white p-2 rounded-md border border-gray-200"
            >
              <div className="flex items-center gap-2 min-w-0">
                <File size={16} className="text-gray-400 flex-shrink-0" />
                <span className="text-sm text-gray-700 truncate">{file.name}</span>
                <span className="text-xs text-gray-500">
                  ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </span>
              </div>
              <button
                onClick={() => removeFile(index)}
                className="p-1 hover:bg-gray-100 rounded-md transition-colors"
              >
                <X size={14} className="text-gray-400" />
              </button>
            </div>
          ))}
          <button
            onClick={handleUpload}
            className="w-full mt-3 py-2 bg-black text-white text-sm rounded-lg hover:bg-gray-800 transition-all hover:scale-[1.02]"
          >
            Upload {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''}
          </button>
        </div>
      )}
    </div>
  );
}
