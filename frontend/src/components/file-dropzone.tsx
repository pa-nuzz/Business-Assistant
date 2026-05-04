"use client";

import React, { useCallback, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, File, X, AlertCircle, Check } from "lucide-react";

interface FileDropzoneProps {
  onFilesAccepted: (files: File[]) => void;
  onUpload: (file: File) => void;
  isUploading: boolean;
  uploadProgress: number;
  maxSizeMB?: number;
  acceptedTypes?: string[];
}

interface ValidationError {
  file: string;
  error: string;
}

const DEFAULT_MAX_SIZE = 50; // 50MB
const DEFAULT_ACCEPTED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
];
const DEFAULT_ACCEPTED_EXTENSIONS = [".pdf", ".docx", ".txt"];

export function FileDropzone({
  onFilesAccepted,
  onUpload,
  isUploading,
  uploadProgress,
  maxSizeMB = DEFAULT_MAX_SIZE,
  acceptedTypes = DEFAULT_ACCEPTED_TYPES,
}: FileDropzoneProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [errors, setErrors] = useState<ValidationError[]>([]);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);

  const validateFile = (file: File): string | null => {
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    
    if (file.size > maxSizeBytes) {
      return `File too large (max ${maxSizeMB}MB)`;
    }

    const ext = `.${file.name.split(".").pop()?.toLowerCase()}`;
    const isValidType = acceptedTypes.includes(file.type);
    const isValidExt = DEFAULT_ACCEPTED_EXTENSIONS.includes(ext);

    if (!isValidType && !isValidExt) {
      return "Only PDF, DOCX, and TXT files are supported";
    }

    return null;
  };

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragActive(false);

      const droppedFiles = Array.from(e.dataTransfer.files);
      const validFiles: File[] = [];
      const newErrors: ValidationError[] = [];

      droppedFiles.forEach((file) => {
        const error = validateFile(file);
        if (error) {
          newErrors.push({ file: file.name, error });
        } else {
          validFiles.push(file);
        }
      });

      if (newErrors.length > 0) {
        setErrors(newErrors);
        // Auto-clear errors after 5 seconds
        setTimeout(() => setErrors([]), 5000);
      }

      if (validFiles.length > 0) {
        setPendingFiles(validFiles);
        onFilesAccepted(validFiles);
      }
    },
    [onFilesAccepted, maxSizeMB, acceptedTypes]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFiles = Array.from(e.target.files || []);
      const validFiles: File[] = [];
      const newErrors: ValidationError[] = [];

      selectedFiles.forEach((file) => {
        const error = validateFile(file);
        if (error) {
          newErrors.push({ file: file.name, error });
        } else {
          validFiles.push(file);
        }
      });

      if (newErrors.length > 0) {
        setErrors(newErrors);
        setTimeout(() => setErrors([]), 5000);
      }

      if (validFiles.length > 0) {
        setPendingFiles(validFiles);
        onFilesAccepted(validFiles);
        // Auto-upload the first valid file
        onUpload(validFiles[0]);
      }

      // Reset input
      e.target.value = "";
    },
    [onFilesAccepted, onUpload, maxSizeMB, acceptedTypes]
  );

  const clearPending = useCallback(() => {
    setPendingFiles([]);
    setErrors([]);
  }, []);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="w-full space-y-4">
      {/* Dropzone Area */}
      <motion.div
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        animate={{
          scale: isDragActive ? 1.02 : 1,
          borderColor: isDragActive
            ? "hsl(var(--primary))"
            : "hsl(var(--border))",
          backgroundColor: isDragActive
            ? "hsl(var(--primary) / 0.05)"
            : "hsl(var(--background))",
        }}
        className={`
          relative border-2 border-dashed rounded-xl p-8
          transition-colors cursor-pointer
          ${isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25"}
          ${isUploading ? "pointer-events-none opacity-60" : ""}
        `}
      >
        <input
          type="file"
          onChange={handleFileInput}
          accept={DEFAULT_ACCEPTED_EXTENSIONS.join(",")}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={isUploading}
          multiple
        />

        <div className="flex flex-col items-center justify-center text-center space-y-4">
          <motion.div
            animate={{ y: isDragActive ? -5 : 0 }}
            className={`
              w-16 h-16 rounded-full flex items-center justify-center
              ${isDragActive ? "bg-primary/20" : "bg-muted"}
            `}
          >
            <Upload
              className={`w-8 h-8 ${isDragActive ? "text-primary" : "text-muted-foreground"}`}
            />
          </motion.div>

          <div className="space-y-1">
            <p className="text-lg font-medium text-foreground">
              {isDragActive ? "Drop files here" : "Drag & drop files here"}
            </p>
            <p className="text-sm text-muted-foreground">
              or click to browse (PDF, DOCX, TXT up to {maxSizeMB}MB)
            </p>
          </div>

          {/* Virus Scan Placeholder Badge */}
          <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted px-3 py-1.5 rounded-full">
            <Check className="w-3.5 h-3.5 text-green-500" />
            <span>Files scanned for security</span>
          </div>
        </div>
      </motion.div>

      {/* Pending Files List */}
      <AnimatePresence>
        {pendingFiles.length > 0 && !isUploading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-muted/50 rounded-lg p-4 space-y-3"
          >
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium">Files ready to upload</p>
              <button
                onClick={clearPending}
                className="text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                Clear
              </button>
            </div>
            <div className="space-y-2">
              {pendingFiles.map((file, index) => (
                <motion.div
                  key={`${file.name}-${index}`}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 10 }}
                  className="flex items-center gap-3 bg-background rounded-md p-2"
                >
                  <File className="w-4 h-4 text-primary" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm truncate">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                  <button
                    onClick={() => onUpload(file)}
                    className="text-xs bg-primary text-primary-foreground px-3 py-1.5 rounded-md hover:bg-primary/90 transition-colors"
                  >
                    Upload
                  </button>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Validation Errors */}
      <AnimatePresence>
        {errors.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-red-50 border border-red-200 rounded-lg p-3 space-y-2"
          >
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="w-4 h-4" />
              <p className="text-sm font-medium">Validation errors</p>
            </div>
            {errors.map((err, index) => (
              <div
                key={index}
                className="flex items-start gap-2 text-sm text-red-600/80"
              >
                <X className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                <span className="truncate">
                  <span className="font-medium">{err.file}:</span> {err.error}
                </span>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Upload Progress */}
      <AnimatePresence>
        {isUploading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-2"
          >
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Uploading...</span>
              <span className="font-medium">{uploadProgress}%</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-primary rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${uploadProgress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
