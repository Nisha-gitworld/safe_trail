import React, { useState } from 'react';

const RISK_LEVELS = ['safe', 'caution', 'danger'];
const RISK_COLORS = { safe: '#639922', caution: '#BA7517', danger: '#E24B4A' };

const DEMO_ZONES = [
  { id: 'z1', name: 'Dharavi High Risk Zone', city: 'MUM', risk: 'danger',  score: 82, active: true  },
  { id: 'z2', name: 'Kurla Station',          city: 'MUM', risk: 'caution', score: 58, active: true  },
  { id: 'z3', name: 'Marine Drive',           city: 'MUM', risk: 'safe',    score: 18, active: true  },
  { id: 'z4', name: 'Colaba Market',          city: 'MUM', risk: 'caution', score: 47, active: true  },
  { id: 'z5', name: 'Connaught Place',        city: 'DEL', risk: 'caution', score: 52, active: true  },
  { id: 'z6', name: 'Hauz Khas Village',      city: 'DEL', risk: 'safe',    score: 21, active: false },
];

export default function ZoneManager() {
  const [zones, setZones] = useState(DEMO_ZONES);
  const [filter, setFilter] = useState('all');
  const [newZone, setNewZone] = useState({
    name: '', city: 'MUM', risk: 'caution', score: 50,
  });
  const [adding, setAdding] = useState(false);

  const filtered = filter === 'all' ? zones : zones.filter(z => z.risk === filter);

  const toggleActive = (id) => {
    setZones(prev => prev.map(z => z.id === id ? { ...z, active: !z.active } : z));
  };

  const handleAdd = () => {
    if (!newZone.name) return;
    setZones(prev => [...prev, {
      ...newZone, id: `z${Date.now()}`, active: true,
    }]);
    setNewZone({ name: '', city: 'MUM', risk: 'caution', score: 50 });
    setAdding(false);
  };

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between',
        alignItems: 'center', marginBottom: 16 }}>
        <div>
          <div style={{ fontWeight: 600, fontSize: 18 }}>Geofence Zone Manager</div>
          <div style={{ fontSize: 13, color: '#888' }}>{zones.length} zones configured</div>
        </div>
        <button
          onClick={() => setAdding(!adding)}
          style={{ background: '#534AB7', color: 'white', border: 'none',
            borderRadius: 8, padding: '8px 16px', fontSize: 13, cursor: 'pointer' }}>
          + Add Zone
        </button>
      </div>

      {/* Add form */}
      {adding && (
        <div style={{ background: '#f9f8f5', borderRadius: 12, padding: 16,
          marginBottom: 16, border: '1px solid #eee' }}>
          <div style={{ fontWeight: 500, marginBottom: 12 }}>New geofence zone</div>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: 10 }}>
            <input
              placeholder="Zone name"
              value={newZone.name}
              onChange={e => setNewZone(p => ({ ...p, name: e.target.value }))}
              style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #ddd', fontSize: 13 }}
            />
            <select value={newZone.city}
              onChange={e => setNewZone(p => ({ ...p, city: e.target.value }))}
              style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #ddd', fontSize: 13 }}>
              {['MUM', 'DEL', 'BLR'].map(c => <option key={c}>{c}</option>)}
            </select>
            <select value={newZone.risk}
              onChange={e => setNewZone(p => ({ ...p, risk: e.target.value }))}
              style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #ddd', fontSize: 13 }}>
              {RISK_LEVELS.map(r => <option key={r}>{r}</option>)}
            </select>
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={handleAdd} style={{ flex: 1, background: '#534AB7',
                color: 'white', border: 'none', borderRadius: 8, fontSize: 13, cursor: 'pointer' }}>
                Save
              </button>
              <button onClick={() => setAdding(false)} style={{ flex: 1, background: '#eee',
                border: 'none', borderRadius: 8, fontSize: 13, cursor: 'pointer' }}>
                Cancel
              </button>
            </div>
          </div>
          <div style={{ fontSize: 11, color: '#aaa', marginTop: 8 }}>
            Note: In production, draw the boundary on the map to generate WKT polygon coordinates.
          </div>
        </div>
      )}

      {/* Filter pills */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
        {['all', ...RISK_LEVELS].map(f => (
          <button key={f} onClick={() => setFilter(f)} style={{
            padding: '5px 14px', borderRadius: 20, border: 'none',
            fontSize: 12, cursor: 'pointer', fontWeight: filter === f ? 600 : 400,
            background: filter === f
              ? (RISK_COLORS[f] || '#534AB7')
              : '#eee',
            color: filter === f ? 'white' : '#555',
          }}>
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Zone table */}
      <div style={{ borderRadius: 12, overflow: 'hidden', border: '1px solid #eee' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ background: '#f9f8f5', borderBottom: '1px solid #eee' }}>
              {['Zone name', 'City', 'Risk level', 'Score', 'Status', 'Actions'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '10px 14px',
                  color: '#888', fontWeight: 500, fontSize: 12 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map(zone => (
              <tr key={zone.id} style={{ borderBottom: '1px solid #f5f5f5' }}>
                <td style={{ padding: '11px 14px', fontWeight: 500 }}>{zone.name}</td>
                <td style={{ padding: '11px 14px', color: '#555' }}>{zone.city}</td>
                <td style={{ padding: '11px 14px' }}>
                  <span style={{
                    padding: '2px 10px', borderRadius: 20, fontSize: 12,
                    background: `${RISK_COLORS[zone.risk]}22`,
                    color: RISK_COLORS[zone.risk],
                    fontWeight: 600,
                  }}>
                    {zone.risk}
                  </span>
                </td>
                <td style={{ padding: '11px 14px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ height: 6, borderRadius: 3, flex: 1, background: '#eee' }}>
                      <div style={{ height: '100%', borderRadius: 3,
                        width: `${zone.score}%`, background: RISK_COLORS[zone.risk] }} />
                    </div>
                    <span style={{ fontSize: 11, color: '#888', minWidth: 24 }}>{zone.score}</span>
                  </div>
                </td>
                <td style={{ padding: '11px 14px' }}>
                  <span style={{
                    fontSize: 11, padding: '2px 10px', borderRadius: 20,
                    background: zone.active ? '#EAF3DE' : '#f5f5f5',
                    color: zone.active ? '#27500A' : '#aaa',
                  }}>
                    {zone.active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td style={{ padding: '11px 14px' }}>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button
                      onClick={() => toggleActive(zone.id)}
                      style={{ fontSize: 11, padding: '4px 10px', borderRadius: 6,
                        background: zone.active ? '#FCF3EB' : '#EAF3DE',
                        color: zone.active ? '#633806' : '#27500A',
                        border: 'none', cursor: 'pointer' }}>
                      {zone.active ? 'Deactivate' : 'Activate'}
                    </button>
                    <button style={{ fontSize: 11, padding: '4px 10px', borderRadius: 6,
                      background: '#EEEDFE', color: '#534AB7', border: 'none', cursor: 'pointer' }}>
                      Edit
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
