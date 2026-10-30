import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import { CongestionBadge } from '../common/Badge';
import { Info, AlertCircle, ArrowUpRight } from 'lucide-react';

// Custom SVG icon generator for congestion pins
const createCustomIcon = (congestionPct) => {
  let color = '#10B981'; // emerald (<25)
  if (congestionPct > 75) color = '#EF4444'; // rose (>75)
  else if (congestionPct > 50) color = '#F97316'; // orange (>50)
  else if (congestionPct > 25) color = '#F59E0B'; // amber (>25)

  return L.divIcon({
    className: 'custom-traffic-pin',
    html: `
      <div style="
        background-color: ${color};
        width: 24px;
        height: 24px;
        border-radius: 50%;
        border: 2px solid #ffffff;
        box-shadow: 0 0 10px ${color}88, 0 2px 4px rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-weight: 700;
        font-size: 10px;
        font-family: monospace;
      ">
        ${Math.round(congestionPct)}%
      </div>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -14],
  });
};

// Sub-component to pan map smoothly when center changes
function ChangeMapView({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, zoom, { animate: true });
  }, [center, zoom, map]);
  return null;
}

export const TrafficMap = ({
  locations = [],
  center = [28.6139, 77.2090],
  zoom = 12,
  onSelectLocation = null,
  height = '480px',
}) => {
  return (
    <div className="relative rounded-xl overflow-hidden border border-slate-800 shadow-xl bg-slate-950">
      {/* Map Disclaimer Banner */}
      <div className="absolute top-3 left-3 z-[1000] bg-slate-900/90 backdrop-blur-md border border-slate-700/80 px-3 py-1.5 rounded-lg text-xs text-slate-300 flex items-center gap-2 shadow-lg">
        <Info className="w-3.5 h-3.5 text-cyan-400" />
        <span>Analytical Road Network · OpenStreetMap & Zenodo Data</span>
      </div>

      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height, width: '100%' }}
        scrollWheelZoom={true}
        className="z-10"
      >
        <ChangeMapView center={center} zoom={zoom} />

        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          className="map-tiles"
        />

        {locations.map((loc) => {
          const congestion = loc.avg_congestion_pct || loc.congestion_percentage || 45;
          const icon = createCustomIcon(congestion);

          return (
            <React.Fragment key={loc.id || loc.location_code}>
              <Circle
                center={[loc.latitude, loc.longitude]}
                radius={600}
                pathOptions={{
                  color: congestion > 75 ? '#EF4444' : congestion > 50 ? '#F97316' : congestion > 25 ? '#F59E0B' : '#10B981',
                  fillColor: congestion > 75 ? '#EF4444' : congestion > 50 ? '#F97316' : congestion > 25 ? '#F59E0B' : '#10B981',
                  fillOpacity: 0.18,
                  weight: 1.5,
                }}
              />

              <Marker position={[loc.latitude, loc.longitude]} icon={icon}>
                <Popup className="clearroute-map-popup">
                  <div className="p-1 min-w-[220px] text-slate-900">
                    <div className="flex items-center justify-between border-b pb-1.5 mb-2 border-slate-200">
                      <span className="font-bold text-sm text-slate-900">{loc.location_name}</span>
                      <CongestionBadge percentage={congestion} />
                    </div>

                    <div className="space-y-1 text-xs text-slate-600 mb-3 font-sans">
                      <p><strong>Corridor:</strong> {loc.corridor_name || 'Primary Corridor'}</p>
                      <p><strong>Road Class:</strong> <span className="font-mono uppercase">{loc.road_type || 'Primary'}</span> ({loc.road_lanes || 4} lanes)</p>
                      <p><strong>Free Flow:</strong> {loc.free_flow_speed_kmh || 55} km/h</p>
                      <p><strong>Observed Speed:</strong> {loc.observed_speed_kmh || (55 * (1 - congestion / 100)).toFixed(1)} km/h</p>
                    </div>

                    {onSelectLocation && (
                      <button
                        onClick={() => onSelectLocation(loc)}
                        className="w-full bg-cyan-700 hover:bg-cyan-800 text-white text-xs font-semibold py-1.5 px-2 rounded flex items-center justify-center gap-1 transition-colors"
                      >
                        <span>Analyze Corridor</span>
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </Popup>
              </Marker>
            </React.Fragment>
          );
        })}
      </MapContainer>
    </div>
  );
};
