# Geospatial Agentic AI App

**Maps to Meaning** — Powering Agentic AI Apps with Spatial, Document, and Video Intelligence

A conversational AI agent built with Microsoft Agent Framework and Azure AI Foundry that combines geospatial intelligence from Singapore government APIs (OneMap, URA, MOE), Bing web search, document understanding, and video analysis. Features a split-panel UI with real-time streaming chat and interactive map visualization.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (React + Vite)                                │
│  ┌────────────────────┬────────────────────────────┐    │
│  │  Chat Panel        │  Map Panel (Leaflet/OneMap)│    │
│  │  - Streaming text  │  - Markers & popups       │    │
│  │  - Tool call cards │  - Polygons & GeoJSON     │    │
│  │  - File upload     │  - Routes & circles       │    │
│  │  - Geolocation     │  - Planning area bounds   │    │
│  └────────┬───────────┴──────────────┬─────────────┘    │
│           │ WebSocket                │                   │
└───────────┼──────────────────────────┼───────────────────┘
            ▼                          │
┌───────────────────────────────────────────────────────────┐
│  Backend (FastAPI)                                        │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Agent (Microsoft Agent Framework + Azure AI)       │  │
│  │  - GPT-5.4 via Azure AI Foundry                     │  │
│  │  - Bing Web Search (server-side grounding)          │  │
│  │  - Session management with TTL eviction             │  │
│  └───┬──────────┬──────────┬───────────────────────────┘  │
│      │ stdio    │ stdio    │ stdio                        │
│  ┌───▼───┐  ┌───▼───┐  ┌──▼────┐                         │
│  │OneMap │  │  URA  │  │  MOE  │                          │
│  │MCP    │  │ MCP   │  │ MCP   │                          │
│  │43 tools│ │10 tools│ │4 tools│                          │
│  └───────┘  └───────┘  └───────┘                          │
└───────────────────────────────────────────────────────────┘
```

- **Frontend**: React 19 + TypeScript + Vite + Material UI + Leaflet (OneMap basemap)
- **Backend**: Python FastAPI with WebSocket streaming
- **Agent**: Microsoft Agent Framework (`agent-framework`) with Azure AI Foundry
- **MCP Servers**: 3 MCP stdio servers providing 57 tools total
- **Web Search**: Bing grounding via Azure AI Foundry (server-side)
- **Auth**: Passcode-protected login page (session-based)

## Prerequisites

- Python 3.11+
- Node.js 18+
- Azure AI Foundry project with GPT-5.4 deployment
- OneMap API credentials ([register here](https://www.onemap.gov.sg/apidocs/register))
- URA API access key ([register here](https://eservice.ura.gov.sg/maps/api/reg.html))
- (Optional) Bing Web Search connection in Azure AI Foundry

## Setup

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your credentials
```

**`.env` configuration:**

```env
ONEMAP_EMAIL=your-email@example.com
ONEMAP_PASSWORD=your-onemap-password
URA_ACCESS_KEY=your-ura-access-key
AZURE_AI_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
MODEL_DEPLOYMENT_NAME=gpt-5.4
AZURE_CONTENT_UNDERSTANDING_ENDPOINT=https://<resource>.cognitiveservices.azure.com
BING_CONNECTION_ID=                         # Optional: Azure AI Foundry Bing connection
```

**Start the backend:**

```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the frontend proxies API/WebSocket calls to the backend on port 8000.

### Docker Compose (Local Containers)

Run all services as containers with MCP servers in streamable-http mode:

```bash
# Copy your .env values — docker-compose reads them automatically
cp backend/.env .env

docker compose up --build
```

Open http://localhost:8080 — the frontend nginx reverse-proxies to the backend container.

### Azure Deployment

Deploy to Azure Container Apps using the Azure Developer CLI (`azd`).

**Prerequisites:**

- [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd) (`azd`)
- Azure subscription with Contributor access
- An existing Azure AI Foundry project with a GPT-5.4 deployment
- Docker (for building container images)

**Deploy:**

```bash
azd auth login
azd init          # select the existing project if already initialized
azd env set AZURE_AI_PROJECT_ENDPOINT "https://<resource>.services.ai.azure.com/api/projects/<project>"
azd env set AZURE_CONTENT_UNDERSTANDING_ENDPOINT "https://<resource>.cognitiveservices.azure.com"
azd env set BING_CONNECTION_ID "<your-bing-connection-id>"
azd env set ONEMAP_EMAIL "<email>"
azd env set ONEMAP_PASSWORD "<password>"
azd env set URA_ACCESS_KEY "<key>"

