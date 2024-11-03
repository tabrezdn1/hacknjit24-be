# utils.py
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.retrievers import WikipediaRetriever

wikipedia_retriever = WikipediaRetriever(load_all_available_meta=True, top_k_results=1)
# app/service/utils.py

def format_conversation(interview_state):
    messages = interview_state["messages"]
    convo = "\n".join(f"{m.name}: {m.content}" for m in messages)
    return f'Conversation with {interview_state["editor"].name}\n\n' + convo

def format_doc(doc, max_length=1000):
    related = "- ".join(doc.metadata.get("categories", []))
    return f"### {doc.metadata.get('title', '')}\n\nSummary: {doc.page_content}\n\nRelated\n{related}"[:max_length]

def format_docs(docs):
    return "\n\n".join(format_doc(doc) for doc in docs)

def tag_with_name(ai_message: AIMessage, name: str):
    ai_message.name = name
    return ai_message

def swap_roles(state, name: str):
    converted = []
    for message in state["messages"]:
        if isinstance(message, AIMessage) and message.name != name:
            message = HumanMessage(**message.dict(exclude={"type"}))
        converted.append(message)
    state["messages"] = converted
    return state

def update_references(references, new_references):
    if not references:
        references = {}
    references.update(new_references)
    return references

def add_messages(left, right):
    if not isinstance(left, list):
        left = [left]
    if not isinstance(right, list):
        right = [right]
    return left + right


def update_references(references, new_references):
    if not references:
        references = {}
    references.update(new_references)
    return references


def update_editor(editor, new_editor):
    # Can only set at the outset
    if not editor:
        return new_editor
    return editor