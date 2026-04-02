import { Circle, Popup } from 'react-leaflet';
import type { CircleData } from '../../types/map';

interface MapCirclesProps {
  circles: CircleData[];
}

export default function MapCircles({ circles }: MapCirclesProps) {
  return (
    <>
      {circles.map((c, idx) => (
        <Circle
          key={`circle-${idx}`}
          center={[c.lat, c.lng]}
          radius={c.radius}
          pathOptions={{
            color: c.color || '#3388ff',
            fillColor: c.fillColor || '#3388ff',
            fillOpacity: c.fillOpacity ?? 0.1,
            weight: 2,
            dashArray: '6 4',
          }}
        >
          {c.label && (
            <Popup>
              <strong>{c.label}</strong>
            </Popup>
          )}
        </Circle>
      ))}
    </>
  );
}
