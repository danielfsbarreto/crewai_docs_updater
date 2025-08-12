import base64
import os

import aiohttp
from github import Auth, Github

from crewai_docs_updater.types import File


class GithubClient:
    _REPO_NAME = "crewAIInc/crewAI"

    def __init__(self):
        self._client = Github(auth=Auth.Token(os.getenv("GITHUB_AUTH_KEY")))
        self._repo = self._client.get_repo(self._REPO_NAME)

    def get_files(self, docs_dir: str) -> list[File]:
        sha = self._repo.get_branch(self._repo.default_branch).commit.sha
        tree = self._repo.get_git_tree(sha=sha, recursive=True).tree

        return [
            File(
                path=item.path,
                content=None,
            )
            for item in tree
            if item.path.startswith(docs_dir + "/")
            and item.path.endswith((".mdx", ".md"))
        ]

    def _get_file_content(self, path: str) -> str:
        return self._repo.get_contents(path).decoded_content.decode("utf-8")

    async def get_file_content_async(self, path: str) -> str:
        owner = "crewAIInc"
        repo = "crewAI"
        token = os.getenv("GITHUB_AUTH_KEY")

        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {token}",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return base64.b64decode(data["content"]).decode("utf-8")
                else:
                    raise Exception(
                        f"Failed to get file content: HTTP {response.status}"
                    )
