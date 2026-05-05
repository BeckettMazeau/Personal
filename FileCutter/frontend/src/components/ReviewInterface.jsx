import React, { useState, useEffect } from 'react';
import VirtualizedFileList from './VirtualizedFileList';
import PreviewPane from './PreviewPane';
import SafetyLockModal from './SafetyLockModal';
import { getFiles, executeCleanup } from '../api';
import './ReviewInterface.css';

const ReviewInterface = () => {
  const [files, setFiles] = useState([]);
  const [selectedFilePaths, setSelectedFilePaths] = useState(new Set());
  const [previewFile, setPreviewFile] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingStatus, setLoadingStatus] = useState('Scanning directory...');
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchFiles();
  }, []);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (isModalOpen || loading) return;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setActiveIndex(prev => {
          const next = Math.min(prev + 1, files.length - 1);
          if (next >= 0 && next < files.length) {
            setPreviewFile(files[next]);
          }
          return next;
        });
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setActiveIndex(prev => {
          const next = Math.max(prev - 1, 0);
          if (next >= 0 && next < files.length) {
            setPreviewFile(files[next]);
          }
          return next;
        });
      } else if (e.key === ' ') {
        e.preventDefault();
        if (activeIndex >= 0 && activeIndex < files.length) {
          handleToggleSelect(files[activeIndex].path);
        }
      } else if (e.key === 'Escape') {
        e.preventDefault();
        setPreviewFile(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [files, activeIndex, isModalOpen, loading]);



  const fetchFiles = async () => {
    try {
      setLoading(true);
      setLoadingStatus('Scanning directory...');
      setLoadingProgress(20);

      // Simulate scanning
      await new Promise(r => setTimeout(r, 600));

      setLoadingStatus('Performing shallow AI assessment...');
      setLoadingProgress(50);

      // Simulate shallow
      await new Promise(r => setTimeout(r, 800));

      setLoadingStatus('Running deep AI assessment...');
      setLoadingProgress(80);

      // Real fetch
      const data = await getFiles();
      setFiles(data);

      setLoadingProgress(100);
      setTimeout(() => setLoading(false), 300);

    } catch (err) {
      setError('Failed to fetch files');
      setLoading(false);
    }
  };

  const handleToggleSelect = (filePath) => {
    setSelectedFilePaths(prev => {
      const next = new Set(prev);
      if (next.has(filePath)) {
        next.delete(filePath);
      } else {
        next.add(filePath);
      }
      return next;
    });
  };

  const handleSelectByConfidence = (level) => {
    const ids = files.filter(f => f.confidence_score === level).map(f => f.path);
    setSelectedFilePaths(new Set(ids));
  };

  const handleClearSelection = () => {
    setSelectedFilePaths(new Set());
  };

  const handlePreview = (file) => {
    setPreviewFile(file);
    const index = files.findIndex(f => f.path === file.path);
    setActiveIndex(index);
  };

  const handleExecuteClick = () => {
    if (selectedFilePaths.size > 0) {
      setIsModalOpen(true);
    }
  };

  const handleConfirmExecute = async () => {
    setIsModalOpen(false);
    try {
      const confirmationToken = "some-secure-token"; // This would typically come from an auth context or previous step
      await executeCleanup(Array.from(selectedFilePaths), confirmationToken);
      // Refresh list or remove deleted files from state
      setFiles(files.filter(f => !selectedFilePaths.has(f.path)));
      setSelectedFilePaths(new Set());
      setPreviewFile(null);
      alert('Cleanup executed successfully');
    } catch (err) {
      alert('Failed to execute cleanup');
    }
  };


  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        <h2>Loading Files...</h2>
        <p>{loadingStatus}</p>
        <div style={{ width: '300px', height: '10px', backgroundColor: '#e2e8f0', borderRadius: '5px', marginTop: '1rem', overflow: 'hidden' }}>
          <div style={{ width: `${loadingProgress}%`, height: '100%', backgroundColor: '#4299e1', transition: 'width 0.3s ease' }}></div>
        </div>
      </div>
    );
  }

  if (error) return <div style={{ padding: '2rem', color: 'red' }}>{error}</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <header style={{ padding: '1rem', backgroundColor: '#2d3748', color: 'white', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem' }}>FileCutter Review</h1>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <span style={{ fontSize: '0.875rem' }}>{selectedFilePaths.size} files selected</span>
          <button
            onClick={handleExecuteClick}
            disabled={selectedFilePaths.size === 0}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: selectedFilePaths.size > 0 ? '#e53e3e' : '#fc8181',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: selectedFilePaths.size > 0 ? 'pointer' : 'not-allowed',
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

      <div className="main-container">
        <div className="list-container">
          <VirtualizedFileList
            files={files}
            selectedFilePaths={selectedFilePaths}
            onToggleSelect={handleToggleSelect}
            onPreview={handlePreview}
            activeIndex={activeIndex}
          />
        </div>
        <div className="preview-container">
          <PreviewPane file={previewFile} />
        </div>
      </div>

      <SafetyLockModal
        isOpen={isModalOpen}
        fileCount={selectedFilePaths.size}
        onConfirm={handleConfirmExecute}
        onCancel={() => setIsModalOpen(false)}
      />
    </div>
  );
};

export default ReviewInterface;
