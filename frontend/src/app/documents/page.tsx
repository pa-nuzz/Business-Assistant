'use client';

import { useState, useEffect, useRef } from 'react';
import { documents } from '@/lib/api';
import api from '@/lib/api';
import { FileText, Upload, FileX, Trash2, Search, Loader2 } from 'lucide-react';

interface Document {
  id: string;
  title: string;
  file_type: string;
  status: 'pending' | 'processing' | 'ready' | 'failed';
  page_count: number;
  created_at: string;
}

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = async () => {
    try {
      const data = await documents.list();
      setDocs(data);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

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

  const getFileIconColor = (type: string) => {
    switch (type) {
      case 'pdf': return { bg: 'rgba(239, 68, 68, 0.1)', color: '#EF4444' };
      case 'docx': return { bg: 'var(--accent-blue-subtle)', color: 'var(--accent-blue)' };
      default: return { bg: 'var(--surface-2)', color: 'var(--ink-2)' };
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ready':
        return (
          <span style={{
            fontSize: '12px',
            padding: '2px 8px',
            backgroundColor: 'rgba(22, 163, 74, 0.1)',
            color: '#16A34A',
            borderRadius: '4px',
          }}>
            Ready
          </span>
        );
      case 'pending':
      case 'processing':
        return (
          <span style={{
            fontSize: '12px',
            padding: '2px 8px',
            backgroundColor: 'rgba(217, 119, 6, 0.1)',
            color: 'var(--accent-amber)',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}>
            <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} />
            Processing
          </span>
        );
      case 'failed':
        return (
          <span style={{
            fontSize: '12px',
            padding: '2px 8px',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            color: '#EF4444',
            borderRadius: '4px',
          }}>
            Failed
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div style={{ maxWidth: '840px', margin: '0 auto', padding: '32px 24px' }}>
      {/* Progress bar for upload */}
      {isUploading && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          height: '3px',
          backgroundColor: 'var(--surface-2)',
          zIndex: 100,
        }}>
          <div style={{
            height: '100%',
            width: `${uploadProgress}%`,
            backgroundColor: 'var(--accent-blue)',
            transition: 'width 0.3s ease',
          }} />
        </div>
      )}

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '32px' }}>
        <div>
          <h1 style={{
            fontSize: '24px',
            fontWeight: 500,
            color: 'var(--ink-0)',
            letterSpacing: 'var(--tracking-tight)',
            margin: '0 0 8px',
          }}>
            Documents
          </h1>
          <p style={{ fontSize: '14px', color: 'var(--ink-2)', margin: 0 }}>
            Upload and search your business files
          </p>
        </div>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            fontSize: '14px',
            color: 'var(--accent-blue)',
            backgroundColor: 'var(--surface-2)',
            border: '1px solid var(--surface-border-strong)',
            borderRadius: 'var(--r-md)',
            cursor: isUploading ? 'not-allowed' : 'pointer',
            transition: 'background-color 120ms ease',
          }}
          onMouseEnter={(e) => {
            if (!isUploading) {
              e.currentTarget.style.backgroundColor = 'var(--surface-1)';
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--surface-2)';
          }}
        >
          <Upload size={16} />
          {isUploading ? 'Uploading...' : 'Upload file'}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={handleUpload}
          style={{ display: 'none' }}
        />
      </div>

      {/* Document List */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '80px 0' }}>
          <Loader2 size={32} style={{ color: 'var(--ink-3)', animation: 'spin 1s linear infinite' }} />
        </div>
      ) : docs.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '80px 0' }}>
          <FileX size={48} style={{ color: 'var(--ink-3)', marginBottom: '16px' }} />
          <p style={{ fontSize: '16px', color: 'var(--ink-1)', margin: '0 0 8px' }}>
            No documents yet
          </p>
          <p style={{ fontSize: '13px', color: 'var(--ink-3)', margin: 0 }}>
            Upload a PDF, DOCX, or TXT to get started
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {docs.map((doc) => {
            const iconColors = getFileIconColor(doc.file_type);
            return (
              <div
                key={doc.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '16px',
                  backgroundColor: 'var(--surface-0)',
                  border: '1px solid var(--surface-border)',
                  borderRadius: 'var(--r-lg)',
                }}
              >
                {/* File Type Icon */}
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '8px',
                  backgroundColor: iconColors.bg,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginRight: '16px',
                }}>
                  <FileText size={20} style={{ color: iconColors.color }} />
                </div>

                {/* Document Info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{
                    fontSize: '14px',
                    fontWeight: 500,
                    color: 'var(--ink-0)',
                    margin: '0 0 4px',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}>
                    {doc.title}
                  </p>
                  <p style={{
                    fontSize: '12px',
                    color: 'var(--ink-3)',
                    margin: 0,
                  }}>
                    {new Date(doc.created_at).toLocaleDateString()}
                    {doc.page_count > 0 && ` • ${doc.page_count} pages`}
                  </p>
                </div>

                {/* Status */}
                <div style={{ marginRight: '16px' }}>
                  {getStatusBadge(doc.status)}
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', gap: '8px' }}>
                  {doc.status === 'ready' && (
                    <a
                      href={`/chat?query=Search in document "${doc.title}"`}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '13px',
                        color: 'var(--accent-blue)',
                        textDecoration: 'none',
                        padding: '6px 12px',
                        borderRadius: '6px',
                        transition: 'background-color 120ms ease',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = 'var(--surface-1)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'transparent';
                      }}
                    >
                      Search
                      <Search size={14} />
                    </a>
                  )}
                  <button
                    onClick={() => handleDelete(doc.id)}
                    disabled={deletingId === doc.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: '32px',
                      height: '32px',
                      background: 'none',
                      border: 'none',
                      cursor: deletingId === doc.id ? 'not-allowed' : 'pointer',
                      color: 'var(--ink-3)',
                      borderRadius: '6px',
                      transition: 'background-color 120ms ease, color 120ms ease',
                    }}
                    onMouseEnter={(e) => {
                      if (deletingId !== doc.id) {
                        e.currentTarget.style.backgroundColor = 'var(--surface-1)';
                        e.currentTarget.style.color = '#EF4444';
                      }
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                      e.currentTarget.style.color = 'var(--ink-3)';
                    }}
                    title="Delete"
                  >
                    {deletingId === doc.id ? (
                      <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
                    ) : (
                      <Trash2 size={16} />
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <style jsx>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
