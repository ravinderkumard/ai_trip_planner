import logging
import os

from langchain_core.messages import HumanMessage

from agent.agentic_workflow import GraphBuilder
from utils.execution_tracer import ExecutionTracer
from utils.save_to_document import save_document

logger = logging.getLogger(__name__)


def build_travel_query(input_data: dict | str) -> str:
    if isinstance(input_data, str):
        query = input_data.strip()
        if not query:
            raise ValueError("Travel query must not be empty.")
        return query

    if not isinstance(input_data, dict):
        raise ValueError("Travel input must be a string or dictionary.")

    raw_query = str(input_data.get("query", "")).strip()
    if raw_query:
        return raw_query

    destination = str(input_data.get("destination", "")).strip()
    duration_days = input_data.get("duration_days")
    budget_inr = input_data.get("budget_inr")

    if not destination:
        raise ValueError("Travel input must include a destination or query.")

    query_parts = [f"Plan a trip to {destination}"]

    if duration_days is not None:
        try:
            duration_days = int(duration_days)
        except (TypeError, ValueError) as exc:
            raise ValueError("duration_days must be a valid integer.") from exc
        if duration_days <= 0:
            raise ValueError("duration_days must be greater than zero.")
        query_parts.append(f"for {duration_days} days")

    if budget_inr is not None:
        try:
            budget_value = float(budget_inr)
        except (TypeError, ValueError) as exc:
            raise ValueError("budget_inr must be numeric.") from exc
        if budget_value <= 0:
            raise ValueError("budget_inr must be greater than zero.")
        budget_display = int(budget_value) if budget_value.is_integer() else budget_value
        query_parts.append(f"within a budget of INR {budget_display}")

    return " ".join(query_parts) + "."


def run_travel_agent(question: str, tracer: ExecutionTracer | None = None):
    logger.info("Starting travel agent run question_length=%s", len(question))
    if tracer:
        tracer.log("status", "Preparing graph")
    graph = GraphBuilder(model_provider="openai", tracer=tracer)
    react_app = graph()

    png_graph = react_app.get_graph().draw_mermaid_png()
    with open("my_graph.png", "wb") as f:
        f.write(png_graph)

    if tracer:
        tracer.log(
            "status",
            "Graph compiled and diagram saved",
            graph_path=os.path.join(os.getcwd(), "my_graph.png"),
        )

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
        token_usage = tracer.get_token_usage()
        tracer.log("usage", "Completed workflow token usage", **token_usage)
    else:
        token_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    logger.info("Travel agent run completed saved_file=%s", bool(saved_file))

    return {"answer": final_output, "saved_file": saved_file, "token_usage": token_usage}
