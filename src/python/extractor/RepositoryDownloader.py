import hashlib
import os
import pickle

import requests
from dotenv import load_dotenv

from src.python.entities.RateLimitException import RateLimitException
from src.python.extractor.Utilities import download_files


class AutomationDownloader:
    def __init__(self, save_path=None):
        load_dotenv()
        self.save_path = save_path
        self.requests_path = "../requests"
        os.makedirs(self.requests_path, exist_ok=True)
        self.num_requests = 0
        self.rate_limit_remaining = "unknown"
        self.rate_limit_total = 5000
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.base_headers = (
            {"Authorization": f"token {self.github_token}"} if self.github_token else {}
        )

    def send_request(self, url: str, params=None):
        filename_url = hashlib.sha256(url.encode()).hexdigest() + ".pkl"
        file_path = os.path.join(self.requests_path, filename_url)
        old_filename_url = url.replace("/", "*") + ".pkl"
        old_file_path = os.path.join(self.requests_path, old_filename_url)
        # Check if the file exists at the specified path
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                return pickle.load(f)
        elif os.path.exists(old_file_path):
            with open(old_file_path, "rb") as f:
                return pickle.load(f)
        else:
            response = requests.get(url, headers=self.base_headers, params=params)
            if response.status_code == 403 or response.status_code == 429:
                raise RateLimitException(f"Rate limit exceeded on {filename_url}")

            self.num_requests += 1
            if "x-ratelimit-remaining" in response.headers:
                self.rate_limit_remaining = response.headers["x-ratelimit-remaining"]
            if "x-ratelimit-limit" in response.headers:
                self.rate_limit_total = response.headers["x-ratelimit-limit"]

            with open(file_path, "wb") as f:
                pickle.dump(response, f)
            return response

    def download_files(self, repo: str):
        # Grab GitHub token, create headers and URL
        url = f"https://api.github.com/repos/{repo}/contents/.github/workflows"

        # Send request
        found_files = self.send_request(url)
        pom_files = self.search_for_pom_files(repo)
        files = list()
        eligible_files = 0

        path = os.path.join(repo)
        print("Downloading", path, end="")

        os.makedirs(os.path.join(self.save_path, repo), exist_ok=True)

        # No files
        if type(pom_files) is int or (
            found_files.status_code != 200 and len(pom_files) == 0
        ):
            return 0, 0
        elif found_files.status_code == 200:
            json = found_files.json()
            if type(json) is not list:
                files = [found_files.json()]
            else:
                files = found_files.json()

        for pom_file in pom_files:
            pom_url = f"https://api.github.com/repos/{repo}/contents/{pom_file['path']}"
            pom_file = self.send_request(pom_url)
            if pom_file.status_code == 200:
                files.append(pom_file.json())

        found = False
        # Filter and download only .yaml files
        for each_file in files:
            file_name = each_file["name"]
            if any(
                file_name.endswith(extension)
                for extension in [".yaml", ".yml", "pom.xml"]
            ):
                found = True
                eligible_files += 1
                if file_name.endswith("pom.xml"):
                    self.download_file(
                        each_file["download_url"], os.path.join(repo, each_file["path"])
                    )
                else:
                    self.download_file(
                        each_file["download_url"], os.path.join(repo, file_name)
                    )
        if not found:
            print(" Error found")
            return 0, 0

        return len(pom_files), eligible_files - len(pom_files)

    def search_for_pom_files(self, repo):
        """
        Find a pom.xml file in a given repository
        :param repo:
        :return:
        """
        repo_url = f"https://api.github.com/repos/{repo}"
        whole_repo = self.send_request(repo_url)
        if whole_repo.status_code != 200:
            print(f"Remove {repo}")
            return 0
        default_branch = whole_repo.json()["default_branch"]
        sha_url = f"https://api.github.com/repos/{repo}/git/refs/heads/{default_branch}"
        sha = self.send_request(sha_url)

        pom_files = []

        if sha.status_code == 200:
            sha = sha.json()["object"]["sha"]

            # Step 2: Get the tree using the SHA
            tree_url = (
                f"https://api.github.com/repos/{repo}/git/trees/{sha}?recursive=1"
            )
            tree_response = self.send_request(tree_url)
            if tree_response.status_code == 200:
                tree = tree_response.json()["tree"]
                for item in tree:
                    if item["path"].endswith("/pom.xml") or item["path"] == "pom.xml":
                        pom_files.append(item)
                    if "gradle" in item["path"]:
                        return 0

        return pom_files

    def download_file(self, url, filename, params=None):
        path = os.path.join(self.save_path, filename)
        downloaded_file = self.send_request(url, params=params)
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        except FileNotFoundError as e:
            print(e)
            return

        with open(path, "wb") as f:
            f.write(downloaded_file.content)


if __name__ == "__main__":
    downloaders = [
        AutomationDownloader("../output/java"),
        AutomationDownloader("../output/python"),
    ]
    with open("../data/rq1_python_repos.txt") as file:
        repos = [line.strip() for line in file if line.strip()]
    with open("../data/rq1_java_repos.txt") as file:
        repos.extend([line.strip() for line in file if line.strip()])

    no_poms = download_files(repos, downloaders)
    for repo in set(repos).difference(no_poms):
        print(repo)
