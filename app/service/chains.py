# chains.py
import os
from getpass import getpass

from langchain_community.tools import TavilySearchResults
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda, chain as as_runnable, RunnableConfig
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_community.utilities.duckduckgo_search import DuckDuckGoSearchAPIWrapper
from langchain_core.tools import tool
from typing import Optional
import json

from app.service.prompts import (
    direct_gen_outline_prompt,
    gen_related_topics_prompt,
    gen_perspectives_prompt,
    gen_qn_prompt,
    gen_queries_prompt,
    gen_answer_prompt,
    refine_outline_prompt,
    section_writer_prompt,
    writer_prompt,
)
from app.service.models import (
    Outline,
    RelatedSubjects,
    Perspectives,
    Editor,
    InterviewState,
    Queries,
    AnswerWithCitations,
    WikiSection,
)
from app.service.utils import format_docs, tag_with_name, swap_roles, update_references, wikipedia_retriever

# app/service/chains.py
from langchain_openai import ChatOpenAI

from setting import get_config

settings=get_config()
fast_llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.OPENAI_API_KEY)
long_context_llm = ChatOpenAI(model="gpt-4o", api_key=settings.OPENAI_API_KEY)


generate_outline_direct = direct_gen_outline_prompt | fast_llm.with_structured_output(
    Outline
)

expand_chain = gen_related_topics_prompt | fast_llm.with_structured_output(
    RelatedSubjects
)

gen_perspectives_chain = gen_perspectives_prompt | ChatOpenAI(
    model="gpt-3.5-turbo", api_key=settings.OPENAI_API_KEY
).with_structured_output(Perspectives)
os.environ["TAVILY_API_KEY"] = settings.TAVILY_API_KEY
search_engine = TavilySearchResults(max_results=4,api_key=settings.TAVILY_API_KEY)

@tool
async def search_engine(query: str):
    """Search engine to the internet."""
    results = search_engine.invoke(query)
    return [{"content": r["content"], "url": r["url"]} for r in results]

gen_queries_chain = gen_queries_prompt | ChatOpenAI(
    model="gpt-3.5-turbo", api_key=settings.OPENAI_API_KEY
).with_structured_output(Queries, include_raw=True)

gen_answer_chain = gen_answer_prompt | fast_llm.with_structured_output(
    AnswerWithCitations, include_raw=True
).with_config(run_name="GenerateAnswer")

@as_runnable
async def generate_question(state: InterviewState):
    editor = state["editor"]
    gn_chain = (
        RunnableLambda(swap_roles).bind(name=editor.name)
        | gen_qn_prompt.partial(persona=editor.persona)
        | fast_llm
        | RunnableLambda(tag_with_name).bind(name=editor.name)
    )
    result = await gn_chain.ainvoke(state)
    return {"messages": [result]}



async def gen_answer(
    state: InterviewState,
    config: Optional[RunnableConfig] = None,
    name: str = "Subject_Matter_Expert",
    max_str_len: int = 15000,
):
    swapped_state = swap_roles(state, name)  # Convert all other AI messages
    queries = await gen_queries_chain.ainvoke(swapped_state)
    query_results = await search_engine.abatch(
        queries["parsed"].queries, config, return_exceptions=True
    )
    successful_results = [
        res for res in query_results if not isinstance(res, Exception)
    ]
    all_query_results = {
        res["url"]: res["content"] for results in successful_results for res in results
    }
    # We could be more precise about handling max token length if we wanted to here
    dumped = json.dumps(all_query_results)[:max_str_len]
    ai_message: AIMessage = queries["raw"]
    tool_call = queries["raw"].tool_calls[0]
    tool_id = tool_call["id"]
    tool_message = ToolMessage(tool_call_id=tool_id, content=dumped)
    swapped_state["messages"].extend([ai_message, tool_message])
    # Only update the shared state with the final answer to avoid
    # polluting the dialogue history with intermediate messages
    generated = await gen_answer_chain.ainvoke(swapped_state)
    cited_urls = set(generated["parsed"].cited_urls)
    # Save the retrieved information to a the shared state for future reference
    cited_references = {k: v for k, v in all_query_results.items() if k in cited_urls}
    formatted_message = AIMessage(name=name, content=generated["parsed"].as_str)
    return {"messages": [formatted_message], "references": cited_references}

# Implement the graph logic
from langgraph.graph import END, StateGraph, START
from langgraph.pregel import RetryPolicy

def route_messages(state: InterviewState, name: str = "Subject_Matter_Expert"):
    messages = state["messages"]
    num_responses = len(
        [m for m in messages if isinstance(m, AIMessage) and m.name == name]
    )
    max_num_turns = 5  # Adjust as needed
    if num_responses >= max_num_turns:
        return END
    last_question = messages[-2]
    if last_question.content.strip().endswith("Thank you so much for your help!"):
        return END
    return "ask_question"

builder = StateGraph(InterviewState)

builder.add_node("ask_question", generate_question, retry=RetryPolicy(max_attempts=5))
builder.add_node("answer_question", gen_answer, retry=RetryPolicy(max_attempts=5))
builder.add_conditional_edges("answer_question", route_messages)
builder.add_edge("ask_question", "answer_question")

builder.add_edge(START, "ask_question")
interview_graph = builder.compile(checkpointer=False).with_config(
    run_name="Conduct Interviews"
)

# Function to run the interview graph
async def run_interview_graph(initial_state: InterviewState):
    final_state = initial_state
    async for step in interview_graph.astream(initial_state):
        final_state = next(iter(step.values()))
    return final_state
@as_runnable
async def survey_subjects(topic: str):
    related_subjects = await expand_chain.ainvoke({"topic": topic})
    retrieved_docs = await wikipedia_retriever.abatch(
        related_subjects.topics, return_exceptions=True
    )
    all_docs = []
    for docs in retrieved_docs:
        if isinstance(docs, Exception):
            continue
        all_docs.extend(docs)
    formatted = format_docs(all_docs)
    perspectives = await gen_perspectives_chain.ainvoke({"examples": formatted, "topic": topic})
    return perspectives
# Define the refine_outline_chain
refine_outline_chain = refine_outline_prompt | long_context_llm.with_structured_output(
    Outline
)

# Define section_writer chain
section_writer = (
    section_writer_prompt
    | long_context_llm.with_structured_output(WikiSection)
)

# Define writer chain
writer = writer_prompt | long_context_llm | StrOutputParser()
