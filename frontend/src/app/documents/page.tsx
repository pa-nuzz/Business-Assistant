'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { documents } from '@/lib/api';
import api from '@/lib/api';
import { FileText, Upload, Trash2, Search, Loader2, X, MessageSquare, Eye } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { PageSkeleton } from '@/components/loading-skeletons';

interface Document {
  id: string;
  title: string;
  file_type: string;
  status: 'pending' | 'processing' | 'ready' | 'failed';
  page_count: number;
  created_at: string;
}

interface DocumentSummary {
  title: string;
  summary: string;
  pages: number;
  type: string;
}

export default function DocumentsPage() {
  const router = useRouter();
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [docSummary, setDocSummary] = useState<DocumentSummary | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [searchResults, setSearchResults] = useState<any>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const pageSize = 20;
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Set page title
  useEffect(() => {
    document.title = 'Documents | AEIOU AI';
  }, []);

  const fetchDocuments = async () => {
    try {
      const data = await documents.list(currentPage, pageSize);
      setDocs(data.results || []);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [currentPage]);

  // Poll document status while processing
  useEffect(() => {
    const processingDocs = docs.filter(d => d.status === 'pending' || d.status === 'processing');
    if (processingDocs.length === 0) return;

    const interval = setInterval(async () => {
      const updatedDocs = await Promise.all(
        processingDocs.map(async (doc) => {
          try {
            const response = await api.get(`/documents/${doc.id}/status/`);
            return { ...doc, status: response.data.status, page_count: response.data.pages };
          } catch {
            return doc;
          }
        })
      );

      setDocs(prev => {
        const newDocs = [...prev];
        updatedDocs.forEach(updated => {
          const idx = newDocs.findIndex(d => d.id === updated.id);
          if (idx >= 0) {
            newDocs[idx] = updated;
          }
        });
        return newDocs;
      });
    }, 3000);

    return () => clearInterval(interval);
  }, [docs]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    const allowedExts = ['pdf', 'docx', 'txt'];
    const ext = file.name.split('.').pop()?.toLowerCase();

    if (!ext || !allowedExts.includes(ext)) {
      alert('Only PDF, DOCX, and TXT files are supported.');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      await documents.upload(file, (progress) => {
        setUploadProgress(progress);
      });
      await fetchDocuments();
    } catch (err: any) {
      console.error('Upload failed:', err);
      const errorMsg = err.response?.data?.error || err.message || 'Upload failed. Please try again.';
      alert(errorMsg);
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    setDeletingId(id);
    try {
      await api.delete(`/documents/${id}/delete/`);
      setDocs(prev => prev.filter(d => d.id !== id));
    } catch (err) {
      console.error('Delete failed:', err);
      alert('Failed to delete document.');
    } finally {
      setDeletingId(null);
    }
  };

  const openDocModal = async (doc: Document) => {
    setSelectedDoc(doc);
    setDocSummary(null);
    setSearchQuery('');
    setSearchResults(null);
    
    if (doc.status === 'ready') {
      try {
        const summary = await documents.getSummary(doc.id);
        setDocSummary(summary);
      } catch (err) {
        console.error('Failed to fetch summary:', err);
      }
    }
  };

  const handleSearchInDoc = async () => {
    if (!selectedDoc || !searchQuery.trim()) return;
    
    setIsSearching(true);
    try {
      const response = await api.post('/chat/', {
        message: `Search in document "${selectedDoc.title}" for: ${searchQuery}`,
      });
      setSearchResults(response.data);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setIsSearching(false);
    }
  };

  const closeModal = () => {
    setSelectedDoc(null);
    setDocSummary(null);
    setSearchQuery('');
    setSearchResults(null);
  };

  const getFileIconColor = (type: string) => {
    switch (type) {
      case 'pdf': return { bg: 'bg-red-50', color: 'text-red-600', border: 'border-red-100' };
      case 'docx': return { bg: 'bg-blue-50', color: 'text-blue-600', border: 'border-blue-100' };
      default: return { bg: 'bg-gray-50', color: 'text-gray-600', border: 'border-gray-100' };
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ready':
        return (
          <span className="text-xs px-2 py-1 rounded-full bg-green-50 text-green-600 border border-green-100">
            Ready
          </span>
        );
      case 'pending':
      case 'processing':
        return (
          <span className="text-xs px-2 py-1 rounded-full bg-amber-50 text-amber-600 border border-amber-100 flex items-center gap-1">
            <Loader2 size={12} className="animate-spin" />
            Processing
          </span>
        );
      case 'failed':
        return (
          <span className="text-xs px-2 py-1 rounded-full bg-red-50 text-red-600 border border-red-100">
            Failed
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Progress bar for upload */}
      {isUploading && (
        <div className="fixed top-0 left-0 right-0 h-[3px] bg-muted z-50">
          <motion.div 
            className="h-full bg-blue-600"
            initial={{ width: 0 }}
            animate={{ width: `${uploadProgress}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      )}

      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Upload Zone - Always visible at top */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-gray-300 hover:border-blue-400 rounded-2xl p-8 text-center cursor-pointer transition-colors bg-gray-50/50 hover:bg-blue-50/30"
          >
            <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center mx-auto mb-3">
              <Upload className="w-6 h-6 text-blue-600" />
            </div>
            <p className="text-sm font-medium text-slate-900 mb-1">Click to upload documents</p>
            <p className="text-xs text-slate-500">Drop files here or click to browse</p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={handleUpload}
            className="hidden"
          />
        </motion.div>

        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 mb-1">Documents</h1>
            <p className="text-sm text-slate-600">Upload and search your business files</p>
          </div>
        </div>

        {/* Document List */}
        {loading ? (
          <PageSkeleton type="documents" />
        ) : docs.length === 0 ? (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-16"
          >
            <h2 className="text-xl font-semibold text-slate-900 mb-2">No documents uploaded</h2>
            <p className="text-sm text-slate-600 mb-4">Upload PDF, DOCX, or TXT files and ask AEIOU questions about them</p>
            <div className="flex items-center justify-center gap-2">
              <span className="px-3 py-1 text-xs font-medium bg-red-50 text-red-600 rounded-full">PDF</span>
              <span className="text-slate-400">·</span>
              <span className="px-3 py-1 text-xs font-medium bg-blue-50 text-blue-600 rounded-full">DOCX</span>
              <span className="text-slate-400">·</span>
              <span className="px-3 py-1 text-xs font-medium bg-gray-100 text-gray-600 rounded-full">TXT</span>
            </div>
          </motion.div>
        ) : (
          <>
            <div className="space-y-3">
              {docs.map((doc, index) => {
                const iconColors = getFileIconColor(doc.file_type);
                return (
                  <motion.div
                    key={doc.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="flex items-center p-4 bg-card rounded-xl border border-border hover:border-blue-200 hover:shadow-sm transition-all duration-200"
                  >
                    {/* File Type Icon */}
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center mr-4 ${iconColors.bg} border ${iconColors.border}`}>
                      <FileText size={24} className={iconColors.color} />
                    </div>

                    {/* Document Info */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-slate-900 truncate">
                        {doc.title}
                      </p>
                      <p className="text-xs text-slate-500">
                        {new Date(doc.created_at).toLocaleDateString()}
                        {doc.page_count > 0 && ` • ${doc.page_count} pages`}
                      </p>
                    </div>

                    {/* Status */}
                    <div className="mr-4">
                      {getStatusBadge(doc.status)}
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                      {doc.status === 'ready' && (
                        <motion.button
                          onClick={() => openDocModal(doc)}
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
                        >
                          <Eye size={14} />
                          View
                        </motion.button>
                      )}
                      <motion.button
                        onClick={() => handleDelete(doc.id)}
                        disabled={deletingId === doc.id}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                        title="Delete"
                      >
                        {deletingId === doc.id ? (
                          <Loader2 size={16} className="animate-spin" />
                        ) : (
                          <Trash2 size={16} />
                        )}
                      </motion.button>
                    </div>
                  </motion.div>
                );
              })}
            </div>

            {/* Pagination */}
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
          </>
        )}
      </div>

      {/* Document Preview Modal */}
      <AnimatePresence>
        {selectedDoc && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={closeModal}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="fixed top-[10%] left-1/2 -translate-x-1/2 w-[90%] max-w-2xl max-h-[80vh] bg-card rounded-2xl border border-border shadow-2xl z-50 overflow-hidden flex flex-col"
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-muted/50">
                <div>
                  <h2 className="text-lg font-semibold text-slate-900">{selectedDoc.title}</h2>
                  <p className="text-sm text-slate-600">
                    {selectedDoc.page_count} pages • {selectedDoc.file_type.toUpperCase()}
                  </p>
                </div>
                <motion.button
                  onClick={closeModal}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  className="p-2 text-slate-400 hover:text-slate-600 hover:bg-muted rounded-lg transition-colors"
                >
                  <X size={20} />
                </motion.button>
              </div>

              {/* Modal Content */}
              <div className="flex-1 overflow-y-auto p-6">
                {selectedDoc.status !== 'ready' ? (
                  <div className="flex flex-col items-center py-10">
                    <Loader2 size={32} className="animate-spin text-slate-400" />
                    <p className="mt-4 text-slate-600">Document is still processing...</p>
                  </div>
                ) : (
                  <>
                    {/* Summary Section */}
                    {docSummary && (
                      <div className="mb-6">
                        <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
                          <FileText size={16} className="text-blue-600" />
                          Summary
                        </h3>
                        <div className="p-4 bg-muted rounded-xl text-sm text-slate-700 leading-relaxed">
                          {docSummary.summary}
                        </div>
                      </div>
                    )}

                    {/* Search Section */}
                    <div className="mb-6">
                      <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
                        <Search size={16} className="text-blue-600" />
                        Search in Document
                      </h3>
                      <div className="flex gap-2 mb-4">
                        <input
                          type="text"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && handleSearchInDoc()}
                          placeholder="Ask anything about this document..."
                          className="flex-1 px-4 py-2.5 bg-background border border-border rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-300 focus:ring-2 focus:ring-blue-100"
                        />
                        <motion.button
                          onClick={handleSearchInDoc}
                          disabled={isSearching || !searchQuery.trim()}
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl transition-colors disabled:opacity-50 shadow-sm"
                        >
                          {isSearching ? (
                            <Loader2 size={16} className="animate-spin" />
                          ) : (
                            <Search size={16} />
                          )}
                          Search
                        </motion.button>
                      </div>

                      {/* Search Results */}
                      {searchResults && (
                        <motion.div 
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          className="p-4 bg-muted rounded-xl text-sm text-slate-700 leading-relaxed"
                        >
                          {searchResults.response || searchResults.text || JSON.stringify(searchResults)}
                        </motion.div>
                      )}
                    </div>

                    {/* Quick Actions */}
                    <div>
                      <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
                        <MessageSquare size={16} className="text-blue-600" />
                        Quick Actions
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {['Summarize key points', 'What are the main findings?', 'Extract action items', 'What does this say about revenue?'].map((query) => (
                          <motion.button
                            key={query}
                            onClick={() => {
                              setSearchQuery(query);
                              setTimeout(() => handleSearchInDoc(), 100);
                            }}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            className="px-3 py-2 text-xs text-slate-600 bg-background hover:bg-muted border border-border rounded-lg transition-colors"
                          >
                            {query}
                          </motion.button>
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* Modal Footer */}
              <div className="flex justify-end gap-3 px-6 py-4 border-t border-border bg-muted/50">
                <motion.button
                  onClick={() => {
                    closeModal();
                    router.push(`/chat?query=${encodeURIComponent(`Tell me about "${selectedDoc.title}"`)}`);
                  }}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-xl transition-colors"
                >
                  <MessageSquare size={16} />
                  Chat about this
                </motion.button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
