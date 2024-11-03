# app/service/workflow.py

import asyncio
from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_core.documents import Document
from langchain_community.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langgraph.graph import StateGraph, START, END
from langgraph.pregel import RetryPolicy
from langgraph.checkpoint.memory import MemorySaver

# Import your chains and utilities
from app.service.chains import (
    generate_outline_direct,
    survey_subjects,
    interview_graph,
    refine_outline_chain,
    section_writer,
    writer,
)
from app.service.utils import format_conversation
from app.setting import get_config

settings=get_config()
# Initialize embeddings and vector store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small",api_key=settings.OPENAI_API_KEY)
vectorstore = InMemoryVectorStore(embedding=embeddings)

async def initialize_research(state: Dict[str, Any]):
    topic = state["topic"]
    coros = (
        generate_outline_direct.ainvoke({"topic": topic}),
        survey_subjects.ainvoke(topic),
    )
    results = await asyncio.gather(*coros)
    return {
        **state,
        "outline": results[0],
        "editors": results[1].editors,
    }

async def conduct_interviews(state: Dict[str, Any]):
    topic = state["topic"]
    initial_states = [
        {
            "editor": editor,
            "messages": [
                AIMessage(
                    content=f"So you said you were writing an article on {topic}?",
                    name="Subject_Matter_Expert",
                )
            ],
        }
        for editor in state["editors"]
    ]
    # Parallelize the interviews
    interview_results = await interview_graph.abatch(initial_states)
    return {
        **state,
        "interview_results": interview_results,
    }

async def refine_outline(state: Dict[str, Any]):
    convos = "\n\n".join(
        [
            format_conversation(interview_state)
            for interview_state in state["interview_results"]
        ]
    )
    updated_outline = await refine_outline_chain.ainvoke(
        {
            "topic": state["topic"],
            "old_outline": state["outline"].as_str,
            "conversations": convos,
        }
    )
    return {**state, "outline": updated_outline}

async def index_references(state: Dict[str, Any]):
    all_docs = []
    for interview_state in state["interview_results"]:
        reference_docs = [
            Document(page_content=v, metadata={"source": k})
            for k, v in interview_state.get("references", {}).items()
        ]
        all_docs.extend(reference_docs)
    await vectorstore.aadd_documents(all_docs)
    return state

async def write_sections(state: Dict[str, Any]):
    outline = state["outline"]
    sections = await section_writer.abatch(
        [
            {
                "outline": state["outline"].as_str,
                "section": section.section_title,
                "topic": state["topic"],
            }
            for section in outline.sections
        ]
    )
    return {
        **state,
        "sections": sections,
    }

async def write_article(state: Dict[str, Any]):
    topic = state["topic"]
    sections = state["sections"]
    draft = "\n\n".join([section.as_str for section in sections])
    article = await writer.ainvoke({"topic": topic, "draft": draft})
    return {
        **state,
        "article": article,
    }

def build_storm_graph():
    builder = StateGraph(Dict[str, Any])
    nodes = [
        ("init_research", initialize_research),
        ("conduct_interviews", conduct_interviews),
        ("refine_outline", refine_outline),
        ("index_references", index_references),
        ("write_sections", write_sections),
        ("write_article", write_article),
    ]
    for i in range(len(nodes)):
        name, node = nodes[i]
        builder.add_node(name, node, retry=RetryPolicy(max_attempts=3))
        if i > 0:
            builder.add_edge(nodes[i - 1][0], name)
    builder.add_edge(START, nodes[0][0])
    builder.add_edge(nodes[-1][0], END)
    storm = builder.compile(checkpointer=MemorySaver())
    return storm

async def run_storm(topic: str):
    storm = build_storm_graph()
    config = {"configurable": {"thread_id": "user_thread"}}
    async for step in storm.astream({"topic": topic}, config):
        name = next(iter(step))
        print(f"Step: {name}")
        print(f"-- {str(step[name])[:300]}")
    checkpoint = storm.get_state(config)
    article = checkpoint.values["article"]
    return article
