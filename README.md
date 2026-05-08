# Geospatial Agentic AI App

**Maps to Meaning** — Powering Agentic AI Apps with Spatial, Document, and Video Intelligence

A conversational AI agent built with Microsoft Agent Framework and Azure AI Foundry that combines geospatial intelligence from Singapore government APIs (OneMap, URA, MOE), Bing web search, document understanding, and video analysis. Features a split-panel UI with real-time streaming chat and interactive map visualization.

## Architecture

The backend can run in **two modes**, selected by the `AGENT_MODE` env var:

- `chat_completion` (default, local dev): in-process agent loop using OpenAI Chat Completions over the Foundry project's OpenAI-compatible endpoint. MCP servers run as local stdio subprocesses (or HTTP if a `*_MCP_URL` is provided).
- `foundry_agent_service` (prod / Container Apps): backend upserts a hosted agent in **Azure AI Foundry Agent Service** that registers the deployed MCP Container Apps as MCP tools. Foundry calls the MCP servers server-side; the backend just streams events to the websocket.

Both modes expose the same websocket event shape, so the frontend is mode-agnostic.

### Local dev (`chat_completion`)

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
│  │  Agent (Microsoft Agent Framework)                  │  │
│  │  - OpenAIChatCompletionClient → Foundry OpenAI v1   │  │
│  │  - GPT-5.4-mini deployment (configurable)           │  │
│  │  - Session management with TTL eviction             │  │
│  └───┬──────────┬──────────┬───────────────────────────┘  │
│      │ stdio    │ stdio    │ stdio                        │
│  ┌───▼───┐  ┌───▼───┐  ┌──▼────┐                          │
│  │OneMap │  │  URA  │  │  MOE  │                          │
│  │MCP    │  │ MCP   │  │ MCP   │                          │
│  │43 tools│ │10 tools│ │4 tools│                          │
│  └───────┘  └───────┘  └───────┘                          │
└───────────────────────────────────────────────────────────┘
```

- **Frontend**: React 19 + TypeScript + Vite + Material UI + Leaflet (OneMap basemap)
- **Backend**: Python FastAPI with WebSocket streaming
- **Agent**: Microsoft Agent Framework (`agent-framework-openai`) over Azure AI Foundry's OpenAI-compatible Chat Completions endpoint
- **MCP Servers**: 3 MCP stdio servers providing 57 tools total
- **Auth**: Passcode-protected login page (session-based)

## Prerequisites

- Python 3.11+
- Node.js 18+
- Azure AI Foundry project with a model deployment (defaults to `gpt-5.4-mini` — any chat model that supports function calling works)
- OneMap API credentials ([register here](https://www.onemap.gov.sg/apidocs/register))
- URA API access key ([register here](https://eservice.ura.gov.sg/maps/api/reg.html))

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
MODEL_DEPLOYMENT_NAME=gpt-5.4-mini
AZURE_CONTENT_UNDERSTANDING_ENDPOINT=https://<resource>.cognitiveservices.azure.com

# Agent runtime (defaults to chat_completion for local dev).
# Set to `foundry_agent_service` only when running in an environment that
# can reach the deployed MCP container apps over public HTTPS.
AGENT_MODE=chat_completion
FOUNDRY_AGENT_NAME=geo-agent
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

In Azure, the backend automatically runs in **`foundry_agent_service` mode** (set by the Bicep template). On startup it upserts a hosted agent in your Azure AI Foundry project named `geo-agent`, registers the three MCP container apps as MCP tools, and lets Foundry call them server-side. The local `lookup_school_details` helper is registered as a function tool and executed in the backend via the `requires_action` handshake.

**Prerequisites:**

- [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd) (`azd`)
- Azure subscription with Contributor access
- An existing Azure AI Foundry project with a chat-capable model deployment (defaults to `gpt-5.4-mini`)
- Docker (for building container images)

**Deploy:**

```bash
azd auth login
azd init          # select the existing project if already initialized
azd env set AZURE_AI_PROJECT_ENDPOINT "https://<resource>.services.ai.azure.com/api/projects/<project>"
azd env set MODEL_DEPLOYMENT_NAME "gpt-5.4-mini"
azd env set AZURE_CONTENT_UNDERSTANDING_ENDPOINT "https://<resource>.cognitiveservices.azure.com"
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
│  │ frontend │ ──────────── │ backend  │   upserts hosted agent │
│  │ (nginx)  │  reverse     │ (FastAPI)│ ───────────────┐       │
│  │ :8080    │  proxy       │ :8000    │                │       │
│  └──────────┘              └────┬─────┘                │       │
│                                 │ run + stream events  │       │
│                                 ▼                      │       │
│  ┌──────────┐ ┌────────┐ ┌────────┐                   │       │
│  │mcp-onemap│ │mcp-ura │ │mcp-moe │ ◄── public HTTPS ──┘       │
│  │ (ext)    │ │ (ext)  │ │ (ext)  │     called by Foundry      │
│  └──────────┘ └────────┘ └────────┘                            │
│                                                                │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ Key Vault   │  │ ACR (Basic)  │  │ Log Analytics      │    │
│  │ (API keys)  │  │ (images)     │  │ (container logs)   │    │
│  └─────────────┘  └──────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
         │                                       ▲
         ▼                                       │
┌────────────────────────────────────┐           │
│  Azure AI Foundry (external RG)   │ ──────────┘
│  GPT-5.4-mini │ Foundry Agent Svc │  thread/run + MCP tool exec
│  Managed Identity: Cog Svc User   │
└────────────────────────────────────┘
```

The backend container is also pre-wired with `AGENT_MODE=foundry_agent_service`, `FOUNDRY_AGENT_NAME=geo-agent`, and the public HTTPS URLs of each MCP container as `*_MCP_URL`. Override any of these by editing [`infra/main.bicep`](infra/main.bicep) if needed (e.g. to point Foundry at a different agent name per environment).

**Known Limitations:**

- **MOE MCP server returns 403 from Azure** — the MOE website (`moe.gov.sg`) blocks Azure data center IPs. School proximity queries work locally but not from Azure Container Apps. The MOE data files in `backend/data/` serve as a local fallback.
- **MCP container apps are publicly reachable** — they need external ingress so Foundry can call them. They don't currently enforce auth; if that's a concern, add an API-key header check in each MCP server and call `McpTool.update_headers(...)` in `_FoundryAgentServiceStrategy.initialize()`.

## Roadmap

- **Fabric Data Agent integration** (WIP) — A Microsoft Fabric Data Agent will be added as a tool, enabling the agent to query structured datasets (e.g., school details, enrollment statistics) stored in Fabric lakehouses via natural language.

## Features

- **Chat**: Ask about Singapore locations, property data, schools, transport, demographics
- **Streaming**: Real-time streamed responses with tool execution visibility
- **Map**: Auto-updates with markers, polygons, routes, circles, GeoJSON layers based on agent responses
- **Distance Circles**: School queries draw 1 km (green) and 2 km (orange) radius circles on the map
- **Geolocation**: Browser location detected and used for "nearby" queries
- **File Upload**: GeoJSON (renders on map), images/PDFs (OCR + analysis via Azure Content Understanding)
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