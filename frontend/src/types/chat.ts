export interface ToolCall {
  name: string;
  arguments: Record<string, unknown>;
  status: 'executing' | 'completed';
  result?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  files?: UploadedFile[];
  tools?: ToolCall[];
}

export interface UploadedFile {
  name: string;
  type: string;
  size: number;
  preview?: string;
}

export interface ChatResponse {
  type: 'delta' | 'done' | 'error' | 'tool_call';
  text?: string;
  mapCommands?: MapCommand[];
  // tool_call fields
  name?: string;
  arguments?: Record<string, unknown>;
  status?: 'executing' | 'completed';
  result?: string;
}

export interface MapCommand {
  action: 'addMarkers' | 'addPolygon' | 'addRoute' | 'addCircle' | 'addGeoJSON' | 'setView' | 'clearMap';
  data: Record<string, unknown>;
}
