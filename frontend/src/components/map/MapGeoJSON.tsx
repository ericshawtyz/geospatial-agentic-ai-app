import { GeoJSON } from 'react-leaflet';
import type { GeoJSONData } from '../../types/map';
import type { PathOptions } from 'leaflet';

interface MapGeoJSONProps {
  layers: GeoJSONData[];
}

export default function MapGeoJSON({ layers }: MapGeoJSONProps) {
  return (
    <>
      {layers.map((layer, idx) => {
        const style: PathOptions = {
          color: layer.style?.color || '#ff6600',
          weight: layer.style?.weight || 3,
          fillColor: layer.style?.fillColor || '#ff6600',
          fillOpacity: layer.style?.fillOpacity || 0.6,
        };

        return (
          <GeoJSON
            key={`geojson-${idx}-${JSON.stringify(layer.geojson).slice(0, 50)}`}
            data={layer.geojson as GeoJSON.GeoJsonObject}
            style={() => style}
          />
        );
      })}
    </>
  );
}
