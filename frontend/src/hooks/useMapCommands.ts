import { useState, useCallback, useEffect } from 'react';
import type { MapCommand } from '../types/chat';
import type { MapState, MarkerData, PolygonData, RouteData, GeoJSONData, ViewData } from '../types/map';
import { DEFAULT_MAP_STATE } from '../types/map';

interface UseMapCommandsReturn {
  mapState: MapState;
  processCommands: (commands: MapCommand[]) => void;
  clearAll: () => void;
}

export function useMapCommands(): UseMapCommandsReturn {
  const [mapState, setMapState] = useState<MapState>(DEFAULT_MAP_STATE);

  const processCommands = useCallback((commands: MapCommand[]) => {
    setMapState((prev) => {
      let next = { ...prev };

      for (const cmd of commands) {
        switch (cmd.action) {
          case 'clearMap':
            next = {
              ...DEFAULT_MAP_STATE,
              view: next.view,
            };
            break;

          case 'setView': {
            const viewData = cmd.data as unknown as ViewData;
            next = {
              ...next,
              view: {
                lat: viewData.lat,
                lng: viewData.lng,
                zoom: viewData.zoom ?? next.view.zoom,
              },
            };
            break;
          }

          case 'addMarkers': {
            const markersData = (cmd.data as { markers: MarkerData[] }).markers || [];
            next = {
              ...next,
              markers: [...next.markers, ...markersData],
            };
            // Auto-center on first marker if multiple markers
            if (markersData.length > 0) {
              const firstMarker = markersData[0];
              next.view = {
                lat: firstMarker.lat,
                lng: firstMarker.lng,
                zoom: markersData.length === 1 ? 16 : 14,
              };
            }
            break;
          }

          case 'addPolygon': {
            const polygonData = cmd.data as unknown as PolygonData;
            next = {
              ...next,
              polygons: [...next.polygons, polygonData],
            };
            // Center on polygon centroid
            if (polygonData.coordinates && polygonData.coordinates.length > 0) {
              const lats = polygonData.coordinates.map((c) => c[0]);
              const lngs = polygonData.coordinates.map((c) => c[1]);
              next.view = {
                lat: (Math.min(...lats) + Math.max(...lats)) / 2,
                lng: (Math.min(...lngs) + Math.max(...lngs)) / 2,
                zoom: 14,
              };
            }
            break;
          }

          case 'addRoute': {
            const routeData = cmd.data as unknown as RouteData;
            next = {
              ...next,
              routes: [...next.routes, routeData],
            };
            break;
          }

          case 'addGeoJSON': {
            const geoData = cmd.data as unknown as GeoJSONData;
            next = {
              ...next,
              geojsonLayers: [...next.geojsonLayers, geoData],
            };
            break;
          }
        }
      }

      return next;
    });
  }, []);

  const clearAll = useCallback(() => {
    setMapState(DEFAULT_MAP_STATE);
  }, []);

  return { mapState, processCommands, clearAll };
}

export function useMapCommandProcessor(
  mapCommands: MapCommand[],
  processCommands: (commands: MapCommand[]) => void,
  clearMapCommands: () => void,
) {
  useEffect(() => {
    if (mapCommands.length > 0) {
      processCommands(mapCommands);
      clearMapCommands();
    }
  }, [mapCommands, processCommands, clearMapCommands]);
}
