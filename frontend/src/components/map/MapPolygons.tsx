import { Polygon, Popup } from 'react-leaflet';
import type { PolygonData } from '../../types/map';

interface MapPolygonsProps {
  polygons: PolygonData[];
}

export default function MapPolygons({ polygons }: MapPolygonsProps) {
  return (
    <>
      {polygons.map((poly, idx) => (
        <Polygon
          key={`polygon-${idx}`}
          positions={poly.coordinates.map((c) => [c[0], c[1]] as [number, number])}
          pathOptions={{
            color: poly.color || '#3388ff',
            fillColor: poly.fillColor || '#3388ff',
            fillOpacity: 0.6,
            weight: 3,
          }}
        >
          {poly.label && (
            <Popup>
              <strong>{poly.label}</strong>
            </Popup>
          )}
        </Polygon>
      ))}
    </>
  );
}
