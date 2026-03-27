from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent.agentic_workflow import GraphBuilder
from utils.save_to_document import save_document
from utils.execution_tracer import ExecutionTracer
from starlette.responses import JSONResponse
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
import os
import datetime
import json
import threading
from dotenv import load_dotenv
from pydantic import BaseModel
from queue import Queue
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # set specific origins in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class QueryRequest(BaseModel):
    question: str


def run_travel_agent(question: str, tracer: ExecutionTracer | None = None):
    if tracer:
        tracer.log("status", "Preparing graph")
    graph = GraphBuilder(model_provider="openai", tracer=tracer)
    react_app = graph()

    png_graph = react_app.get_graph().draw_mermaid_png()
    with open("my_graph.png", "wb") as f:
        f.write(png_graph)

    if tracer:
        tracer.log("status", "Graph compiled and diagram saved", graph_path=os.path.join(os.getcwd(), "my_graph.png"))

    messages = {"messages": [HumanMessage(content=question)]}
    if tracer:
        tracer.log("status", "Invoking workflow", question=question)
    output = react_app.invoke(messages)

    if isinstance(output, dict) and "messages" in output:
        final_output = output["messages"][-1].content
    else:
        final_output = str(output)

    saved_file = save_document(final_output)
    if tracer:
        tracer.log("status", "Saved generated itinerary", saved_file=saved_file)

    return {"answer": final_output, "saved_file": saved_file}

@app.post("/query")
async def query_travel_agent(query:QueryRequest):
    try:
        print(query)
        return run_travel_agent(query.question)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/query/stream")
async def query_travel_agent_stream(query: QueryRequest):
    event_queue: Queue = Queue()
    tracer = ExecutionTracer(event_queue=event_queue)

    def worker():
        try:
            result = run_travel_agent(query.question, tracer=tracer)
            event_queue.put({"type": "final", "timestamp": "", "message": "Workflow completed", "details": result})
        except Exception as exc:
            event_queue.put({"type": "error", "timestamp": "", "message": str(exc), "details": {}})
        finally:
            event_queue.put(None)

    threading.Thread(target=worker, daemon=True).start()

    def event_stream():
        while True:
            event = event_queue.get()
            if event is None:
                break
            yield json.dumps(event) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")
