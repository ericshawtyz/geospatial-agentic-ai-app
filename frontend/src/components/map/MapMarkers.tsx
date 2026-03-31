import { Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import type { MarkerData } from '../../types/map';

// Fix default Leaflet marker icon issue with bundlers
const defaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

interface MapMarkersProps {
  markers: MarkerData[];
}

export default function MapMarkers({ markers }: MapMarkersProps) {
  return (
    <>
      {markers.map((marker, idx) => (
        <Marker
          key={`marker-${idx}-${marker.lat}-${marker.lng}`}
          position={[marker.lat, marker.lng]}
          icon={defaultIcon}
        >
          {(marker.label || marker.popup) && (
            <Popup>
              {marker.label && <strong>{marker.label}</strong>}
              {marker.label && marker.popup && <br />}
              {marker.popup && <span>{marker.popup}</span>}
            </Popup>
          )}
        </Marker>
      ))}
    </>
  );
}
