# AI Trip Planner

AI Trip Planner is an agent-based travel planning application that turns a natural-language trip request into a detailed itinerary. The project combines a FastAPI backend, a LangGraph workflow, a Streamlit frontend, and a Redis-backed worker path to generate travel plans that include attractions, restaurants, activities, transportation guidance, weather context, and approximate trip costs.

The repository is structured as a small end-to-end application rather than a library. The backend handles orchestration, the agent decides when to use tools, and the frontend provides an interactive way to submit requests and observe execution progress.

## What the project does

- Accepts free-form trip planning prompts such as `Plan a trip to Goa for 5 days`
- Uses an LLM with tools for place search, weather lookup, budgeting, and currency conversion
- Streams execution trace events while the workflow is running
- Saves generated itineraries as Markdown files under `output/`
- Generates a workflow diagram image as part of execution
- Supports asynchronous request processing through a Redis stream worker
- Tracks token usage for each workflow run

## Security measures currently implemented

- Request validation for incoming travel queries
- Restricted CORS defaults with environment-based origin overrides
- In-memory rate limiting for both API endpoints
- Safer error handling that avoids returning raw internal exceptions to clients
- Timeout-based protection for outbound weather and currency API calls
- Targeted application logging for request flow and external service failures
- Prompt-injection screening for suspicious input patterns at the API boundary
- Validation of place-search tool arguments before Tavily calls are made
- Sanitization of Tavily search results before they are passed back to the model
- A hardened system prompt that tells the model to treat retrieved content as untrusted

## Repository structure

- [`main.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/main.py): FastAPI application and API endpoints
- [`streamlit_app.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/streamlit_app.py): Streamlit frontend
- [`worker.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/worker.py): Redis stream worker for background task processing
- [`run_worker.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/run_worker.py): worker entry point
- [`agent/agentic_workflow.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/agent/agentic_workflow.py): LangGraph workflow assembly
- [`tools/`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/tools): LangChain tool wrappers
- [`utils/`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/utils): helper services and utilities
- [`config/config.yaml`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/config/config.yaml): model configuration
- [`Dockerfile`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/Dockerfile): container image definition
- [`docker-compose.yml`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/docker-compose.yml): local multi-service deployment
- [`DESIGN.md`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/DESIGN.md): implementation design document

## How it works

1. The user enters a travel request in the Streamlit UI.
2. The frontend sends that request to the FastAPI backend.
3. The backend builds a LangGraph workflow through `GraphBuilder`.
4. The language model decides when to answer directly and when to call supporting tools.
5. The final itinerary is returned to the UI and also saved to a Markdown file.

## Processing modes

### Direct API mode

- Streamlit sends a `question` payload to the FastAPI backend
- The backend executes the agent immediately
- Execution trace and token usage are returned in the streamed response

### Worker mode

- A producer writes tasks into the Redis `agent_tasks` stream
- [`worker.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/worker.py) reads those tasks and normalizes the payload into a travel query
- The worker runs the same shared travel-agent execution path used by the API
- Results are written back to the Redis `agent_results` stream
- Each Redis stream entry must contain a field named `data`, and `data` must be a JSON string payload

The worker currently accepts both of these task input styles:

```json
{
  "data": "{\"agent\":\"travel_agent\",\"input\":{\"query\":\"Plan a trip to Goa for 3 days within a budget of INR 20000\"},\"task_id\":\"example-task-id\"}"
}
```

```json
{
  "agent": "travel_agent",
  "input": {
    "query": "Plan a trip to Goa for 3 days within a budget of INR 20000"
  },
  "task_id": "example-task-id"
}
```

```json
{
  "agent": "travel_agent",
  "action": "create_trip_plan",
  "input": {
    "destination": "Goa",
    "duration_days": 3,
    "budget_inr": 20000
  },
  "task_id": "example-task-id"
}
```

## Tech stack

- Python
- FastAPI
- Streamlit
- LangChain
- LangGraph
- OpenAI and Groq integrations
- Tavily search
- Redis
- Docker and Docker Compose

## Local setup

### Prerequisites

- Python 3.13 or a compatible local Python version
- API keys for the providers you plan to use

### Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment variables

Create a `.env` file with the required credentials. Depending on the workflow you want to run, the application may use:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL_NAME=gpt-4.1-nano
GROQ_API_KEY=your_key_here
GROQ_MODEL_NAME=your_model_here
OPENWEATHERMAP_API_KEY=your_key_here
EXCHANGE_RATE_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
CORS_ALLOWED_ORIGINS=http://localhost:8501,http://127.0.0.1:8501
RATE_LIMIT_MAX_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=60
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
BACKEND_URL=http://localhost:8500
```

## Running the application

Start the backend:

```bash
uvicorn main:app --host 0.0.0.0 --port 8500 --reload
```

Start the frontend in a separate terminal:

```bash
streamlit run streamlit_app.py
```

Once both are running, open the Streamlit app in your browser and submit a travel-planning request.

Start the Redis worker in another terminal if you want asynchronous task processing:

```bash
python run_worker.py
```

## Docker setup

The current Docker Compose setup starts:

- FastAPI API
- Streamlit UI
- Redis worker

Redis is expected to run outside Compose. The containers connect to an external Redis instance, typically a Redis server running on the host machine.

To run the containerized app stack:

```bash
docker compose up --build
```

Services:

- FastAPI API: `http://localhost:8500`
- Streamlit UI: `http://localhost:8501`

External Redis expectation:

- Host: `localhost:6379` for local terminal runs
- Host: `host.docker.internal:6379` for container runs when `REDIS_HOST` is not explicitly set

## Design document

The detailed implementation notes for this repository are available in [`DESIGN.md`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/DESIGN.md). That document explains the architecture, request flow, tool integration, persistence model, and current limitations of the project.

## Current status

This codebase is in a working prototype stage. The main flow is present and usable, but there is still room to improve resilience, testing, cleanup, and production hardening.
