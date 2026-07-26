import React, { useState } from 'react';
import { UserContext } from '../types';
import { apiService } from '../services/api';
import { FileText, Upload, Search, CheckCircle2, Shield } from 'lucide-react';

interface DocumentPortalProps {
  userContext: UserContext;
}

export const DocumentPortal: React.FC<DocumentPortalProps> = ({ userContext }) => {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [aclTag, setAclTag] = useState('');
  const [ingestStatus, setIngestStatus] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;

    const acl = aclTag.trim() ? [aclTag.trim()] : [];
    await apiService.ingestDocument(userContext.tenantId, title, content, acl);

    setIngestStatus(`Document "${title}" chunked & embedded into pgvector!`);
    setTitle('');
    setContent('');
    setAclTag('');
    setTimeout(() => setIngestStatus(null), 4000);
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    const res = await apiService.searchDocuments(userContext.tenantId, searchQuery);
    setSearchResults(res.citations || []);
    setIsSearching(false);
  };

  return (
    <div className="flex-1 p-6 bg-dark-bg overflow-y-auto">
      <div className="max-w-5xl mx-auto space-y-8">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <FileText className="w-6 h-6 text-cyan-400" />
            <span>ACL-Aware Document RAG Portal</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Ingest internal documents with tenant isolation & permission tags, and perform vector similarity searches.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Document Ingestion Form */}
          <div className="p-6 glass-panel rounded-2xl space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <Upload className="w-4 h-4 text-brand-500" />
              <span>Ingest New Document</span>
            </h3>

            <form onSubmit={handleIngest} className="space-y-4">
              <div>
                <label className="text-xs text-slate-300 font-medium mb-1 block">Document Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Employee Handbook 2026"
                  required
                  className="w-full bg-dark-bg border border-dark-border rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="text-xs text-slate-300 font-medium mb-1 block">ACL Permission Tag (Optional)</label>
                <input
                  type="text"
                  value={aclTag}
                  onChange={(e) => setAclTag(e.target.value)}
                  placeholder="e.g. group:execs or role:ADMIN"
                  className="w-full bg-dark-bg border border-dark-border rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="text-xs text-slate-300 font-medium mb-1 block">Content</label>
                <textarea
                  rows={5}
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Paste document text..."
                  required
                  className="w-full bg-dark-bg border border-dark-border rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 resize-none"
                />
              </div>

              <button
                type="submit"
                className="w-full py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs transition-all shadow-lg shadow-indigo-500/20"
              >
                Chunk & Embed Document
              </button>

              {ingestStatus && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>{ingestStatus}</span>
                </div>
              )}
            </form>
          </div>

          {/* Vector Search Tester */}
          <div className="p-6 glass-panel rounded-2xl space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <Search className="w-4 h-4 text-cyan-400" />
              <span>Vector Similarity Search</span>
            </h3>

            <form onSubmit={handleSearch} className="flex items-center space-x-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Query internal knowledge..."
                className="flex-1 bg-dark-bg border border-dark-border rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400"
              />
              <button
                type="submit"
                disabled={isSearching}
                className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs shrink-0"
              >
                Search
              </button>
            </form>

            <div className="space-y-3">
              <div className="text-[11px] font-semibold uppercase text-slate-400">Search Results & Citations:</div>
              {searchResults.length === 0 ? (
                <div className="text-xs text-slate-500 italic py-6 text-center">
                  No query executed or zero matching documents.
                </div>
              ) : (
                searchResults.map((res, i) => (
                  <div key={i} className="p-3 rounded-xl bg-dark-bg border border-dark-border text-xs space-y-1">
                    <div className="font-semibold text-indigo-300">{res.title}</div>
                    <div className="text-slate-400 text-[11px]">{res.snippet}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
