import logging
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.tools import retrieve_tool, summarize_tool
from app.agent.prompts import SYSTEM_PROMPT, RETRIEVAL_PROMPT, SUMMARIZE_PROMPT
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


# ── State ──────────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    query: str
    intent: Literal["retrieve", "summarize", "unknown"]
    retrieval_result: dict
    summarize_result: dict
    answer: str
    citations: list[dict]
    grounded: bool


# ── LLM singleton ──────────────────────────────────────────────────────────────

def get_llm() -> ChatOllama:
    return ChatOllama(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
        temperature=0.1,        # Low temp for factual grounded answers
        num_predict=1024,
    )


# ── Nodes ──────────────────────────────────────────────────────────────────────

async def classify_intent(state: AgentState) -> AgentState:
    """
    Node 1: Decide if the query needs retrieval or summarization.
    Simple keyword-based classification — avoids an extra LLM call.
    """
    query_lower = state["query"].lower()
    summarize_keywords = [
        "summarize", "summary", "overview", "what is this document about",
        "what does this document cover", "give me an overview"
    ]

    if any(kw in query_lower for kw in summarize_keywords):
        intent = "summarize"
    else:
        intent = "retrieve"

    logger.info(f"Intent classified: {intent}")
    return {**state, "intent": intent}


async def run_retrieve(state: AgentState) -> AgentState:
    """
    Node 2a: Run the hybrid retrieval pipeline.
    """
    result = await retrieve_tool(state["query"])
    return {**state, "retrieval_result": result, "grounded": result.get("grounded", False)}


async def run_summarize(state: AgentState) -> AgentState:
    """
    Node 2b: Fetch document content for summarization.
    """
    result = await summarize_tool()
    return {**state, "summarize_result": result, "grounded": True}


async def generate_answer(state: AgentState) -> AgentState:
    """
    Node 3: Generate the final answer using the LLM.
    Handles three cases:
    - Not grounded → explicit refusal (no LLM call needed)
    - Retrieval → answer from contexts
    - Summarize → summary of document(s)
    """
    llm = get_llm()

    # ── Case 1: Not grounded → refuse without calling LLM ──
    if not state.get("grounded", False):
        return {
            **state,
            "answer": "I cannot answer this from the provided documents.",
            "citations": [],
        }

    # ── Case 2: Summarization ──
    if state["intent"] == "summarize":
        content_blocks = state["summarize_result"].get("content", [])
        if not content_blocks:
            return {
                **state,
                "answer": "No documents are available to summarize.",
                "citations": [],
            }

        # Construit un prompt unique avec tous les documents
        all_content = "\n\n---\n\n".join(
            f"Document: {block['filename']}\n{block['content']}"                for block in content_blocks
        )

        prompt = SUMMARIZE_PROMPT.format(
            filename=", ".join(b["filename"] for b in content_blocks),
            content=all_content,
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]

        response = await llm.ainvoke(messages)

        # Une citation par document unique — dédupliquées
        seen = set()
        citations = []
        for block in content_blocks:
            if block["filename"] not in seen:
                seen.add(block["filename"])
                citations.append({
                    "filename": block["filename"],
                    "document_id": block["document_id"],
                    "page_number": None,
                })

        return {
            **state,
            "answer": response.content,
            "citations": citations,
        }


    # ── Case 3: Retrieval-based answer ──
    contexts = state["retrieval_result"].get("contexts", [])
    if not contexts:
        return {
            **state,
            "answer": "I cannot answer this from the provided documents.",
            "citations": [],
        }

    # Format contexts for the prompt
    formatted_contexts = "\n\n---\n\n".join(
        f"[Source: {c['filename']}, Page {c['page_number']}]\n{c['parent_content']}"
        for c in contexts
    )

    prompt = RETRIEVAL_PROMPT.format(
        query=state["query"],
        contexts=formatted_contexts,
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]

    response = await llm.ainvoke(messages)

    # Build citations from contexts used
    citations = [
        {
            "filename": c["filename"],
            "page_number": c["page_number"],
            "rerank_score": round(c["rerank_score"], 4),
            "excerpt": c["child_content"][:150],
        }
        for c in contexts
    ]

    return {
        **state,
        "answer": response.content,
        "citations": citations,
    }


# ── Routing ────────────────────────────────────────────────────────────────────

def route_intent(state: AgentState) -> Literal["run_retrieve", "run_summarize"]:
    return "run_retrieve" if state["intent"] == "retrieve" else "run_summarize"


# ── Graph assembly ─────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("classify_intent", classify_intent)
    graph.add_node("run_retrieve", run_retrieve)
    graph.add_node("run_summarize", run_summarize)
    graph.add_node("generate_answer", generate_answer)

    graph.set_entry_point("classify_intent")

    graph.add_conditional_edges(
        "classify_intent",
        route_intent,
        {
            "run_retrieve": "run_retrieve",
            "run_summarize": "run_summarize",
        },
    )

    graph.add_edge("run_retrieve", "generate_answer")
    graph.add_edge("run_summarize", "generate_answer")
    graph.add_edge("generate_answer", END)

    return graph.compile()


# Module-level compiled graph
agent_graph = build_graph()