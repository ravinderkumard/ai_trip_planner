# AI Trip Planner

## Design Document

### 1. Purpose

The AI Trip Planner is a travel-planning application built around a tool-using language model. Its goal is to take a natural-language travel request such as "Plan a trip to Goa for 5 days" and turn it into a structured itinerary that includes sightseeing options, accommodation suggestions, transport guidance, weather context, and approximate trip costs.

The implementation combines three layers:

- A FastAPI backend that owns orchestration and exposes the service over HTTP
- A LangGraph-based agent workflow that decides when to answer directly and when to call tools
- A Streamlit frontend that lets a user submit a request and observe execution progress in real time

The current codebase is optimized for a single-user, local-development workflow. It favors simplicity and traceability over heavy abstraction.

### 2. Scope

This document describes the design reflected in the current implementation. It focuses on:

- Runtime architecture
- Module responsibilities
- Agent workflow and tool integration
- Request and response flow
- Configuration and external dependencies
- Current limitations and implementation considerations

It does not define a future roadmap or deployment strategy in detail, although a few practical extension points are noted near the end.

### 3. System Overview

At a high level, the application works as follows:

1. A user enters a travel-planning prompt in the Streamlit UI.
2. The frontend sends the prompt to the FastAPI backend.
3. The backend creates a LangGraph workflow through `GraphBuilder`.
4. The workflow binds a chat model with domain-specific tools for weather, place search, budgeting, and currency conversion.
5. The model evaluates the request, calls tools when needed, and produces a final itinerary in Markdown-style text.
6. The backend saves the generated response to a timestamped Markdown file under `output/`.
7. The frontend displays both the execution trace and the final formatted answer.

The design intentionally keeps the backend stateless per request. Each incoming request builds and runs a fresh graph instance.

### 4. Design Goals

The implementation suggests the following working goals:

- Accept free-form travel requests without rigid input schemas
- Use external tools to enrich the model response with live or near-live information
- Provide a complete answer in one response rather than a multi-step interview flow
- Make execution observable through streamed trace events
- Save generated travel plans as standalone Markdown files

There are also a few implicit design choices:

- Prefer composition over inheritance for tools and services
- Keep domain utilities small and easy to reason about
- Keep the frontend thin and let the backend own orchestration

### 5. Architecture

#### 5.1 Backend API Layer

The backend lives in [`main.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/main.py). It exposes two endpoints:

- `POST /query`
- `POST /query/stream`

`/query` is the simpler synchronous interface. It runs the workflow and returns the final answer and saved file path.

`/query/stream` is the more user-facing endpoint. It creates an `ExecutionTracer`, runs the workflow in a background thread, and streams newline-delimited JSON events back to the client. This allows the UI to show progress updates while the agent is running.

The API layer is responsible for:

- Input validation through `QueryRequest`
- CORS setup
- Request rate limiting
- Prompt-injection screening for suspicious input patterns
- Running the orchestration entry point
- Returning either a final payload or a streamed event sequence
- Handling top-level exceptions

#### 5.2 Agent Orchestration Layer

The orchestration logic lives in [`agent/agentic_workflow.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/agent/agentic_workflow.py).

`GraphBuilder` is the central assembly point. It is responsible for:

- Loading the configured LLM
- Creating tool wrapper objects
- Collecting the callable tool list
- Binding tools to the model
- Building the LangGraph state machine

The graph is intentionally compact. It has two active nodes:

- `agent`
- `tools`

Execution starts at `agent`, conditionally routes to `tools` when the model emits tool calls, returns to `agent` after tool execution, and terminates at `END` when no more tool work is needed.

This is a standard ReAct-style loop implemented with LangGraph primitives.

#### 5.3 Tool Layer

The tool layer is split into lightweight wrappers under `tools/` and underlying service helpers under `utils/`.

This separation keeps the LangChain-facing interface small while isolating external API calls and calculation logic in plain Python classes.

The main tool groups are:

- Weather tools
- Place-discovery tools
- Expense calculation tools
- Currency conversion tools

Each group is initialized inside `GraphBuilder` and contributes one or more callable tools to the bound model.

The current implementation also places lightweight validation and sanitization in front of tool-backed search so untrusted retrieved content is less likely to influence model behavior as instructions.

