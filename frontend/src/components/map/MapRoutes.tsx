import { Polyline, Popup } from 'react-leaflet';
import type { RouteData } from '../../types/map';

interface MapRoutesProps {
  routes: RouteData[];
}

/**
 * Decode an encoded polyline string (Google format) into an array of [lat, lng].
 */
function decodePolyline(encoded: string): [number, number][] {
  const points: [number, number][] = [];
  let index = 0;
  let lat = 0;
  let lng = 0;

  while (index < encoded.length) {
    let b: number;
    let shift = 0;
    let result = 0;

    do {
      b = encoded.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);

    const dlat = result & 1 ? ~(result >> 1) : result >> 1;
    lat += dlat;

    shift = 0;
    result = 0;

    do {
      b = encoded.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);

    const dlng = result & 1 ? ~(result >> 1) : result >> 1;
    lng += dlng;

    points.push([lat / 1e5, lng / 1e5]);
  }

  return points;
}

const MODE_COLORS: Record<string, string> = {
  walk: '#4CAF50',
  drive: '#2196F3',
  cycle: '#FF9800',
  pt: '#9C27B0',
};

export default function MapRoutes({ routes }: MapRoutesProps) {
  return (
    <>
      {routes.map((route, idx) => {
        let positions: [number, number][];

        if (typeof route.geometry === 'string') {
          positions = decodePolyline(route.geometry);
        } else {
          positions = route.geometry as [number, number][];
        }

        const color = route.color || MODE_COLORS[route.mode || 'drive'] || '#2196F3';

        return (
          <Polyline
            key={`route-${idx}`}
            positions={positions}
            pathOptions={{ color, weight: 4, opacity: 0.8 }}
          >
            {route.summary && (
              <Popup>
                {route.mode && <strong>{route.mode.toUpperCase()}</strong>}
                {route.summary.distance && <div>Distance: {route.summary.distance}</div>}
                {route.summary.time && <div>Time: {route.summary.time}</div>}
              </Popup>
            )}
          </Polyline>
        );
      })}
    </>
  );
}
