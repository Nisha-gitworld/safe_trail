import React, { useState, useEffect } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from 'recharts';

const API_BASE = 'http://localhost:8000/api';

const PRESET_LOCATIONS = [
  { name: 'Mumbai (Central)', lat: 19.076, lng: 72.877 },
  { name: 'Delhi (Connaught Place)', lat: 28.632, lng: 77.219 },
  { name: 'Bengaluru (Koramangala)', lat: 12.935, lng: 77.624 },
  { name: 'Goa (Panaji)', lat: 15.498, lng: 73.827 },
  { name: 'Kolkata (Park Street)', lat: 22.553, lng: 88.351 },
  { name: 'London (Westminster)', lat: 51.500, lng: -0.124 },
  { name: 'New York (Times Square)', lat: 40.758, lng: -73.985 },
];

// ── Mock data (for historical reference) ──────────────────────────────────────
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

// ── UI Components ─────────────────────────────────────────────────────────────
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
  const [activeIncidents] = useState(mockIncidents);
  const [location, setLocation] = useState(PRESET_LOCATIONS[0]);
  const [customLat, setCustomLat] = useState('19.076');
  const [customLng, setCustomLng] = useState('72.877');
  const [locationStatus, setLocationStatus] = useState('');

  const [liveAssessment, setLiveAssessment] = useState(null);
  const [liveWeather, setLiveWeather] = useState(null);
  const [nearbyServices, setNearbyServices] = useState([]);
  const [loadingFeeds, setLoadingFeeds] = useState(true);

  // Fetch real-time feeds whenever location changes
  useEffect(() => {
    async function fetchRealTimeData() {
      setLoadingFeeds(true);
      try {
        const [assessRes, weatherRes, servicesRes] = await Promise.all([
          fetch(`${API_BASE}/risk/live-assessment?lat=${location.lat}&lng=${location.lng}`),
          fetch(`${API_BASE}/risk/weather?lat=${location.lat}&lng=${location.lng}`),
          fetch(`${API_BASE}/incident/nearby-services?lat=${location.lat}&lng=${location.lng}&radius=3500`),
        ]);

        if (assessRes.ok) setLiveAssessment(await assessRes.json());
        if (weatherRes.ok) setLiveWeather(await weatherRes.json());
        if (servicesRes.ok) {
          const s = await servicesRes.json();
          setNearbyServices(s.services || []);
        }
      } catch (err) {
        console.warn('Real-time feed error:', err);
      } finally {
        setLoadingFeeds(false);
      }
    }

    fetchRealTimeData();
    const interval = setInterval(fetchRealTimeData, 15000); // Polling every 15s
    return () => clearInterval(interval);
  }, [location.lat, location.lng]);

  // Use browser GPS
  const handleUseDeviceLocation = () => {
    if (!navigator.geolocation) {
      setLocationStatus('Geolocation is not supported by your browser.');
      return;
    }
    setLocationStatus('Requesting browser GPS permission...');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = parseFloat(pos.coords.latitude.toFixed(4));
        const lng = parseFloat(pos.coords.longitude.toFixed(4));
        setLocation({
          name: 'My Device GPS Location',
          lat,
          lng,
        });
        setCustomLat(lat.toString());
        setCustomLng(lng.toString());
        setLocationStatus('GPS location acquired!');
        setTimeout(() => setLocationStatus(''), 4000);
      },
      (err) => {
        setLocationStatus(`Could not get GPS: ${err.message}`);
        setTimeout(() => setLocationStatus(''), 5000);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  // Change via city dropdown
  const handlePresetChange = (e) => {
    const selected = PRESET_LOCATIONS.find(p => p.name === e.target.value);
    if (selected) {
      setLocation(selected);
      setCustomLat(selected.lat.toString());
      setCustomLng(selected.lng.toString());
      setLocationStatus(`Switched to ${selected.name}`);
      setTimeout(() => setLocationStatus(''), 3000);
    }
  };

  // Change via manual coordinates
  const handleApplyCoordinates = (e) => {
    e.preventDefault();
    const lat = parseFloat(customLat);
    const lng = parseFloat(customLng);
    if (isNaN(lat) || isNaN(lng) || lat < -90 || lat > 90 || lng < -180 || lng > 180) {
      setLocationStatus('Please enter valid latitude (-90 to 90) and longitude (-180 to 180).');
      return;
    }
    setLocation({
      name: `Custom (${lat.toFixed(3)}°, ${lng.toFixed(3)}°)`,
      lat,
      lng,
    });
    setLocationStatus('Coordinates updated!');
    setTimeout(() => setLocationStatus(''), 3000);
  };

  const score = liveAssessment ? liveAssessment.danger_score : 28;
  const scoreColor = score < 40 ? '#639922' : score < 70 ? '#BA7517' : '#E24B4A';

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', background: '#f5f4f0', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{
        background: '#534AB7', padding: '14px 28px', display: 'flex',
        alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10,
      }}>
        <div style={{ color: 'white', fontWeight: 700, fontSize: 20, display: 'flex', alignItems: 'center', gap: 10 }}>
          <span>🛡️ SafeTrail — Live Safety Platform</span>
          <span style={{ fontSize: 11, background: '#2E7D32', color: 'white', padding: '2px 8px', borderRadius: 12 }}>
            REAL-TIME FEEDS ACTIVE
          </span>
        </div>
        <div style={{ color: 'rgba(255,255,255,0.9)', fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontWeight: 600 }}>{location.name}</span>
          <span>({location.lat.toFixed(4)}°N, {location.lng.toFixed(4)}°E)</span>
        </div>
      </div>

      {/* Location Control Bar */}
      <div style={{
        background: 'white', borderBottom: '1px solid #e2e8f0', padding: '12px 28px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16,
      }}>
        {/* Left: Device GPS & City Dropdown */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <button
            onClick={handleUseDeviceLocation}
            style={{
              background: '#2E7D32', color: 'white', border: 'none', borderRadius: 8,
              padding: '8px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: 6,
            }}
          >
            <span>📍 Use My Device Location</span>
          </button>

          <span style={{ color: '#aaa', fontSize: 13 }}>or select preset:</span>

          <select
            value={PRESET_LOCATIONS.some(p => p.name === location.name) ? location.name : ''}
            onChange={handlePresetChange}
            style={{
              padding: '7px 12px', borderRadius: 8, border: '1px solid #cbd5e1',
              fontSize: 13, background: '#f8fafc', color: '#1e293b', cursor: 'pointer',
            }}
          >
            <option value="" disabled>Choose City...</option>
            {PRESET_LOCATIONS.map(p => (
              <option key={p.name} value={p.name}>{p.name}</option>
            ))}
          </select>
        </div>

        {/* Right: Manual Lat / Lng inputs */}
        <form onSubmit={handleApplyCoordinates} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 12, color: '#64748b', fontWeight: 500 }}>Custom GPS:</span>
          <input
            type="text"
            placeholder="Latitude"
            value={customLat}
            onChange={(e) => setCustomLat(e.target.value)}
            style={{ width: 85, padding: '6px 10px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: 13 }}
          />
          <input
            type="text"
            placeholder="Longitude"
            value={customLng}
            onChange={(e) => setCustomLng(e.target.value)}
            style={{ width: 85, padding: '6px 10px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: 13 }}
          />
          <button
            type="submit"
            style={{
              background: '#534AB7', color: 'white', border: 'none', borderRadius: 6,
              padding: '6px 14px', fontSize: 13, fontWeight: 500, cursor: 'pointer',
            }}
          >
            Set Location
          </button>
        </form>

        {locationStatus && (
          <div style={{ width: '100%', fontSize: 12, color: '#1e293b', background: '#f1f5f9', padding: '4px 10px', borderRadius: 6 }}>
            ℹ️ {locationStatus}
          </div>
        )}
      </div>

      <div style={{ padding: 28 }}>
        {/* Stats Row */}
        <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
          <StatCard
            label="Live Safety Risk"
            value={score.toFixed(0)}
            sub={score < 40 ? '● Safe Zone' : score < 70 ? '● Caution' : '● High Alert'}
            color={scoreColor}
          />
          <StatCard
            label="Live Weather"
            value={liveWeather ? `${liveWeather.temperature_c}°C` : '29°C'}
            sub={liveWeather ? `${liveWeather.hazard_description} · ${liveWeather.wind_speed_kmh} km/h wind` : 'Open-Meteo Feed'}
            color="#2979FF"
          />
          <StatCard
            label="Nearest Police Station"
            value={liveAssessment?.nearest_police ? liveAssessment.nearest_police.split('(')[0].trim() : (nearbyServices.find(s => s.type === 'police')?.name || 'Scanning...')}
            sub={liveAssessment?.nearest_police ? (liveAssessment.nearest_police.match(/\((.*?)\)/)?.[1] || 'nearby') : 'from OpenStreetMap'}
            color="#534AB7"
          />
          <StatCard
            label="Nearest Hospital"
            value={liveAssessment?.nearest_medical ? liveAssessment.nearest_medical.split('(')[0].trim() : (nearbyServices.find(s => s.type === 'hospital')?.name || 'Scanning...')}
            sub={liveAssessment?.nearest_medical ? (liveAssessment.nearest_medical.match(/\((.*?)\)/)?.[1] || 'nearby') : 'from OpenStreetMap'}
            color="#1D9E75"
          />
          <StatCard label="Active Area Tourists" value="1,284" sub="streaming live GPS" color="#E65100" />
        </div>

        {/* Real-time Infrastructure & Weather Radar */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
          {/* Real Emergency Services Feed from OpenStreetMap */}
          <div style={{ background: 'white', borderRadius: 16, padding: 24, border: '1px solid #eee' }}>
            <div style={{ fontWeight: 600, marginBottom: 12, fontSize: 15, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>🚨 Live Emergency Infrastructure (OpenStreetMap)</span>
              <span style={{ fontSize: 12, color: '#666', background: '#eef2ff', padding: '3px 8px', borderRadius: 6 }}>
                Within 3.5 km
              </span>
            </div>
            {loadingFeeds ? (
              <div style={{ color: '#888', fontSize: 13, padding: 20 }}>Scanning OpenStreetMap POIs for this location...</div>
            ) : nearbyServices.length === 0 ? (
              <div style={{ color: '#888', fontSize: 13, padding: 20 }}>
                No registered police stations or hospitals found within 3.5 km of these coordinates.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxHeight: 240, overflowY: 'auto' }}>
                {nearbyServices.slice(0, 6).map((srv, idx) => (
                  <div key={idx} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '8px 12px', background: '#fbfbfb', borderRadius: 8, border: '1px solid #f0f0f0',
                  }}>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: '#333' }}>
                        {srv.type === 'police' ? '🚔 ' : '🏥 '} {srv.name}
                      </div>
                      <div style={{ fontSize: 11, color: '#888' }}>
                        Lat: {srv.lat.toFixed(4)}, Lng: {srv.lng.toFixed(4)} · Source: {srv.source}
                      </div>
                    </div>
                    <span style={{
                      fontSize: 12, fontWeight: 600,
                      color: srv.type === 'police' ? '#303F9F' : '#2E7D32',
                      background: srv.type === 'police' ? '#E8EAF6' : '#E8F5E9',
                      padding: '2px 8px', borderRadius: 12,
                    }}>
                      {srv.distance_meters > 1000
                        ? `${(srv.distance_meters / 1000).toFixed(1)} km`
                        : `${srv.distance_meters.toFixed(0)} m`}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Environmental Hazard & Live Weather */}
          <div style={{ background: 'white', borderRadius: 16, padding: 24, border: '1px solid #eee' }}>
            <div style={{ fontWeight: 600, marginBottom: 12, fontSize: 15, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>🌤️ Environmental & Weather Safety Feed</span>
              <span style={{ fontSize: 12, color: '#666', background: '#e0f2fe', padding: '3px 8px', borderRadius: 6 }}>
                Open-Meteo Live API
              </span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12, marginTop: 10 }}>
              <div style={{ padding: 12, background: '#f8fafc', borderRadius: 8 }}>
                <div style={{ fontSize: 12, color: '#64748b' }}>Heat Index / Feels Like</div>
                <div style={{ fontSize: 20, fontWeight: 600, color: '#0f172a', marginTop: 4 }}>
                  {liveWeather?.feels_like_c ?? '--'}°C
                </div>
              </div>
              <div style={{ padding: 12, background: '#f8fafc', borderRadius: 8 }}>
                <div style={{ fontSize: 12, color: '#64748b' }}>Relative Humidity</div>
                <div style={{ fontSize: 20, fontWeight: 600, color: '#0f172a', marginTop: 4 }}>
                  {liveWeather?.humidity_pct ?? '--'}%
                </div>
              </div>
              <div style={{ padding: 12, background: '#f8fafc', borderRadius: 8 }}>
                <div style={{ fontSize: 12, color: '#64748b' }}>Rainfall Rate</div>
                <div style={{ fontSize: 20, fontWeight: 600, color: '#0f172a', marginTop: 4 }}>
                  {liveWeather?.rain_mm ?? 0} mm/h
                </div>
              </div>
              <div style={{ padding: 12, background: '#f8fafc', borderRadius: 8 }}>
                <div style={{ fontSize: 12, color: '#64748b' }}>Wind & Gusts</div>
                <div style={{ fontSize: 20, fontWeight: 600, color: '#0f172a', marginTop: 4 }}>
                  {liveWeather?.wind_speed_kmh ?? '--'} km/h
                </div>
              </div>
            </div>
            <div style={{ marginTop: 14, fontSize: 12, color: '#475569', background: '#f1f5f9', padding: '8px 12px', borderRadius: 8 }}>
              <strong>AI Recommendation: </strong>
              {liveAssessment?.recommendation || 'All clear — environmental conditions safe for tourists.'}
            </div>
          </div>
        </div>

        {/* Analytics Charts */}
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
              Auto-refreshes every 15s
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