#### 5.4 Frontend Layer

The frontend lives in [`streamlit_app.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/streamlit_app.py).

Its role is intentionally narrow:

- Render a simple request form
- Call the backend stream endpoint
- Show execution trace updates as they arrive
- Render the final itinerary in Markdown
- Surface the saved output file path to the user

The frontend does not run model logic locally. It acts as a client to the FastAPI service running on `http://localhost:8500`.

### 6. Request Lifecycle

#### 6.1 User Input

The user enters a free-form travel query in the Streamlit form. The form submits a payload of the shape:

```json
{
  "question": "Plan a trip to Goa for 5 days"
}
```

#### 6.2 API Handling

The backend receives the request and delegates work to `run_travel_agent()`.

That function:

- Creates a `GraphBuilder`
- Compiles the LangGraph workflow
- Generates a Mermaid-rendered graph image and writes it to `my_graph.png`
- Invokes the workflow with a `HumanMessage`
- Extracts the last model message from the returned state
- Persists the response to a Markdown file in `output/`

#### 6.3 Streaming Execution

For `/query/stream`, execution runs in a background thread. Progress is captured through `ExecutionTracer`, which emits timestamped events into a queue. A generator function consumes the queue and yields newline-delimited JSON events to the frontend.

This gives the UI two useful properties:

- The user sees that the system is actively working
- Tool-level execution can be surfaced without blocking the final response

#### 6.4 Final Output

The final backend payload currently contains:

- `answer`
- `saved_file`

The frontend then wraps the answer in presentation Markdown and renders it on screen.

### 7. Module Responsibilities

#### 7.1 `main.py`

Primary responsibilities:

- FastAPI app bootstrap
- Request schema definition
- CORS configuration
- Workflow invocation
- Streaming endpoint implementation

This file acts as the runtime entry point for backend execution.

#### 7.2 `agent/agentic_workflow.py`

Primary responsibilities:

- LLM loading through `ModelLoader`
- Tool initialization
- Tool binding
- Agent function definition
- LangGraph graph assembly and compilation

This module is the heart of the application.

#### 7.3 `prompt_library/prompt.py`

This module defines a single system prompt that frames the assistant as:

- A travel planner
- An expense planner
- A tool-using assistant that should provide a detailed, Markdown-formatted answer

The prompt strongly shapes response structure. It asks for two itinerary variants, practical recommendations, cost details, and weather context.

The prompt also now includes explicit security rules telling the model to treat user input, tool output, and retrieved search content as untrusted data rather than higher-priority instructions.

#### 7.4 `utils/model_loader.py`

This module abstracts model selection and config loading.

Its responsibilities are:

- Read provider choice
- Load YAML configuration
- Resolve environment-variable overrides
- Create the appropriate LangChain chat model object

The code currently supports:

- OpenAI via `ChatOpenAI`
- Groq via `ChatGroq`

#### 7.5 `tools/*.py`

Each file in `tools/` exposes LangChain-compatible tool functions through a small wrapper class. The wrappers also integrate with `ExecutionTracer`, which means tool activity can be surfaced to the frontend without polluting service classes with UI concerns.

This layer is intentionally thin:

- Input comes in as simple Python arguments
- The wrapper delegates to a utility/service object
- A human-readable string or numeric result is returned to the model

#### 7.6 `utils/*.py`

The `utils/` directory contains helper classes that perform direct work:

- Calling the OpenWeatherMap API
- Calling the ExchangeRate API
- Running Tavily searches
- Performing arithmetic calculations
- Saving final output to a Markdown file
- Loading configuration
- Capturing execution trace events

These classes are plain and easy to test in isolation.

Security-related helpers also live in `utils/`, including the in-memory rate limiter and prompt-injection guard utilities used by the API and search tools.

### 8. Agent Workflow Design

The workflow uses a compact ReAct-style loop:

1. The system prompt and user message are combined.
2. The bound LLM evaluates the current conversation state.
3. If the model wants to call a tool, `tools_condition` routes execution to the tool node.
4. The selected tool runs and returns its result into graph state.
5. Control returns to the model for another reasoning step.
6. The loop ends when the model produces a final answer with no further tool calls.

This design has a few advantages:

- The orchestration code stays small
- Tool use remains model-driven
- New capabilities can be added by registering additional tools
- The same graph can support both synchronous and streamed execution

The graph is not currently specialized by trip type, region, or user profile. All queries go through the same general-purpose planning loop.

### 9. Tooling Design

#### 9.1 Weather

Weather support is implemented through:

- [`tools/weather_info_tool.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/tools/weather_info_tool.py)
- [`utils/weather_info.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/utils/weather_info.py)

Two tools are exposed:

- `get_current_weather(city)`
- `get_weather_forecast(city)`

The helper uses the OpenWeatherMap REST API. Responses are normalized into short strings for the model.

One implementation detail is worth noting: current weather requests do not set metric units, while forecast requests do. As a result, the code labels current temperature as Celsius even though the API default is Kelvin. That is a correctness issue in the current implementation, not an architectural one.

#### 9.2 Place Search

Place lookup is implemented through:

- [`tools/place_search_tool.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/tools/place_search_tool.py)
- [`utils/place_info_search.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/utils/place_info_search.py)

Four tools are exposed:

- `search_attractions(place)`
- `search_restaurants(place)`
- `search_activities(place)`
- `search_transportation(place)`

Each tool performs a focused Tavily search and returns the answer field when available. This keeps prompt context compact while still letting the agent retrieve web-backed information.

The current implementation adds two safeguards here:

- Place arguments are validated before search is executed
- Tavily results are sanitized and returned with an explicit reminder that they are untrusted reference data only

#### 9.3 Expense Calculation

Expense support is implemented through:

- [`tools/expense_calculator_tool.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/tools/expense_calculator_tool.py)
- [`utils/expense_calculator.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/utils/expense_calculator.py)

Three tools are exposed:

- `estimate_total_hotel_cost(price_per_night, total_days)`
- `calculate_total_expense(*costs)`
- `calculate_daily_expense_budget(total_cost, days)`

These are intentionally simple arithmetic helpers. They make it easier for the model to offload repetitive numeric operations instead of calculating totals in free text.

#### 9.4 Currency Conversion

Currency conversion is implemented through:

- [`tools/currency_conversion_tool.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/tools/currency_conversion_tool.py)
- [`utils/currency_converter.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/utils/currency_converter.py)

One tool is exposed:

- `convert_currency(amount, from_currency, to_currency)`

The helper calls ExchangeRate API and multiplies the input amount by the target currency rate.

There is also an older arithmetic utility module in [`tools/arthematic_op_tool.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/tools/arthematic_op_tool.py), but it is not part of the active graph and appears to be legacy or exploratory code.

### 10. Persistence and Output Design

Generated itineraries are persisted through [`utils/save_to_document.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/utils/save_to_document.py).

The save flow is straightforward:

- Ensure the output directory exists
- Build a Markdown document with metadata and disclaimer
- Generate a timestamped filename
- Write the document to disk using UTF-8 encoding

This design provides a useful audit trail for generated plans and keeps output portable. A saved file can be reviewed independently of the UI.

The current implementation also saves a visual representation of the graph to `my_graph.png` each time a request is executed. This is helpful during development, though it is not required for serving responses.

### 11. Execution Trace Design

Tracing is handled by [`utils/execution_tracer.py`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/utils/execution_tracer.py).

The tracer records:

- Event type
- Message
- Timestamp
- Arbitrary structured details

It stores events locally and can optionally publish them to a queue. This makes it suitable for both:

- In-memory execution history
- Live event streaming to the frontend

The tracer is deliberately lightweight. It is not a full observability framework, but it gives enough visibility to understand graph progress, model invocation, and tool execution during interactive use.

The broader logging approach in the current codebase is intentionally selective. It logs request lifecycle events, model/provider initialization, output persistence, rate-limit rejections, and external-service failures, while avoiding full user prompt logging and avoiding secret values.

### 12. Configuration and Environment

The application relies on both YAML configuration and environment variables.

#### 12.1 YAML Configuration

Current model configuration lives in [`config/config.yaml`](/Users/ravinderkumar/Work/upskill/AI/AIAgent/ai_trip_planner/config/config.yaml).

At present, the file defines the default OpenAI model:

- `gpt-4.1-nano`

This gives the application a simple default while still allowing runtime overrides.

#### 12.2 Environment Variables

The implementation expects the following keys to exist when relevant:

- `OPENAI_API_KEY`
- `OPENAI_MODEL_NAME` optional override
- `GROQ_API_KEY`
- `GROQ_MODEL_NAME` optional override
- `OPENWEATHERMAP_API_KEY`
- `EXCHANGE_RATE_API_KEY`
- Tavily credentials through the environment expected by `langchain_tavily`

Environment values are loaded using `python-dotenv`.

### 13. External Dependencies

The current dependency set centers on:

- FastAPI for backend APIs
- Streamlit for UI
- LangChain and LangGraph for model orchestration
- OpenAI and Groq integrations for model providers
- Tavily for search-backed place discovery
- Requests and HTTPX for HTTP communication

This is a pragmatic stack for an agent-based prototype. The codebase stays mostly in plain Python while relying on LangGraph only where orchestration adds clear value.

### 14. Error Handling Strategy

Error handling is intentionally minimal in the current implementation.

Observed patterns:

- Top-level API handlers catch exceptions and return a 500 response or error event
- Tool helpers usually return empty results on non-200 API responses
- Some utility methods raise raw exceptions directly

This keeps the code simple but creates uneven failure behavior across tools. For example:

- A weather failure may degrade to an empty response
- A currency conversion failure may raise and bubble up

From a design standpoint, this means the current system is functional for development, but not yet hardened for production-grade resilience.

That said, the implementation now includes a first security-focused hardening pass:

- Generic client-safe error messages at the API layer
- Logging of server-side exceptions without returning internals to the caller
- Timeouts on outbound weather and currency API calls
- Rate limiting for `/query` and `/query/stream`
- Prompt-injection pattern checks for inbound requests
- Input validation for place-search tool arguments

### 15. Current Limitations

The current implementation is usable, but a few constraints are visible in the code:

- The frontend is hardcoded to `http://localhost:8500`
- The backend builds a fresh graph on every request
- Tool outputs are returned as plain strings, which limits downstream structure
- The saved output format is presentation-first rather than schema-first
- Weather units are inconsistent between current and forecast calls
- Some files suggest prototype-stage code quality, including unused imports and a legacy arithmetic tool module
- There is no persistent conversation state or user profile
- There is no caching layer for repeated searches or API calls
- There are no automated tests in the current repository

These are not design failures so much as reasonable tradeoffs for an early implementation.

### 16. Security and Operational Notes

The application is designed for trusted local or controlled use. A few operational details matter:

- CORS is restricted to configured origins
- Secrets are expected through environment variables
- Output files are written directly to the local filesystem
- There is no authentication on the API layer

The current implementation includes the following defensive controls:

- Request validation with bounded question length
- In-memory per-client rate limiting
- Environment-configurable CORS allowlist
- Timeout-based handling for outbound HTTP calls
- Prompt-injection screening at the API boundary
- Sanitization of Tavily search content before it re-enters model context
- Targeted warning and exception logging for abuse or upstream failures

This is acceptable for development and demo usage, but it would need tightening before public deployment.

### 17. Extension Points

The current design leaves several clean extension points:

- Add more tools by following the existing wrapper-plus-service pattern
- Add more model providers in `ModelLoader`
- Introduce structured tool responses if downstream formatting needs to become more deterministic
- Replace local file persistence with object storage or a database
- Add richer trace events without changing the API contract
- Support itinerary refinement by carrying conversation state between requests

Because the orchestration layer is isolated in `GraphBuilder`, most feature growth can happen without disturbing the API and frontend layers.

### 18. Summary

The AI Trip Planner is designed as a small but coherent agent application. FastAPI handles transport, LangGraph handles reasoning and tool orchestration, utility services integrate with external data sources, and Streamlit provides an approachable interface for interactive use.

The design is intentionally direct. It does not over-engineer the problem. The codebase is organized around a clear flow from user request to agent execution to persisted output. That makes it a solid foundation for iteration, especially if the next steps are to improve reliability, clean up a few implementation details, and add tests around tool behavior and response generation.
