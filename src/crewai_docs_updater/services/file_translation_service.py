import asyncio
from time import sleep

from crewai_docs_updater.agents import translator_agent
from crewai_docs_updater.clients import GithubClient
from crewai_docs_updater.types import File
from crewai_docs_updater.utils import MdxChunker


class FileTranslationService:
    def __init__(self):
        self._files = []
        self._github_client = GithubClient()

    def get_files(self, docs_path: str, primary_language: str) -> list[File]:
        self._files = self._github_client.get_files(f"{docs_path}/{primary_language}")
        print(f"Found {len(self._files)} files to translate")

        return self._files

    async def chunk_files(self):
        async def chunk_file(file: File, idx: int):
            file.content = await self._github_client.get_file_content_async(file.path)
            file.chunks = MdxChunker(file.content).chunk()
            print(f"Chunked file {idx + 1}/{len(self._files)}")

        batch_size = 10
        for i in range(0, len(self._files), batch_size):
            batch = self._files[i : i + batch_size]
            tasks = [chunk_file(file, i + idx) for idx, file in enumerate(batch)]
            await asyncio.gather(*tasks)

        return self._files

    async def determine_files_translation_path(
        self, from_language: str, to_language: str
    ):
        async def determine_file_translation_path(file: File, idx: int):
            translation_path_result = await translator_agent.kickoff_async(
                f"""
                Knowing that the pathname of the file being translated is "{file.path}"
                and the primary language of the file is "{from_language}",
                translate the pathname into "{to_language}".

                Its structure is usually "docs/<LANGUAGE>/.../<FILE_NAME>.<EXTENSION>"

                OUTPUT FORMAT:
                - Only the translated pathname, no other text.
                - Change only the language code directory, not the file name or subfolders.
                """
            )
            file.translation_path = translation_path_result.raw
            print(f"Determined translation path for file {idx + 1}/{len(self._files)}")

        batch_size = 10
        for i in range(0, len(self._files), batch_size):
            batch = self._files[i : i + batch_size]
            tasks = [
                determine_file_translation_path(file, i + idx)
                for idx, file in enumerate(batch)
            ]
            await asyncio.gather(*tasks)

        return self._files

    async def translate_files(self, from_language: str, to_language: str):
        async def translate_file(file: File):
            async def translate_chunk(chunk: str):
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        return await translator_agent.kickoff_async(
                            f"""
                            Translate the following text chunk from "{from_language}" into "{to_language}":

                            <start_of_chunk>
                            {chunk}
                            <end_of_chunk>

                            - Respect formatting such as title hierarchy, bold, italic, line breaks, etc.
                            - Do not translate any code blocks. Leave them as-is. The only exception to this rule is if the code contains references to filenames/links
                            that have "docs/{from_language}/..." or similar references to the primary language. In such cases, translate "docs/{from_language}/..." to "docs/{to_language}/...".
                            - Do not translate any entity names like "crew", "flow", "prompt", "knowledge", "reasoning", or any computer science terms.
                            - Output only the translated chunk content, no other text.
                            """
                        )
                    except Exception as e:
                        if attempt < max_attempts - 1:
                            print(
                                f"Translation attempt {attempt + 1} failed: {e}. Retrying in 5 seconds..."
                            )
                            await asyncio.sleep(5)
                        else:
                            print(
                                f"Translation failed after {max_attempts} attempts: {e}"
                            )
                            raise

            chunk_tasks = [translate_chunk(chunk) for chunk in file.chunks]
            chunk_results = await asyncio.gather(*chunk_tasks)
            file.translated_chunks = [result.raw for result in chunk_results]
            file.translation_content = "\n\n".join(file.translated_chunks)

        batch_size = 1
        for i in range(0, len(self._files), batch_size):
            batch = self._files[i : i + batch_size]
            tasks = [translate_file(file) for file in batch]
            await asyncio.gather(*tasks)
            print(f"Translation of file {i + 1}/{len(self._files)} completed")
            sleep(3)

        return self._files
