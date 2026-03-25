import React, { useState, useEffect, useRef } from 'react';

const WS_URL = 'ws://localhost:8000';

/**
 * WebSocket Live Feed Panel — shows real-time messages from tourists.
 * Uses the admin broadcast WebSocket to display city-wide activity.
 */
export default function LiveFeed({ token }) {
  const [messages, setMessages] = useState([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    if (!token) return;

    const connect = () => {
      try {
        const ws = new WebSocket(`${WS_URL}/ws/admin?token=${token}`);
        wsRef.current = ws;

        ws.onopen = () => setConnected(true);
        ws.onclose = () => {
          setConnected(false);
          setTimeout(connect, 3000); // reconnect
        };
        ws.onerror = () => ws.close();

        ws.onmessage = (e) => {
          const msg = JSON.parse(e.data);
          setMessages(prev => [
            { ...msg, id: Date.now(), receivedAt: new Date().toLocaleTimeString() },
            ...prev.slice(0, 49), // keep last 50
          ]);
        };
      } catch (err) {
        setTimeout(connect, 3000);
      }
    };

    connect();
    return () => wsRef.current?.close();
  }, [token]);

  const typeColors = {
    danger_score: '#534AB7',
    zone_alert:   '#E24B4A',
    sos_confirmed:'#A32D2D',
    buddy_alert:  '#185FA5',
    city_alert:   '#BA7517',
    connected:    '#639922',
  };

  const typeIcons = {
    danger_score:  '📊',
    zone_alert:    '⚠️',
    sos_confirmed: '🚨',
    buddy_alert:   '👥',
    city_alert:    '📢',
    connected:     '✅',
  };

  return (
    <div style={{
      background: 'white', borderRadius: 16, padding: 20,
      border: '1px solid #eee', height: 400, display: 'flex', flexDirection: 'column',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between',
        alignItems: 'center', marginBottom: 14 }}>
        <span style={{ fontWeight: 600, fontSize: 15 }}>Live Event Feed</span>
        <span style={{
          fontSize: 12, padding: '3px 10px', borderRadius: 20,
          background: connected ? '#EAF3DE' : '#FCF3EB',
          color: connected ? '#27500A' : '#633806',
        }}>
          {connected ? '● Connected' : '○ Reconnecting…'}
        </span>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 6 }}>
        {messages.length === 0 ? (
          <div style={{ color: '#aaa', fontSize: 13, textAlign: 'center', marginTop: 60 }}>
            Waiting for events…<br />
            <span style={{ fontSize: 11 }}>Tourist WebSocket pings appear here in real time</span>
          </div>
        ) : messages.map(m => (
          <div key={m.id} style={{
            display: 'flex', alignItems: 'flex-start', gap: 8,
            padding: '8px 10px', borderRadius: 8,
            background: `${typeColors[m.type] || '#888'}18`,
            borderLeft: `3px solid ${typeColors[m.type] || '#888'}`,
          }}>
            <span style={{ fontSize: 14 }}>{typeIcons[m.type] || '📌'}</span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 11, color: '#888', marginBottom: 1 }}>
                {m.type?.replace('_', ' ').toUpperCase()} · {m.receivedAt}
              </div>
              <div style={{ fontSize: 12, color: '#333', wordBreak: 'break-word' }}>
                {m.message || m.recommendation ||
                 (m.danger_score != null ? `Score: ${m.danger_score} (${m.zone_type})` : JSON.stringify(m))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
