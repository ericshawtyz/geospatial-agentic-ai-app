export interface MarkerData {
  lat: number;
  lng: number;
  label?: string;
  popup?: string;
}

export interface PolygonData {
  coordinates: [number, number][];
  color?: string;
  fillColor?: string;
  label?: string;
}

export interface RouteData {
  geometry: string | [number, number][];
  mode?: string;
  summary?: {
    distance?: string;
    time?: string;
  };
  color?: string;
}

export interface GeoJSONData {
  geojson: GeoJSON.GeoJsonObject;
  style?: {
    color?: string;
    weight?: number;
    fillColor?: string;
    fillOpacity?: number;
  };
}

export interface ViewData {
  lat: number;
  lng: number;
  zoom: number;
}

export interface MapState {
  markers: MarkerData[];
  polygons: PolygonData[];
  routes: RouteData[];
  geojsonLayers: GeoJSONData[];
  view: ViewData;
}

export const DEFAULT_MAP_STATE: MapState = {
  markers: [],
  polygons: [],
  routes: [],
  geojsonLayers: [],
  view: {
    lat: 1.35,
    lng: 103.8198,
    zoom: 12,
  },
};
