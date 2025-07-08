#!/usr/bin/env python
import asyncio
import os
from datetime import datetime

from crewai import Agent
from crewai.flow import Flow, listen, start

from crewai_docs_updater.services import GithubService, MdxChunker
from crewai_docs_updater.types import CrewDocsUpdaterState, File


class CrewDocsUpdaterFlow(Flow[CrewDocsUpdaterState]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.github_service = GithubService()

    @start()
    def get_file_content(self):
        print("Getting file content")
        self.state.files_outdated.append(
            File(
                path="docs/en/guides/flows/first-flow.mdx",
                content=self.github_service.get_file_content(
                    "docs/en/guides/flows/first-flow.mdx"
                ),
            )
        )

    @listen(get_file_content)
    def chunk_file(self):
        print("Chunking file")
        mdx_chunker = MdxChunker(self.state.files_outdated[0].content)
        self.state.files_outdated[0].chunks = mdx_chunker.chunk()

    @listen(chunk_file)
    async def translate_file(self):
        print("Translating file")
        agent = Agent(
            role="Translator",
            goal="Translate the file into the secondary languages",
            backstory="You are a translator. You are given a file and you need to translate it into the secondary languages.",
            verbose=True,
        )

        async def translate_chunk(chunk):
            query = f"""
                Translate the following text chunk into pt-BR:

                <start_of_chunk>
                {chunk}
                <end_of_chunk>

                IMPORTANT NOTES:
                - Respect formatting such as title hierarchy, bold, italic, line breaks, etc.
                - Do not translate any code blocks. Leave them in the file as-is.
                - Do not translate any entity names like "crew", "flow", "prompt", "knowledge", or "reasoning".
                - Output only the translated chunk content, no other text.
            """
            result = await agent.kickoff_async(query)
            return result.raw

        batch_size = 10
        for i in range(0, len(self.state.files_outdated[0].chunks), batch_size):
            batch = self.state.files_outdated[0].chunks[i : i + batch_size]
            print(
                f"Translating batch {i // batch_size + 1} ({i + 1}-{min(i + batch_size, len(self.state.files_outdated[0].chunks))}) of {((len(self.state.files_outdated[0].chunks) - 1) // batch_size) + 1}"
            )
            tasks = [translate_chunk(chunk) for chunk in batch]
            batch_results = await asyncio.gather(*tasks)
            self.state.files_outdated[0].translated_chunks.extend(batch_results)
        pass

    @listen(translate_file)
    def save_file(self):
        print("Saving file")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for file in self.state.files_outdated:
            output_path = f"tmp/{timestamp}/{file.path}"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, "w") as f:
                f.write("\n\n".join(file.translated_chunks))

            print(f"Saved: {output_path}")


def kickoff():
    CrewDocsUpdaterFlow().kickoff()


def plot():
    CrewDocsUpdaterFlow().plot()


if __name__ == "__main__":
    kickoff()
