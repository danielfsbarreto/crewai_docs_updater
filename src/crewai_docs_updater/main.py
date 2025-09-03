#!/usr/bin/env python
import os
from datetime import datetime

from crewai.flow import Flow, and_, listen, start

from crewai_docs_updater.services import FileTranslationService
from crewai_docs_updater.types import CrewDocsUpdaterState


class CrewDocsUpdaterFlow(Flow[CrewDocsUpdaterState]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.translation_service = FileTranslationService()

    @start()
    def list_files_to_translate(self):
        self.state.files = self.translation_service.get_files(
            self.state.docs_path,
            self.state.primary_language,
            self.state.files,
        )

    @listen(list_files_to_translate)
    async def chunk_files(self):
        self.state.files = await self.translation_service.chunk_files()

    @listen(chunk_files)
    async def determine_files_translation_path(self):
        self.state.files = (
            await self.translation_service.determine_files_translation_path(
                from_language=self.state.primary_language,
                to_language=self.state.secondary_language,
            )
        )

    @listen(chunk_files)
    async def translate_files(self):
        self.state.files = await self.translation_service.translate_files(
            from_language=self.state.primary_language,
            to_language=self.state.secondary_language,
        )

    @listen(and_(determine_files_translation_path, translate_files))
    def save_file(self):
        print("Saving files")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for file in self.state.files:
            output_path = f"tmp/{timestamp}/{file.translation_path}"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w") as f:
                f.write(file.translation_content)
            print(f"Saved: {output_path}")


def kickoff():
    """
    How to Pass Down Specific Files for Translation
    -----------------------------------------------

    By default, the CrewDocsUpdaterFlow will process all files found in the documentation path (`docs_path`) for translation.
    However, you can specify a subset of files to process by passing a list of `File` objects to the flow's `kickoff` method.

    Example:

        from crewai_docs_updater.types import File

        CrewDocsUpdaterFlow().kickoff(
            inputs={
                "files": [
                    File(path="docs/en/guides/flows/first-flow.mdx"),
                    File(path="docs/en/another-guide.mdx"),
                ]
            }
        )

    This will restrict the translation process to only the files you specify.
    Each `File` object should have at least the `path` attribute set to the relative path of the file you want to process.

    If you do not provide the `files` input, the flow will automatically discover all files in the `docs_path` directory.

    """
    CrewDocsUpdaterFlow().kickoff()


def plot():
    CrewDocsUpdaterFlow().plot()


if __name__ == "__main__":
    kickoff()
