import os

from github import Auth, Github


class GithubService:
    _REPO_NAME = "crewAIInc/crewAI"

    def __init__(self):
        self.client = Github(auth=Auth.Token(os.getenv("GITHUB_AUTH_KEY")))
        self.repo = self.client.get_repo(self._REPO_NAME)

    def get_file_content(self, path: str) -> str:
        return self.repo.get_contents(path).decoded_content.decode("utf-8")
