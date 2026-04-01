'use client';

import { useState, useCallback } from 'react';
import { Upload, File, X, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
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
      {/* Drop Zone with enhanced visual feedback */}
      <motion.div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        whileHover={{ scale: isDragging ? 1.02 : 1.01 }}
        animate={{
          borderColor: isDragging ? '#3B82F6' : '#E5E7EB',
          backgroundColor: isDragging ? 'rgba(59, 130, 246, 0.05)' : 'transparent',
        }}
        transition={{ duration: 0.2 }}
        className={`relative border-2 border-dashed rounded-xl p-8 transition-all overflow-hidden ${
          isDragging 
            ? 'border-blue-500' 
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        {/* Animated background pulse when dragging */}
        <AnimatePresence>
          {isDragging && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="absolute inset-0 pointer-events-none"
            >
              {/* Pulsing rings */}
              <motion.div
                className="absolute inset-4 rounded-xl bg-blue-400/10"
                animate={{ 
                  scale: [1, 1.05, 1],
                  opacity: [0.3, 0.6, 0.3],
                }}
                transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
              />
              <motion.div
                className="absolute inset-8 rounded-lg bg-blue-400/5"
                animate={{ 
                  scale: [1, 1.1, 1],
                  opacity: [0.2, 0.4, 0.2],
                }}
                transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut', delay: 0.3 }}
              />
            </motion.div>
          )}
        </AnimatePresence>

        <input
          type="file"
          multiple
          accept={acceptedTypes.join(',')}
          onChange={handleFileSelect}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
        />
        
        <div className="flex flex-col items-center gap-3 text-center relative z-0">
          <motion.div 
            className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-300 ${
              isDragging 
                ? 'bg-gradient-to-br from-blue-500 to-cyan-400 shadow-lg shadow-blue-500/30' 
                : 'bg-gray-100 text-gray-500'
            }`}
            animate={{
              scale: isDragging ? [1, 1.1, 1] : 1,
            }}
            transition={{
              duration: 0.6,
              repeat: isDragging ? Infinity : 0,
              ease: 'easeInOut',
            }}
          >
            {isDragging ? (
              <Sparkles className="w-6 h-6 text-white" />
            ) : (
              <Upload className="w-6 h-6 text-gray-500" />
            )}
          </motion.div>
          
          <div>
            <motion.p 
              className="text-sm font-medium text-gray-900"
              animate={{ y: isDragging ? -2 : 0 }}
            >
              {isDragging ? 'Drop files here' : 'Drag and drop files here'}
            </motion.p>
            <p className="text-xs text-gray-500 mt-1">
              or click to browse • {acceptedTypes.join(', ')} • Max {maxSizeMB}MB
            </p>
          </div>
        </div>
      </motion.div>

      {/* Selected Files */}
      <AnimatePresence>
        {selectedFiles.length > 0 && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-gray-50 rounded-xl p-4 space-y-2"
          >
            <p className="text-sm font-medium text-gray-900 mb-3">
              Selected files ({selectedFiles.length})
            </p>
            {selectedFiles.map((file, index) => (
              <motion.div 
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                transition={{ delay: index * 0.05 }}
                className="flex items-center justify-between bg-white p-3 rounded-xl border border-gray-200 shadow-sm"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
                    <File size={16} className="text-blue-500" />
                  </div>
                  <div className="min-w-0">
                    <span className="text-sm text-gray-700 font-medium truncate block">{file.name}</span>
                    <span className="text-xs text-gray-500">
                      ({(file.size / 1024 / 1024).toFixed(2)} MB)
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X size={14} className="text-gray-400" />
                </button>
              </motion.div>
            ))}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleUpload}
              className="w-full mt-3 py-2.5 bg-gradient-to-r from-blue-500 to-cyan-500 text-white text-sm font-medium rounded-xl hover:shadow-lg hover:shadow-blue-500/25 transition-all"
            >
              Upload {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''}
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
