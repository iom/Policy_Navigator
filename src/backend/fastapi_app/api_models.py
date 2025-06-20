from enum import Enum
from typing import Any, Optional

from openai.types.responses import ResponseInputItemParam
from pydantic import BaseModel, Field


class AIChatRoles(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    content: str
    role: AIChatRoles = AIChatRoles.USER


class RetrievalMode(str, Enum):
    TEXT = "text"
    VECTORS = "vectors"
    HYBRID = "hybrid"


class ChatRequestOverrides(BaseModel):
    top: int = 3
    temperature: float = 0.3
    retrieval_mode: RetrievalMode = RetrievalMode.HYBRID
    use_advanced_flow: bool = True
    prompt_template: Optional[str] = None
    seed: Optional[int] = None


class ChatRequestContext(BaseModel):
    overrides: ChatRequestOverrides


class ChatRequest(BaseModel):
    messages: list[ResponseInputItemParam]
    context: ChatRequestContext
    sessionState: Optional[Any] = None


class ItemPublic(BaseModel):
    id: int
    filename: str
    fileurl: str
    pagenumber: int
    chunk: int
    content: str
    typedoc: str

    def to_str_for_rag(self):
        return (
            f"Filename: {self.filename} | "
            f"File URL: {self.fileurl} | "
            f"Page Number: {self.pagenumber} | "
            f"Chunk: {self.chunk} | "
            f"Document Type: {self.typedoc} | "
            f"Content: {self.content}"
        )

class ItemWithDistance(ItemPublic):
    distance: float

    def __init__(self, **data):
        super().__init__(**data)
        self.distance = round(self.distance, 2)


class ThoughtStep(BaseModel):
    title: str
    description: Any
    props: dict = {}


class RAGContext(BaseModel):
    data_points: dict[int, ItemPublic]
    thoughts: list[ThoughtStep]
    followup_questions: Optional[list[str]] = None


class ErrorResponse(BaseModel):
    error: str

class ImpactValue(BaseModel):
    value: float

class Impacts(BaseModel):
    energy: Optional[ImpactValue] = None
    gwp: Optional[ImpactValue] = None


class RetrievalResponse(BaseModel):
    message: Message
    context: RAGContext
    sessionState: Optional[Any] = None    
    impacts: Optional[Impacts] = None


class RetrievalResponseDelta(BaseModel):
    delta: Optional[Message] = None
    context: Optional[RAGContext] = None
    sessionState: Optional[Any] = None


class ChatParams(ChatRequestOverrides):
    prompt_template: str
    response_token_limit: int = 1024
    enable_text_search: bool
    enable_vector_search: bool
    original_user_query: str
    past_messages: list[ResponseInputItemParam]


class Filter(BaseModel):
    column: str
    comparison_operator: str
    value: Any



class SearchResults(BaseModel):
    query: str
    """The original search query"""

    items: list[ItemPublic]
    """List of items that match the search query and filters"""

    filters: list[Filter]
    """List of filters applied to the search results"""
