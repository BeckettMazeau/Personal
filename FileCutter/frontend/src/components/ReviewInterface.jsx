import React, { useState, useEffect } from 'react';
import VirtualizedFileList from './VirtualizedFileList';
import PreviewPane from './PreviewPane';
import SafetyLockModal from './SafetyLockModal';
import { getFiles, executeCleanup } from '../api';

const ReviewInterface = () => {
  const [files, setFiles] = useState([]);
  const [selectedFileIds, setSelectedFileIds] = useState(new Set());
  const [previewFile, setPreviewFile] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      setLoading(true);
      const data = await getFiles();
      setFiles(data);
    } catch (err) {
      setError('Failed to fetch files');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleSelect = (fileId) => {
    setSelectedFileIds(prev => {
      const next = new Set(prev);
      if (next.has(fileId)) {
        next.delete(fileId);
      } else {
        next.add(fileId);
      }
      return next;
    });
  };

  const handleSelectByConfidence = (level) => {
    const ids = files.filter(f => f.confidence === level).map(f => f.id);
    setSelectedFileIds(new Set(ids));
  };

  const handleClearSelection = () => {
    setSelectedFileIds(new Set());
  };

  const handlePreview = (file) => {
    setPreviewFile(file);
  };

  const handleExecuteClick = () => {
    if (selectedFileIds.size > 0) {
      setIsModalOpen(true);
    }
  };

  const handleConfirmExecute = async () => {
    setIsModalOpen(false);
    try {
      const confirmationToken = "some-secure-token"; // This would typically come from an auth context or previous step
      await executeCleanup(Array.from(selectedFileIds), confirmationToken);
      // Refresh list or remove deleted files from state
      setFiles(files.filter(f => !selectedFileIds.has(f.id)));
      setSelectedFileIds(new Set());
      setPreviewFile(null);
      alert('Cleanup executed successfully');
    } catch (err) {
      alert('Failed to execute cleanup');
    }
  };

  if (loading) return <div style={{ padding: '2rem', textAlign: 'center' }}>Loading files...</div>;
  if (error) return <div style={{ padding: '2rem', color: 'red' }}>{error}</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <header style={{ padding: '1rem', backgroundColor: '#2d3748', color: 'white', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem' }}>FileCutter Review</h1>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <span style={{ fontSize: '0.875rem' }}>{selectedFileIds.size} files selected</span>
          <button
            onClick={handleExecuteClick}
            disabled={selectedFileIds.size === 0}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: selectedFileIds.size > 0 ? '#e53e3e' : '#fc8181',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: selectedFileIds.size > 0 ? 'pointer' : 'not-allowed',
              fontWeight: 'bold'
            }}
          >
            Execute Cleanup
          </button>
        </div>
      </header>

      <div style={{ padding: '1rem', backgroundColor: '#f7fafc', borderBottom: '1px solid #e2e8f0', display: 'flex', gap: '1rem' }}>
        <span>Quick Select:</span>
        <button onClick={() => handleSelectByConfidence(3)} style={{ padding: '0.25rem 0.5rem', cursor: 'pointer' }}>All Level 3 (Safe to Delete)</button>
        <button onClick={() => handleSelectByConfidence(2)} style={{ padding: '0.25rem 0.5rem', cursor: 'pointer' }}>All Level 2 (Review)</button>
        <button onClick={() => handleSelectByConfidence(1)} style={{ padding: '0.25rem 0.5rem', cursor: 'pointer' }}>All Level 1 (Keep)</button>
        <button onClick={handleClearSelection} style={{ padding: '0.25rem 0.5rem', cursor: 'pointer', marginLeft: 'auto' }}>Clear Selection</button>
      </div>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <div style={{ flex: 2, display: 'flex', flexDirection: 'column', borderRight: '1px solid #e2e8f0' }}>
          <VirtualizedFileList
            files={files}
            selectedFileIds={selectedFileIds}
            onToggleSelect={handleToggleSelect}
            onPreview={handlePreview}
          />
        </div>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <PreviewPane file={previewFile} />
        </div>
      </div>

      <SafetyLockModal
        isOpen={isModalOpen}
        fileCount={selectedFileIds.size}
        onConfirm={handleConfirmExecute}
        onCancel={() => setIsModalOpen(false)}
      />
    </div>
  );
};

export default ReviewInterface;
