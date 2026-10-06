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
      background: 'rgba(0, 0, 0, 0.6)', backdropFilter: 'blur(3px)', zIndex: 99999,
      display: 'flex', alignItems: 'center', justifyContent: 'center'
    }}>
      <div style={{
        background: '#1e293b', borderRadius: '12px', width: '420px', maxWidth: '90%',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)', 
        padding: '24px', border: '1px solid #334155',
        animation: 'fadeIn 0.2s ease-out'
      }}>
        <h3 style={{ marginTop: 0, marginBottom: '16px', color: '#f8fafc', fontSize: '18px', fontWeight: 'bold' }}>
          {dialog.title}
        </h3>
        <div style={{ color: '#cbd5e1', fontSize: '14px', lineHeight: '1.6', marginBottom: '24px', whiteSpace: 'pre-wrap', maxHeight: '60vh', overflowY: 'auto' }}>
          {dialog.message}
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          {dialog.type === 'confirm' && (
            <button 
              onClick={() => handleClose(false)}
              style={{ padding: '10px 16px', borderRadius: '6px', border: '1px solid #475569', background: '#334155', color: '#f1f5f9', cursor: 'pointer', fontWeight: '600', fontSize: '14px', transition: 'background 0.2s' }}
              onMouseOver={(e) => e.target.style.background = '#475569'}
              onMouseOut={(e) => e.target.style.background = '#334155'}
            >
              취소
            </button>
          )}
          <button 
            onClick={() => handleClose(true)}
            style={{ padding: '10px 16px', borderRadius: '6px', border: 'none', background: '#3b82f6', color: '#ffffff', cursor: 'pointer', fontWeight: '600', fontSize: '14px', minWidth: '80px', transition: 'background 0.2s' }}
            onMouseOver={(e) => e.target.style.background = '#2563eb'}
            onMouseOut={(e) => e.target.style.background = '#3b82f6'}
          >
            확인
          </button>
        </div>
      </div>
    </div>
  );
}
