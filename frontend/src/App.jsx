import React, { useState, useEffect } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from 'recharts';

const API_BASE = 'http://localhost:8000/api';

// ── Mock data (replace with real API calls) ──────────────────────────────────
const mockRiskTrend = [
  { time: '00:00', score: 22 }, { time: '03:00', score: 45 },
  { time: '06:00', score: 18 }, { time: '09:00', score: 31 },
  { time: '12:00', score: 28 }, { time: '15:00', score: 35 },
  { time: '18:00', score: 52 }, { time: '21:00', score: 74 },
  { time: '23:00', score: 68 },
];

const mockIncidentTypes = [
  { name: 'Theft',      value: 38, color: '#F09595' },
  { name: 'Medical',    value: 22, color: '#E24B4A' },
  { name: 'Accident',   value: 25, color: '#FAC775' },
  { name: 'Harassment', value: 10, color: '#B5D4F4' },
  { name: 'Lost',       value: 5,  color: '#97C459' },
];

const mockIncidents = [
  { id: 'INC-001', type: 'THEFT',   zone: 'Dharavi Area',  status: 'open',     time: '23:14' },
  { id: 'INC-002', type: 'MEDICAL', zone: 'Kurla Station', status: 'resolved', time: '22:41' },
  { id: 'INC-003', type: 'LOST',    zone: 'Marine Drive',  status: 'open',     time: '21:58' },
];

// ── Components ────────────────────────────────────────────────────────────────
function StatCard({ label, value, sub, color }) {
  return (
    <div style={{
      background: 'white', borderRadius: 16, padding: '20px 24px',
      border: '1px solid #eee', flex: 1, minWidth: 160,
    }}>
      <div style={{ fontSize: 13, color: '#888', marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: 32, fontWeight: 600, color }}>{value}</div>
      {sub && <div style={{ fontSize: 12, color: '#aaa', marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

function BadgeStatus({ status }) {
  const colors = {
    open:     { bg: '#FCEBEB', text: '#A32D2D' },
    resolved: { bg: '#EAF3DE', text: '#3B6D11' },
  };
  const c = colors[status] || colors.open;
  return (
    <span style={{ background: c.bg, color: c.text, padding: '2px 10px',
      borderRadius: 20, fontSize: 12, fontWeight: 500 }}>
      {status}
    </span>
  );
}

function BadgeType({ type }) {
  const colors = {
    THEFT:      '#F09595', MEDICAL: '#E24B4A',
    ACCIDENT:   '#FAC775', HARASSMENT: '#B5D4F4', LOST: '#97C459',
  };
  return (
    <span style={{ background: colors[type] || '#eee', color: '#333',
      padding: '2px 10px', borderRadius: 20, fontSize: 12, fontWeight: 500 }}>
      {type}
    </span>
  );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────
export default function App() {
  const [activeIncidents, setActiveIncidents] = useState(mockIncidents);
  const [liveScore, setLiveScore] = useState(42);

  // Simulate live score updates
  useEffect(() => {
    const interval = setInterval(() => {
      setLiveScore(prev => Math.max(10, Math.min(95, prev + (Math.random() - 0.5) * 8)));
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const scoreColor = liveScore < 40 ? '#639922' : liveScore < 70 ? '#BA7517' : '#E24B4A';

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', background: '#f5f4f0', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ background: '#534AB7', padding: '14px 28px', display: 'flex',
        alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ color: 'white', fontWeight: 700, fontSize: 20 }}>
          🛡️ SafeTrail — Admin Dashboard
        </div>
        <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: 13 }}>
          Mumbai · Live · {new Date().toLocaleTimeString()}
        </div>
      </div>

      <div style={{ padding: 28 }}>
        {/* Stats Row */}
        <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
          <StatCard label="City Danger Score" value={liveScore.toFixed(0)}
            sub={liveScore < 40 ? '● Safe' : liveScore < 70 ? '● Caution' : '● High Risk'}
            color={scoreColor} />
          <StatCard label="Active Tourists" value="1,284" sub="with SafeTrail app" color="#534AB7" />
          <StatCard label="Open Incidents" value="3" sub="2 theft · 1 medical" color="#E24B4A" />
          <StatCard label="DID Registrations" value="986" sub="verified on Polygon" color="#1D9E75" />
          <StatCard label="Avg Response" value="4.2s" sub="SOS to authority notify" color="#BA7517" />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 20, marginBottom: 24 }}>
          {/* Risk Trend Chart */}
          <div style={{ background: 'white', borderRadius: 16, padding: 24, border: '1px solid #eee' }}>
            <div style={{ fontWeight: 600, marginBottom: 16, fontSize: 15 }}>City Risk Score — 24h Trend</div>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={mockRiskTrend}>
                <defs>
                  <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#534AB7" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#534AB7" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="time" tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Area type="monotone" dataKey="score" stroke="#534AB7" strokeWidth={2}
                  fill="url(#riskGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Incident Type Pie */}
          <div style={{ background: 'white', borderRadius: 16, padding: 24, border: '1px solid #eee' }}>
            <div style={{ fontWeight: 600, marginBottom: 16, fontSize: 15 }}>Incident Types</div>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={mockIncidentTypes} cx="50%" cy="50%" innerRadius={55}
                  outerRadius={85} paddingAngle={3} dataKey="value">
                  {mockIncidentTypes.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Legend iconSize={10} iconType="circle" wrapperStyle={{ fontSize: 12 }} />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Live Incidents Table */}
        <div style={{ background: 'white', borderRadius: 16, padding: 24, border: '1px solid #eee' }}>
          <div style={{ fontWeight: 600, marginBottom: 16, fontSize: 15, display: 'flex',
            justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Live Incidents</span>
            <span style={{ fontSize: 12, color: '#888', fontWeight: 400 }}>
              Auto-refreshes every 10s
            </span>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #eee' }}>
                {['ID', 'Type', 'Zone', 'Time', 'Status', 'Action'].map(h => (
                  <th key={h} style={{ textAlign: 'left', padding: '8px 12px',
                    color: '#888', fontSize: 12, fontWeight: 500 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {activeIncidents.map(inc => (
                <tr key={inc.id} style={{ borderBottom: '1px solid #f5f5f5' }}>
                  <td style={{ padding: '12px', fontFamily: 'monospace', fontSize: 12 }}>{inc.id}</td>
                  <td style={{ padding: '12px' }}><BadgeType type={inc.type} /></td>
                  <td style={{ padding: '12px', color: '#555' }}>{inc.zone}</td>
                  <td style={{ padding: '12px', color: '#888' }}>{inc.time}</td>
                  <td style={{ padding: '12px' }}><BadgeStatus status={inc.status} /></td>
                  <td style={{ padding: '12px' }}>
                    <button style={{ background: '#534AB7', color: 'white', border: 'none',
                      borderRadius: 6, padding: '4px 12px', fontSize: 12, cursor: 'pointer' }}>
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
