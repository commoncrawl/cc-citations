import os

from huggingface_hub import Repository, HfApi


repo_id = 'handecelikkanat/hnd-test-repo'
local_dir = './tmp'


# Create test repo
api = HfApi()
api.create_repo(repo_id=repo_id, repo_type="dataset", private=True)


# Try git clone and pull
if not os.path.exists(local_dir):
    repo = Repository(local_dir=local_dir, clone_from=repo_id, token=api.token)
else:
    repo = Repository(local_dir=local_dir, token=api.token)
    repo.git_pull()

