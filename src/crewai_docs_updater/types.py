from typing import Any

from pydantic import BaseModel, Field


class File(BaseModel):
    path: str
    content: str
    chunks: list[Any] = Field(default_factory=list)
    translated_chunks: list[Any] = Field(default_factory=list)


class CrewDocsUpdaterState(BaseModel):
    repo: str = "crewAIInc/crewAI"
    primary_language: str = "en"
    secondary_languages: list[str] = ["pt-BR"]
    files_outdated: list[File] = Field(default_factory=list)
