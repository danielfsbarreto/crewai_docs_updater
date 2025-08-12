from typing import Union

from pydantic import BaseModel, Field


class File(BaseModel):
    path: str
    content: Union[str, None] = None
    chunks: list[str] = Field(default_factory=list)
    translation_path: Union[str, None] = None
    translation_content: Union[str, None] = None
    translated_chunks: list[str] = Field(default_factory=list)


class CrewDocsUpdaterState(BaseModel):
    repo: str = "crewAIInc/crewAI"
    docs_path: str = "docs"
    primary_language: str = "en"
    secondary_language: str = "ko"
    files: list[File] = Field(default_factory=list)
