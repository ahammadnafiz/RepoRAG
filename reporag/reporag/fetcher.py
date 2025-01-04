# repoprompter/repoprompter/fetcher.py
from github import Github, GithubException

def fetch_repo_content(repo_url, access_token):
    try:
        g = Github(access_token)
        repo = g.get_repo(repo_url)
        contents = repo.get_contents("")
        # print(f"Repository content fetched: {contents} items")
        return repo, contents
    except GithubException as e:
        if e.status == 404:
            raise Exception(f"Repository not found: {repo_url}. Please check the repository URL and access token.")
        elif e.status == 401:
            raise Exception(f"Unauthorized access: {repo_url}. Please check your access token and permissions.")
        else:
            raise Exception(f"GitHub API error: {e.data['message']}")
    except Exception as e:
        raise Exception(f"Error fetching repository content: {str(e)}")
