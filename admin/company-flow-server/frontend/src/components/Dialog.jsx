import React, { useState, useEffect } from 'react';

export function showAlert(message, title = "알림") {
  return new Promise(resolve => {
    window.dispatchEvent(new CustomEvent('app-dialog', {
      detail: { type: 'alert', message, title, resolve }
    }));
  });
}

export function showConfirm(message, title = "확인") {
  return new Promise(resolve => {
    window.dispatchEvent(new CustomEvent('app-dialog', {
      detail: { type: 'confirm', message, title, resolve }
    }));
  });
}

export default function DialogContainer() {
  const [dialog, setDialog] = useState(null);

  useEffect(() => {
    const handleEvent = (e) => setDialog(e.detail);
    window.addEventListener('app-dialog', handleEvent);
    return () => window.removeEventListener('app-dialog', handleEvent);
  }, []);

  if (!dialog) return null;

  const handleClose = (result) => {
    if (dialog.resolve) dialog.resolve(result);
    setDialog(null);
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
      background: 'rgba(15, 23, 42, 0.4)', backdropFilter: 'blur(2px)', zIndex: 99999,
      display: 'flex', alignItems: 'center', justifyContent: 'center'
    }}>
      <div style={{
        background: '#ffffff', borderRadius: '12px', width: '420px', maxWidth: '90%',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)', 
        padding: '24px', border: '1px solid #e2e8f0',
        animation: 'fadeIn 0.2s ease-out'
      }}>
        <h3 style={{ marginTop: 0, marginBottom: '16px', color: '#0f172a', fontSize: '18px', fontWeight: 'bold' }}>
          {dialog.title}
        </h3>
        <div style={{ color: '#475569', fontSize: '14px', lineHeight: '1.6', marginBottom: '24px', whiteSpace: 'pre-wrap', maxHeight: '60vh', overflowY: 'auto' }}>
          {dialog.message}
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          {dialog.type === 'confirm' && (
            <button 
              onClick={() => handleClose(false)}
              style={{ padding: '10px 16px', borderRadius: '6px', border: '1px solid #cbd5e1', background: '#f8fafc', color: '#475569', cursor: 'pointer', fontWeight: '600', fontSize: '14px' }}
            >
              취소
            </button>
          )}
          <button 
            onClick={() => handleClose(true)}
            style={{ padding: '10px 16px', borderRadius: '6px', border: 'none', background: '#3b82f6', color: '#ffffff', cursor: 'pointer', fontWeight: '600', fontSize: '14px', minWidth: '80px' }}
          >
            확인
          </button>
        </div>
      </div>
    </div>
  );
}
