# models.py
from typing import List, Optional
from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypedDict
from langchain_core.messages import AnyMessage
from enum import Enum

class Subsection(BaseModel):
    subsection_title: str = Field(..., title="Title of the subsection")
    description: str = Field(..., title="Content of the subsection")

    @property
    def as_str(self) -> str:
        return f"### {self.subsection_title}\n\n{self.description}".strip()


from typing import List, Optional
from pydantic import BaseModel, Field


class Strategy(BaseModel):
    name: str = Field(..., title="Name of the strategy or technique to use")
    description: str = Field(..., title="Clear instructions on how to implement the strategy")
    when_to_use: str = Field(..., title="Situations or times when this strategy should be applied")

    @property
    def as_str(self) -> str:
        return f"### {self.name}\n{self.description}\nWhen to use: {self.when_to_use}"


class Section(BaseModel):
    title: str = Field(..., title="Main focus area of this section")
    description: str = Field(..., title="Brief overview of this section's purpose")
    strategies: List[Strategy] = Field(
        default_factory=list,
        title="Practical strategies and techniques for this focus area",
    )

    @property
    def as_str(self) -> str:
        strategies_text = "\n\n".join(strategy.as_str for strategy in self.strategies)
        return f"# {self.title}\n{self.description}\n\n{strategies_text}".strip()


class Outline(BaseModel):
    page_title: str = Field(..., title="Title of the Mental Health Plan")
    sections: List[Section] = Field(
        default_factory=list,
        title="Different areas of focus in the plan",
    )

    @property
    def as_str(self) -> str:
        header = f"# {self.page_title}\n\n"
        sections = "\n\n".join(section.as_str for section in self.sections)
        return f"{header}{sections}".strip()


class RelatedSubjects(BaseModel):
    topics: List[str] = Field(
        description="Comprehensive list of related subjects as background research.",
    )

class Editor(BaseModel):
    affiliation: str = Field(
        description="Primary affiliation of the editor.",
    )
    name: str = Field(
        description="Name of the editor.", pattern=r"^[a-zA-Z0-9_-]{1,64}$"
    )
    role: str = Field(
        description="Role of the editor in the context of the topic.",
    )
    description: str = Field(
        description="Description of the editor's focus, concerns, and motives.",
    )

    @property
    def persona(self) -> str:
        return f"Name: {self.name}\nRole: {self.role}\nAffiliation: {self.affiliation}\nDescription: {self.description}\n"

class Perspectives(BaseModel):
    editors: List[Editor] = Field(
        description="Comprehensive list of editors with their roles and affiliations.",
    )

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

class InterviewState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    references: Annotated[Optional[dict], update_references]
    editor: Annotated[Optional[Editor], update_editor]

class Queries(BaseModel):
    queries: List[str] = Field(
        description="Comprehensive list of search engine queries to answer the user's questions.",
    )

class AnswerWithCitations(BaseModel):
    answer: str = Field(
        description="Comprehensive answer to the user's question with citations.",
    )
    cited_urls: List[str] = Field(
        description="List of urls cited in the answer.",
    )

    @property
    def as_str(self) -> str:
        citations = "\n".join(
            f"[{i+1}]: {url}" for i, url in enumerate(self.cited_urls)
        )
        return f"{self.answer}\n\nCitations:\n\n{citations}"

class SubSection(BaseModel):
    subsection_title: str = Field(..., title="Title of the subsection")
    content: str = Field(
        ...,
        title="Full content of the subsection. Include [#] citations to the cited sources where relevant.",
    )

    @property
    def as_str(self) -> str:
        return f"### {self.subsection_title}\n\n{self.content}".strip()

class WikiSection(BaseModel):
    section_title: str = Field(..., title="Title of the section")
    content: str = Field(..., title="Full content of the section")
    subsections: Optional[List[SubSection]] = Field(
        default=None,
        title="Titles and descriptions for each subsection of the Wikipedia page.",
    )
    citations: List[str] = Field(default_factory=list)

    @property
    def as_str(self) -> str:
        subsections = "\n\n".join(
            subsection.as_str for subsection in self.subsections or []
        )
        citations = "\n".join([f" [{i}] {cit}" for i, cit in enumerate(self.citations)])
        return (
            f"## {self.section_title}\n\n{self.content}\n\n{subsections}".strip()
            + f"\n\n{citations}".strip()
        )
