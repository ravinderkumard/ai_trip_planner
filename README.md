# AI Trip Planner

AI Trip Planner is an agent-based travel planning application that turns a natural-language trip request into a detailed itinerary. The project combines a FastAPI backend, a LangGraph workflow, and a Streamlit frontend to generate travel plans that include attractions, restaurants, activities, transportation guidance, weather context, and approximate trip costs.

The repository is structured as a small end-to-end application rather than a library. The backend handles orchestration, the agent decides when to use tools, and the frontend provides an interactive way to submit requests and observe execution progress.

## What the project does

- Accepts free-form trip planning prompts such as `Plan a trip to Goa for 5 days`
- Uses an LLM with tools for place search, weather lookup, budgeting, and currency conversion
- Streams execution trace events while the workflow is running
- Saves generated itineraries as Markdown files under `output/`
- Generates a workflow diagram image as part of execution

## Repository structure

- [`main.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/main.py): FastAPI application and API endpoints
- [`streamlit_app.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/streamlit_app.py): Streamlit frontend
- [`agent/agentic_workflow.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/agent/agentic_workflow.py): LangGraph workflow assembly
- [`tools/`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/tools): LangChain tool wrappers
- [`utils/`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/utils): helper services and utilities
- [`config/config.yaml`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/config/config.yaml): model configuration
- [`DESIGN.md`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/DESIGN.md): implementation design document

## How it works

1. The user enters a travel request in the Streamlit UI.
2. The frontend sends that request to the FastAPI backend.
3. The backend builds a LangGraph workflow through `GraphBuilder`.
4. The language model decides when to answer directly and when to call supporting tools.
5. The final itinerary is returned to the UI and also saved to a Markdown file.

## Tech stack

- Python
- FastAPI
- Streamlit
- LangChain
- LangGraph
- OpenAI and Groq integrations
- Tavily search

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

## Design document

The detailed implementation notes for this repository are available in [`DESIGN.md`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/DESIGN.md). That document explains the architecture, request flow, tool integration, persistence model, and current limitations of the project.

## Current status

This codebase is in a working prototype stage. The main flow is present and usable, but there is still room to improve resilience, testing, cleanup, and production hardening.
