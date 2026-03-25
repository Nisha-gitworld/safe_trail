import React, { useState } from 'react';

const INCIDENT_TYPES = {
  THEFT:      { color: '#F09595', dark: '#501313', label: 'Theft',      icon: '🎒' },
  MEDICAL:    { color: '#E24B4A', dark: '#501313', label: 'Medical',    icon: '🏥' },
  ACCIDENT:   { color: '#FAC775', dark: '#412402', label: 'Accident',   icon: '🚗' },
  HARASSMENT: { color: '#B5D4F4', dark: '#042C53', label: 'Harassment', icon: '🚨' },
  LOST:       { color: '#C0DD97', dark: '#173404', label: 'Lost',       icon: '🗺️'  },
};

export function IncidentCard({ incident, onViewMap }) {
  const [expanded, setExpanded] = useState(false);
  const meta = INCIDENT_TYPES[incident.type] || INCIDENT_TYPES.ACCIDENT;

  return (
    <div style={{
      border: `1px solid ${meta.color}88`,
      borderLeft: `4px solid ${meta.color}`,
      borderRadius: 12, padding: '14px 16px',
      marginBottom: 10, background: `${meta.color}0d`,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between',
        alignItems: 'center', cursor: 'pointer' }}
        onClick={() => setExpanded(!expanded)}>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 20 }}>{meta.icon}</span>
          <div>
            <div style={{ fontWeight: 600, fontSize: 14 }}>{meta.label}</div>
            <div style={{ fontSize: 12, color: '#888' }}>{incident.zone} · {incident.time}</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{
            fontSize: 11, padding: '2px 10px', borderRadius: 20,
            background: incident.status === 'resolved' ? '#EAF3DE' : '#FCEBEB',
            color: incident.status === 'resolved' ? '#27500A' : '#A32D2D',
          }}>
            {incident.status}
          </span>
          <span style={{ color: '#aaa', fontSize: 12 }}>{expanded ? '▲' : '▼'}</span>
        </div>
      </div>

      {expanded && (
        <div style={{ marginTop: 12, paddingTop: 12,
          borderTop: `1px solid ${meta.color}44` }}>

          <div style={{ fontSize: 13, color: '#555', marginBottom: 10 }}>
            {incident.description || 'No description provided'}
          </div>

          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {incident.did && (
              <span style={{ fontSize: 11, padding: '3px 10px', borderRadius: 20,
                background: '#EEEDFE', color: '#534AB7' }}>
                DID: {incident.did.slice(0, 20)}…
              </span>
            )}
            {incident.incidentId && (
              <span style={{ fontSize: 11, padding: '3px 10px', borderRadius: 20,
                background: '#f5f5f5', color: '#555', fontFamily: 'monospace' }}>
                {incident.incidentId}
              </span>
            )}
          </div>

          <div style={{ marginTop: 10, display: 'flex', gap: 8 }}>
            <button
              onClick={() => onViewMap?.(incident)}
              style={{ fontSize: 12, padding: '5px 14px', borderRadius: 8,
                background: '#534AB7', color: 'white', border: 'none', cursor: 'pointer' }}>
              View on map
            </button>
            <button style={{ fontSize: 12, padding: '5px 14px', borderRadius: 8,
              background: 'transparent', color: '#534AB7',
              border: '1px solid #534AB7', cursor: 'pointer' }}>
              Mark resolved
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export function IncidentList({ incidents = [], onViewMap }) {
  if (incidents.length === 0) {
    return (
      <div style={{ textAlign: 'center', color: '#aaa', padding: 40 }}>
        <div style={{ fontSize: 40, marginBottom: 10 }}>✅</div>
        No active incidents
      </div>
    );
  }
  return (
    <div>
      {incidents.map(inc => (
        <IncidentCard key={inc.id} incident={inc} onViewMap={onViewMap} />
      ))}
    </div>
  );
}
