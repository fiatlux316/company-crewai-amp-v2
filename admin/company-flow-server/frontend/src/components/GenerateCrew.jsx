import React, { useState } from 'react';
import { api } from '../utils/api';

export default function GenerateCrew() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleGenerate = async () => {
    if (!file) {
      alert('파일을 선택해주세요.');
      return;
    }
    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const data = await api.generateCrew(file);
      setResult(data);
    } catch (err) {
      setError(err.message || '업로드 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', color: '#f3f4f6' }}>
      <h2>Generate Crew from Excel</h2>
      <p style={{ marginBottom: '20px', color: '#9ca3af' }}>
        Crew AI Spec 문서(Excel)를 업로드하여 tasks.jsonc, agents.jsonc, process.jsonc 등의 설정을 자동 생성합니다.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', maxWidth: '500px' }}>
        <div style={{ background: '#1f2937', padding: '20px', borderRadius: '8px', border: '1px solid #374151' }}>
          <label style={{ display: 'block', marginBottom: '10px', fontWeight: 'bold' }}>
            엑셀 파일 선택 (.xlsx)
          </label>
          <input 
            type="file" 
            accept=".xlsx" 
            onChange={handleFileChange}
            style={{ width: '100%', padding: '10px', background: '#374151', color: 'white', borderRadius: '4px', border: 'none' }}
          />
        </div>

        <button 
          onClick={handleGenerate}
          disabled={loading || !file}
          style={{
            padding: '12px 20px',
            background: loading ? '#6b7280' : '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: loading || !file ? 'not-allowed' : 'pointer',
            fontWeight: 'bold',
            fontSize: '16px'
          }}
        >
          {loading ? '생성 중...' : '✨ Generate Crew'}
        </button>

        {error && (
          <div style={{ padding: '15px', background: '#ef444420', border: '1px solid #ef4444', borderRadius: '6px', color: '#fca5a5' }}>
            <strong>오류 발생:</strong> {error}
          </div>
        )}

        {result && (
          <div style={{ padding: '15px', background: '#10b98120', border: '1px solid #10b981', borderRadius: '6px', color: '#6ee7b7' }}>
            <strong>생성 성공!</strong>
            <p style={{ marginTop: '10px' }}>Crew ID: {result.crew_id}</p>
            <p>Version: {result.version}</p>
            <p style={{ marginTop: '10px', fontSize: '14px', color: '#9ca3af' }}>
              이제 'Crew Management' 탭에서 생성된 크루를 확인하고 관리할 수 있습니다.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
