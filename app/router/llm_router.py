# app.py
from fastapi import FastAPI, APIRouter
from typing import Optional

from langchain_core.messages import AIMessage

# Import your modules from app.service
from app.service.chains import (
    generate_outline_direct,
    expand_chain,
    gen_perspectives_chain,
    generate_question,
    gen_answer,
    interview_graph,
    run_interview_graph,
    refine_outline_chain,
    section_writer,
    writer,
)
from app.service.models import (
    Outline,
    Perspectives,
    Editor,
    InterviewState,
    AnswerWithCitations,
    Subsection,
    Section,
    WikiSection,
)
from app.service.utils import format_docs, swap_roles
from app.service.workflow import run_storm

# Define your APIRouter with the prefix
__prefix = "/llm"
router = APIRouter(prefix=__prefix)

# In-memory storage (Replace with a database in production)
stored_outlines = {}
stored_perspectives = {}
stored_interviews = {}
stored_refined_outlines = {}
stored_sections = {}

@router.post("/generate_outline")
async def generate_outline(topic: str):
    initial_outline = await generate_outline_direct.ainvoke({"topic": topic})
    stored_outlines[topic] = initial_outline
    return initial_outline.dict()

