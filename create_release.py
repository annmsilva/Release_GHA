import os
import subprocess
import sys

import requests


def run(cmd):
    result = subprocess.run(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if result.returncode != 0:
        print(f"Command failed: {cmd}\n{result.stderr}")
        sys.exit(1)
    return result.stdout.strip()


def get_branch_name():
    # GitHub sets GITHUB_REF env var like 'refs/heads/release/2508'
    ref = os.environ.get("GITHUB_REF", "")
    if not ref.startswith("refs/heads/release/"):
        print("This script should run on a release/* branch.")
        sys.exit(1)
    return ref[len("refs/heads/") :]


def get_release_num(branch_name):
    # branch_name example: release/2508
    parts = branch_name.split("/")
    if len(parts) < 2:
        print("Branch name format invalid. Expecting release/<number>")
        sys.exit(1)
    return parts[1]


def get_existing_rc_tags(release_num):
    # fetch all tags first
    run("git fetch --tags")

    # list tags starting with release_num + '.'
    tags = run(f"git tag -l '{release_num}.*'")
    tags_list = tags.splitlines()

    rc_numbers = []
    for tag in tags_list:
        parts = tag.split(".")
        if len(parts) == 2 and parts[0] == release_num:
            try:
                rc_num = int(parts[1])
                rc_numbers.append(rc_num)
            except ValueError:
                pass
    return rc_numbers


def create_and_push_tag(new_tag):
    print(f"Creating and pushing tag: {new_tag}")
    run(f"git tag {new_tag}")
    run(f"git push origin {new_tag}")


def create_github_release(token, repo, tag, name, body, draft=False, prerelease=True):
    url = f"https://api.github.com/repos/{repo}/releases"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    data = {
        "tag_name": tag,
        "name": name,
        "body": body,
        "draft": draft,
        "prerelease": prerelease,
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print(f"Release {tag} created successfully.")
    else:
        print(f"Failed to create release: {response.status_code} {response.text}")
        sys.exit(1)


def main():
    # Environment vars
    token = os.environ.get("GITHUB_TOKEN") 
    repo = os.environ.get("GITHUB_REPOSITORY")  # e.g. owner/repo
    if not token or not repo:
        print("GITHUB_TOKEN and GITHUB_REPOSITORY env vars are required")
        sys.exit(1)

    branch_name = get_branch_name()
    release_num = get_release_num(branch_name)

    rc_numbers = get_existing_rc_tags(release_num)
    next_rc = max(rc_numbers) + 1 if rc_numbers else 1
    new_tag = f"{release_num}.{next_rc}"

    create_and_push_tag(new_tag)

    release_name = f"{new_tag}"
    release_body = f"Release Candidate {new_tag} based on branch {branch_name}."

    create_github_release(token, repo, new_tag, release_name, release_body)

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"release_url=https://github.com/{repo}/releases/tag/{new_tag}\n")
            f.write(f"release_version={new_tag}\n")


if __name__ == "__main__":
    main()
