# Geospatial Agentic AI App

**Maps to Meaning** — Powering Agentic AI Apps with Spatial, Document, and Video Intelligence

A conversational AI agent built with Microsoft Foundry Agent Service that combines geospatial intelligence (OneMap + URA APIs), document understanding, and video analysis. Features a split-panel UI with real-time chat and interactive map visualization.

## Architecture

- **Frontend**: React + TypeScript + Vite + Material UI + Leaflet (OneMap basemap)
- **Backend**: Python FastAPI with WebSocket streaming chat endpoint
- **Agent**: Microsoft Agent Framework with MCP tool connections
- **MCP Servers**: OneMap (44 tools) and URA (10 tools) geospatial API servers
- **Auth**: Passcode-protected login page (session-based)

## Prerequisites

- Python 3.14+
- Node.js 24.14+
- Azure AI Foundry project with GPT-4o deployment
- OneMap API credentials ([register](https://www.onemap.gov.sg/apidocs/register))
- URA API access key ([register](https://eservice.ura.gov.sg/maps/api/reg.html))

## Setup

### Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt

# Copy and fill in your credentials
cp .env.example .env
# Edit .env with your API keys

# Run the backend
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the frontend proxies API/WebSocket calls to the backend.

## Features

- **Login**: Passcode-protected access gate
- **Chat**: Ask about Singapore locations, property data, transport, demographics
- **Streaming**: Real-time streamed responses with animated thinking indicator
- **Tool Calls**: Visible tool execution details (expandable in chat)
- **Map**: Auto-updates with markers, polygons, routes, GeoJSON based on agent responses
- **Geolocation**: Browser location auto-detected and used for "nearby" queries
- **File Upload**: GeoJSON (renders on map), images/PDFs (OCR + analysis), video
- **OneMap Tools** (44): Search, routing, reverse geocoding, coordinate conversion, themes, planning area boundaries, population demographics, land lots, nearby MRT/bus
- **URA Tools** (10): Car parks, property transactions, rentals, developer sales, pipeline, planning decisions, approved use