import React, { useState, useEffect } from 'react';
import VirtualizedFileList from './VirtualizedFileList';
import PreviewPane from './PreviewPane';
import SafetyLockModal from './SafetyLockModal';
import ReviewHeader from './ReviewHeader';
import QuickSelectBar from './QuickSelectBar';
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
      setLoadingProgress(50);

      const data = await getFiles();
      setFiles(data);

      setLoadingProgress(100);
      setLoading(false);

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
      <div className="loading-container">
        <h2>Loading Files...</h2>
        <p>{loadingStatus}</p>
        <div className="progress-bar-container">
          <div className="progress-bar" style={{ width: `${loadingProgress}%` }}></div>
        </div>
      </div>
    );
  }

  if (error) return <div className="error-container">{error}</div>;

  return (
    <div className="review-container">
      <ReviewHeader
        selectedCount={selectedFilePaths.size}
        onExecuteClick={handleExecuteClick}
      />

      <QuickSelectBar
        onSelectByConfidence={handleSelectByConfidence}
        onClearSelection={handleClearSelection}
      />

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
