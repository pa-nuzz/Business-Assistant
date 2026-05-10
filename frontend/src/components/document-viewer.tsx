"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  X, FileText, ChevronLeft, ChevronRight, Search, 
  Highlighter, Quote, ZoomIn, ZoomOut, Download,
  AlertCircle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import api from "@/lib/api";

interface DocumentViewerProps {
  documentId: string;
  documentName: string;
  documentUrl: string;
  onClose: () => void;
  citedPages?: number[];
  highlightedText?: string;
}

interface DocumentChunk {
  id: string;
  page_number: number;
  text_content: string;
  chunk_index: number;
}

export function DocumentViewer({
  documentId,
  documentName,
  documentUrl,
  onClose,
  citedPages = [],
  highlightedText = "",
}: DocumentViewerProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [zoom, setZoom] = useState(100);
  const [showSidebar, setShowSidebar] = useState(true);
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [filteredChunks, setFilteredChunks] = useState<DocumentChunk[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeCitation, setActiveCitation] = useState<string | null>(null);

  useEffect(() => {
    async function fetchChunks() {
      try {
        setLoading(true);
        const response = await api.get(`/documents/${documentId}/chunks/`);
        setChunks(response.data.chunks || []);
        setFilteredChunks(response.data.chunks || []);
        setTotalPages(response.data.total_pages || 1);
      } catch (err) {
        setError("Failed to load document text");
      } finally {
        setLoading(false);
      }
    }
    fetchChunks();
  }, [documentId]);

  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredChunks(chunks);
      return;
    }
    const filtered = chunks.filter(chunk =>
      chunk.text_content.toLowerCase().includes(searchQuery.toLowerCase())
    );
    setFilteredChunks(filtered);
  }, [searchQuery, chunks]);

  const navigateToPage = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  };

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 25, 200));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 25, 50));

  const handleCitationClick = (chunk: DocumentChunk) => {
    setCurrentPage(chunk.page_number);
    setActiveCitation(chunk.id);
    setTimeout(() => setActiveCitation(null), 3000);
  };

  const chunksByPage = filteredChunks.reduce((acc, chunk) => {
    if (!acc[chunk.page_number]) acc[chunk.page_number] = [];
    acc[chunk.page_number].push(chunk);
    return acc;
  }, {} as Record<number, DocumentChunk[]>);

  const isCitedPage = (page: number) => citedPages.includes(page);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-background/95 backdrop-blur-sm"
    >
      {/* Header */}
      <div className="h-14 border-b flex items-center justify-between px-4 bg-background">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-muted-foreground" />
            <span className="font-medium truncate max-w-md">{documentName}</span>
          </div>
          {citedPages.length > 0 && (
            <div className="flex items-center gap-1 text-xs text-primary bg-primary/10 px-2 py-1 rounded">
              <Highlighter className="h-3 w-3" />
              <span>{citedPages.length} cited pages</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 border rounded-lg p-1">
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleZoomOut}>
              <ZoomOut className="h-4 w-4" />
            </Button>
            <span className="text-sm w-12 text-center">{zoom}%</span>
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleZoomIn}>
              <ZoomIn className="h-4 w-4" />
            </Button>
          </div>

          <a 
            href={documentUrl} 
            download 
            target="_blank" 
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center h-9 w-9 rounded-md hover:bg-accent"
          >
            <Download className="h-4 w-4" />
          </a>

          <Button 
            variant="ghost" 
            onClick={() => setShowSidebar(!showSidebar)}
            className="gap-2"
          >
            <Quote className="h-4 w-4" />
            {showSidebar ? "Hide" : "Show"} Text
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex h-[calc(100vh-56px)]">
        <div className={`flex-1 flex flex-col transition-all duration-300 ${showSidebar ? 'mr-80' : ''}`}>
          {/* Page Navigation */}
          <div className="h-12 border-b flex items-center justify-center gap-4">
            <Button 
              variant="ghost" 
              size="icon" 
              disabled={currentPage <= 1}
              onClick={() => navigateToPage(currentPage - 1)}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            
            <div className="flex items-center gap-2">
              <Input
                type="number"
                min={1}
                max={totalPages}
                value={currentPage}
                onChange={(e) => navigateToPage(parseInt(e.target.value) || 1)}
                className="w-16 text-center"
              />
              <span className="text-sm text-muted-foreground">of {totalPages}</span>
            </div>

            <Button 
              variant="ghost" 
              size="icon" 
              disabled={currentPage >= totalPages}
              onClick={() => navigateToPage(currentPage + 1)}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>

            {citedPages.length > 0 && (
              <div className="flex items-center gap-1 ml-4">
                <span className="text-xs text-muted-foreground">Cited:</span>
                {citedPages.map(page => (
                  <Button
                    key={page}
                    variant={currentPage === page ? "default" : "ghost"}
                    size="sm"
                    className="h-6 w-8 text-xs"
                    onClick={() => navigateToPage(page)}
                  >
                    {page}
                  </Button>
                ))}
              </div>
            )}
          </div>

          {/* PDF iframe */}
          <div className="flex-1 overflow-auto bg-muted p-4">
            <motion.div
              animate={{ scale: zoom / 100 }}
              className="origin-top mx-auto shadow-lg"
              style={{ maxWidth: "fit-content" }}
            >
              <iframe
                src={`${documentUrl}#page=${currentPage}`}
                className="w-[800px] h-[1100px] bg-white"
                title={documentName}
              />
            </motion.div>
          </div>
        </div>

        {/* Text Extraction Sidebar */}
        <AnimatePresence>
          {showSidebar && (
            <motion.div
              initial={{ x: 320, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 320, opacity: 0 }}
              className="w-80 border-l bg-background flex flex-col absolute right-0 top-14 bottom-0"
            >
              <div className="p-4 border-b">
                <h3 className="font-medium flex items-center gap-2 mb-3">
                  <Quote className="h-4 w-4" />
                  Extracted Text
                </h3>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search in document..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {loading ? (
                  <div className="space-y-3">
                    {[...Array(3)].map((_, i) => (
                      <div key={i} className="h-20 bg-muted rounded animate-pulse" />
                    ))}
                  </div>
                ) : error ? (
                  <div className="flex items-center gap-2 text-destructive">
                    <AlertCircle className="h-4 w-4" />
                    <span className="text-sm">{error}</span>
                  </div>
                ) : filteredChunks.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    {searchQuery ? "No matches found" : "No text extracted yet"}
                  </p>
                ) : (
                  Object.entries(chunksByPage).map(([pageNum, pageChunks]) => (
                    <div key={pageNum} className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          className={`text-xs h-6 ${
                            isCitedPage(Number(pageNum)) 
                              ? 'bg-primary/10 text-primary hover:bg-primary/20' 
                              : ''
                          }`}
                          onClick={() => navigateToPage(Number(pageNum))}
                        >
                          Page {pageNum}
                          {isCitedPage(Number(pageNum)) && (
                            <Highlighter className="h-3 w-3 ml-1" />
                          )}
                        </Button>
                      </div>
                      <div className="space-y-1.5">
                        {pageChunks.map((chunk) => (
                          <motion.div
                            key={chunk.id}
                            onClick={() => handleCitationClick(chunk)}
                            className={`
                              p-3 rounded-md text-sm cursor-pointer transition-colors
                              ${activeCitation === chunk.id 
                                ? 'bg-primary/20 border border-primary/30' 
                                : 'bg-muted/50 hover:bg-muted border border-transparent'
                              }
                            `}
                            animate={activeCitation === chunk.id ? { scale: [1, 1.02, 1] } : {}}
                          >
                            <p className="line-clamp-4 text-muted-foreground">
                              {chunk.text_content}
                            </p>
                          </motion.div>
                        ))}
                      </div>
                    </div>
                  ))
                )}
              </div>

              <div className="p-4 border-t text-xs text-muted-foreground">
                <div className="flex justify-between">
                  <span>{chunks.length} chunks extracted</span>
                  <span>{totalPages} pages</span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
