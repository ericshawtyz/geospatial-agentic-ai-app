import { useEffect } from 'react';
import { MapContainer, TileLayer, useMap, ZoomControl } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import type { MapState } from '../../types/map';
import MapMarkers from './MapMarkers';
import MapPolygons from './MapPolygons';
import MapCircles from './MapCircles';
import MapRoutes from './MapRoutes';
import MapGeoJSON from './MapGeoJSON';

interface MapPanelProps {
  mapState: MapState;
}

function MapViewController({ view }: { view: MapState['view'] }) {
  const map = useMap();

  useEffect(() => {
    map.setView([view.lat, view.lng], view.zoom, { animate: true });
  }, [map, view.lat, view.lng, view.zoom]);

  // Fix grey tiles on resize / sidebar toggle
  useEffect(() => {
    const container = map.getContainer();
    const invalidate = () => map.invalidateSize({ animate: false });

    window.addEventListener('resize', invalidate);

    // ResizeObserver fires continuously during CSS transitions
    const observer = new ResizeObserver(() => {
      invalidate();
    });
    if (container) observer.observe(container);

    // Also listen for CSS transition end on the sidebar's parent
    const parentFlex = container?.parentElement?.parentElement; // map -> mapBox -> flex root
    const onTransitionEnd = (e: TransitionEvent) => {
      if (e.propertyName === 'width' || e.propertyName === 'min-width') {
        invalidate();
      }
    };
    parentFlex?.addEventListener('transitionend', onTransitionEnd);

    // Initial invalidate
    const timer = setTimeout(invalidate, 100);

    return () => {
      window.removeEventListener('resize', invalidate);
      clearTimeout(timer);
      observer.disconnect();
      parentFlex?.removeEventListener('transitionend', onTransitionEnd);
    };
  }, [map]);

  return null;
}

export default function MapPanel({ mapState }: MapPanelProps) {
  return (
    <MapContainer
      center={[mapState.view.lat, mapState.view.lng]}
      zoom={mapState.view.zoom}
      style={{ height: '100%', width: '100%', background: '#6da8e4' }}
      zoomControl={false}
    >
      <ZoomControl position="bottomright" />
      <TileLayer
        attribution='&copy; <a href="https://www.onemap.gov.sg" target="_blank">OneMap</a> &copy; <a href="https://www.sla.gov.sg" target="_blank">SLA</a>'
        url="https://www.onemap.gov.sg/maps/tiles/Default/{z}/{x}/{y}.png"
        maxZoom={19}
        minZoom={11}
      />
      <MapViewController view={mapState.view} />
      <MapMarkers markers={mapState.markers} />
      <MapPolygons polygons={mapState.polygons} />
      <MapCircles circles={mapState.circles} />
      <MapRoutes routes={mapState.routes} />
      <MapGeoJSON layers={mapState.geojsonLayers} />
    </MapContainer>
  );
}
