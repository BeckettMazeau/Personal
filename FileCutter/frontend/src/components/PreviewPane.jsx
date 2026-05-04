import React from 'react';

const PreviewPane = ({ file }) => {
  if (!file) {
    return (
      <div className="preview-pane empty">
        <p>Select a file to preview</p>
      </div>
    );
  }

  const { filename, url, type } = file;

  const renderPreview = () => {
    if (!type) return <p>Unknown file type</p>;

    if (type.startsWith('image/')) {
      return <img src={url} alt={filename} style={{ maxWidth: '100%', maxHeight: '100%' }} />;
    }

    if (type === 'application/pdf') {
      return <iframe src={url} title={filename} style={{ width: '100%', height: '100%', border: 'none' }} />;
    }

    return (
      <div className="unsupported-preview">
        <p>Preview not supported for this file type.</p>
        <p>Filename: {filename}</p>
      </div>
    );
  };

  return (
    <div className="preview-pane" style={{ flex: 1, padding: '1rem', borderLeft: '1px solid #ccc', display: 'flex', flexDirection: 'column' }}>
      <h3>Preview</h3>
      <div className="preview-content" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f9f9f9', overflow: 'hidden' }}>
        {renderPreview()}
      </div>
    </div>
  );
};

export default PreviewPane;