azd up
```

This provisions: Container Apps Environment, ACR, Key Vault, Log Analytics, User-Assigned Managed Identity, and 5 Container Apps (frontend, backend, mcp-onemap, mcp-ura, mcp-moe). It also assigns the **Cognitive Services User** role on your AI Foundry resource group to the managed identity.

**Architecture (Azure):**

```
Internet
   │
   ▼
┌─────────────────────────────────────────────────────────────────┐
│  Azure Container Apps Environment (Southeast Asia)             │
│                                                                │
│  ┌──────────┐    nginx     ┌──────────┐                        │
│  │ frontend │ ──────────── │ backend  │                        │
│  │ (nginx)  │  reverse     │ (FastAPI)│                        │
│  │ :8080    │  proxy       │ :8000    │                        │
│  └──────────┘              └────┬─────┘                        │
│                          streamable-http                       │
│                    ┌───────────┼───────────┐                   │
│                    ▼           ▼           ▼                   │
│              ┌──────────┐ ┌────────┐ ┌────────┐               │
│              │mcp-onemap│ │mcp-ura │ │mcp-moe │               │
│              │ :8000    │ │ :8000  │ │ :8000  │               │
│              └──────────┘ └────────┘ └────────┘               │
│                                                                │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ Key Vault   │  │ ACR (Basic)  │  │ Log Analytics      │    │
│  │ (API keys)  │  │ (images)     │  │ (container logs)   │    │
│  └─────────────┘  └──────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  Azure AI Foundry (external RG)   │
│  GPT-5.4 │  Bing  │  Content AI   │
│  Managed Identity: Cog Svc User   │
└────────────────────────────────────┘
```

**Known Limitations:**

- **MOE MCP server returns 403 from Azure** — the MOE website (`moe.gov.sg`) blocks Azure data center IPs. School proximity queries work locally but not from Azure Container Apps. The MOE data files in `backend/data/` serve as a local fallback.

## Roadmap

- **Fabric Data Agent integration** (WIP) — A Microsoft Fabric Data Agent will be added as a tool, enabling the agent to query structured datasets (e.g., school details, enrollment statistics) stored in Fabric lakehouses via natural language.

## Features

- **Chat**: Ask about Singapore locations, property data, schools, transport, demographics
- **Streaming**: Real-time streamed responses with tool execution visibility
- **Map**: Auto-updates with markers, polygons, routes, circles, GeoJSON layers based on agent responses
- **Distance Circles**: School queries draw 1 km (green) and 2 km (orange) radius circles on the map
- **Geolocation**: Browser location detected and used for "nearby" queries
- **File Upload**: GeoJSON (renders on map), images/PDFs (OCR + analysis via Azure Content Understanding)
- **Web Search**: Bing grounding for real-time web information (shown as tool call with cited sources)
- **Fallback Map Commands**: Auto-extracts coordinates from tool results even when the agent forgets to emit `mapCommands`

## MCP Servers & Tools (57 total)

### OneMap — Singapore Land Authority (43 tools)

| Category | Tools | Description |
|----------|-------|-------------|
| Search | `search`, `reverse_geocode_wgs84`, `reverse_geocode_svy21` | Address/postal search, reverse geocoding |
| Routing | `get_route` | Walk, drive, cycle, public transport directions |
| Coordinate Conversion | `convert_4326_to_3857`, `convert_4326_to_3414`, `convert_3414_to_3857`, `convert_3414_to_4326`, `convert_3857_to_3414`, `convert_3857_to_4326` | WGS84, SVY21, Web Mercator conversions |
| Themes | `get_all_themes`, `get_theme_info`, `check_theme_status`, `retrieve_theme` | OneMap data layers |
| Transport | `get_nearest_mrt_stops`, `get_nearest_bus_stops` | Nearby MRT/LRT and bus stops |
| Planning Areas | `get_all_planning_areas`, `get_planning_area_names`, `get_planning_area`, `get_planning_area_boundary` | Planning area metadata and polygon boundaries |
| Demographics | `get_economic_status`, `get_education_attending`, `get_ethnic_group`, `get_household_monthly_income`, `get_household_size`, `get_household_structure`, `get_income_from_work`, `get_industry`, `get_language_literate`, `get_marital_status`, `get_mode_of_transport_school`, `get_mode_of_transport_work`, `get_population_age_group`, `get_religion`, `get_spoken_at_home`, `get_tenancy`, `get_dwelling_type_household` | Population data by planning area/year |
| Static Map | `get_static_map` | Generate static map image URLs |
| Land Lots | `retrieve_lot_info_by_lot_key`, `retrieve_land_lot`, `retrieve_land_ownership`, `retrieve_land_lot_search`, `retrieve_lot_info_with_attributes` | Land parcel queries |

### URA — Urban Redevelopment Authority (10 tools)

| Category | Tools | Description |
|----------|-------|-------------|
| Car Parks | `get_car_park_availability`, `get_car_park_details`, `get_season_car_park_details` | Real-time lots, rates, season parking |
| Property | `get_private_resi_transactions`, `get_private_resi_median_rentals`, `get_private_resi_rental_contracts`, `get_private_resi_developer_sales`, `get_private_resi_pipeline` | Transaction history, rental data, developer sales, pipeline |
| Planning | `get_planning_decisions`, `check_approved_residential_use` | Planning permissions and approved use |

### MOE — Ministry of Education (4 tools)

| Tool | API Endpoint | Description |
|------|-------------|-------------|
| `search` | [`/api/onemap/common/elastic/search`](https://www.moe.gov.sg/api/onemap/common/elastic/search?searchVal=522625&returnGeom=Y&getAddrDetails=Y) | Search address by postal code to get BLK_NO, coordinates, and details |
| `query_kindergartens` | [`/api/onemap/moe/queryKindergartens`](https://www.moe.gov.sg/api/onemap/moe/queryKindergartens?postalcode=522625&hbn=625B) | Find MOE kindergartens near an address (needs postalcode + BLK_NO) |
| `query_primary_schools` | [`/api/onemap/moe/querySchools`](https://www.moe.gov.sg/api/onemap/moe/querySchools?postalcode=522625&hbn=625B) | Find primary schools near an address with distance band (dist_code) |
| `nearby_secondary_schools` | [`/api/onemap/moe/nearbySecondarySchools`](https://www.moe.gov.sg/api/onemap/moe/nearbySecondarySchools?latitude=1.36248280964256&longitude=103.940680964014&distance=5000) | Find secondary schools near coordinates within a radius |

**MOE School Finder reference pages:**

- [MOE Kindergartens](https://www.moe.gov.sg/schoolfinder/moe%20kindergarten)
- [Primary Schools](https://www.moe.gov.sg/schoolfinder/primary%20school) — e.g. [Admiralty Primary](https://www.moe.gov.sg/schoolfinder/schooldetail/admiralty-primary-school?_rsc=17k0v)
- [Secondary Schools](https://www.moe.gov.sg/schoolfinder/secondary%20school) — e.g. [Admiralty Secondary](https://www.moe.gov.sg/schoolfinder/schooldetail/admiralty-secondary-school?_rsc=1hewu)
- [Post-Secondary / JC](https://www.moe.gov.sg/schoolfinder/post%20secondary-jc%20school) — e.g. [Anderson Serangoon JC](https://www.moe.gov.sg/schoolfinder/schooldetail/anderson-serangoon-junior-college?_rsc=cd2tb)
- School detail pages: [`/schoolfinder/schooldetail/{slug}`](https://www.moe.gov.sg/schoolfinder/schooldetail/admiralty-primary-school?_rsc=17k0v) — WIP: no API yet, investigate scraping
- Post-Secondary / JC nearby search: WIP — no known public API endpoint yet

**MOE tool workflow:**
1. Call `search(searchVal="522625")` → returns `BLK_NO` (e.g. `"625B"`), latitude, longitude
2. Call `query_primary_schools(postalcode="522625", blk_no="625B")` or `query_kindergartens(...)` using the BLK_NO from step 1
3. For secondary schools: call `nearby_secondary_schools(latitude=..., longitude=..., distance=5000)` using coordinates from step 1

Results include `dist_code`: `"1"` = within 1 km (P1 registration priority), `"2"` = 1–2 km.