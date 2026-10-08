import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';

export default function RAGChatbot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    let uuid = localStorage.getItem('chat_uuid');
    if (!uuid) {
      uuid = uuidv4();
      localStorage.setItem('chat_uuid', uuid);
    }
    setSessionId(uuid);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    const botMessage = { role: 'assistant', content: '' };
    setMessages(prev => [...prev, botMessage]);

    try {
      const response = await fetch('/api/v1/chat_stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [userMessage],
          uuid: sessionId
        })
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        setMessages(prev => {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1].content += chunk;
          return newMessages;
        });
      }
    } catch (error) {
      console.error('Error fetching chat:', error);
      setMessages(prev => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1].content = "오류가 발생했습니다. 다시 시도해 주세요.";
        return newMessages;
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="panel" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 80px)' }}>
      <div className="panel-header" style={{ flexShrink: 0, paddingBottom: '1rem', borderBottom: '1px solid #374151' }}>
        <h2>AI 상담 서비스</h2>
        <p style={{ color: '#9ca3af', fontSize: '0.9rem' }}>나만의 쇼핑 에이전트 AI 챗봇입니다.<br/>주문/배송/상품/포인트/프로모션/편의시설 및 매장내 서비스 관련 전반적인 것에 대해서 무엇이든 물어보세요!</p>
      </div>
      
      <div className="chat-messages" style={{ flexGrow: 1, overflowY: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{
            alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
            backgroundColor: msg.role === 'user' ? '#2563eb' : '#374151',
            color: 'white',
            padding: '0.75rem 1rem',
            borderRadius: '0.5rem',
            maxWidth: '80%',
            whiteSpace: 'pre-wrap'
          }}>
            {msg.content}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} style={{ flexShrink: 0, padding: '1rem', display: 'flex', gap: '0.5rem', borderTop: '1px solid #374151' }}>
        <input 
          type="text" 
          value={input} 
          onChange={(e) => setInput(e.target.value)} 
          placeholder="안녕하세요. 무엇을 도와드릴까요?" 
          disabled={isLoading}
          style={{ flexGrow: 1, padding: '0.5rem 1rem', borderRadius: '0.25rem', border: '1px solid #4b5563', backgroundColor: '#1f2937', color: 'white' }}
        />
        <button type="submit" disabled={isLoading} className="btn primary">
          전송
        </button>
      </form>
    </div>
  );
}
