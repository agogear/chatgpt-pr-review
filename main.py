from fnmatch import fnmatch
from logging import info, basicConfig, getLevelName, debug
from time import sleep
import os
from typing import Iterable, List, Tuple
from argparse import ArgumentParser
from re import search
import openai
from github import Github, PullRequest, Commit

OPENAI_BACKOFF_SECONDS = 20  # 3 requests per minute
OPENAI_MAX_RETRIES = 3

MAX_FILES_ALLOWED_FOR_REVIEW = 10


def code_type(filename: str) -> str | None:
    match = search(r"^.*\.([^.]*)$", filename)
    if match:
        match match.group(1):
            case "js":
                return "JavaScript"
            case "ts":
                return "TypeScript"
            case "java":
                return "Java"
            case "py":
                return "Python"


def prompt(
    filename: str,
    contents: str,
    pr_description: str,
    comments: List[str],
    readme: str,
) -> str:
    code = "code"
    type = code_type(filename)
    if type:
        code = f"{type} {code}"

    additional_context = (
        f"PR Description (provides intent and high-level overview):\n{pr_description}\n\n"
        + "PR Comments (feedback and discussions from team members):\n"
        + "\n".join(comments)
        + "\n\nREADME (project overview and setup instructions):\n"
        + f"{readme}\n\n"
    )

    return (
        f"Please evaluate the {code} below with the following additional context:\n{additional_context}\n"
        "Use the following checklist to guide your analysis:\n"
        "   1. Documentation Defects:\n"
        "       a. Naming: Assess the quality of software element names.\n"
        "       b. Comment: Analyze the quality and accuracy of code comments.\n"
        "   2. Visual Representation Defects:\n"
        "       a. Bracket Usage: Identify any issues with incorrect or missing brackets.\n"
        "       b. Indentation: Check for incorrect indentation that affects readability.\n"
        "       c. Long Line: Point out any long code statements that hinder readability.\n"
        "   3. Structure Defects:\n"
        "       a. Dead Code: Find any code statements that serve no meaningful purpose.\n"
        "       b. Duplication: Identify duplicate code statements that can be refactored.\n"
        "   4. New Functionality:\n"
        "       a. Use Standard Method: Determine if a standardized approach should be used for single-purpose code statements.\n"
        "   5. Resource Defects:\n"
        "       a. Variable Initialization: Identify variables that are uninitialized or incorrectly initialized.\n"
        "       b. Memory Management: Evaluate the program's memory usage and management.\n"
        "   6. Check Defects:\n"
        "       a. Check User Input: Analyze the validity of user input and its handling.\n"
        "   7. Interface Defects:\n"
        "       a. Parameter: Detect incorrect or missing parameters when calling functions or libraries.\n"
        "   8. Logic Defects:\n"
        "       a. Compute: Identify incorrect logic during system execution.\n"
        "       b. Performance: Evaluate the efficiency of the algorithm used.\n"
        "Provide your feedback in a numbered list for each category. At the end of your answer, summarize the recommended changes to improve the quality of the code provided.\n"
        f"```\n{contents}\n```"
    )


def fetch_contextual_info(
    pull: PullRequest.PullRequest, repo
) -> Tuple[str, List[str], str]:
    pr_description = pull.body or "No description provided."
    comments = [
        comment.body
        for comment in list(pull.get_issue_comments())
        + list(pull.get_review_comments())
        if not comment.user.type == "Bot"
    ]
    # Try to fetch README file content, considering different common casings
    readme_filenames = ["README.md", "Readme.md", "readme.md", "README.MD", "ReadMe.md"]
    readme_content = "No README file found."
    for filename in readme_filenames:
        try:
            readme_content = repo.get_contents(filename).decoded_content.decode("utf8")
            break  # If found, break out of the loop
        except Exception:
            # Continue trying other filenames if not found
            continue

    return pr_description, comments, readme_content


def is_merge_commit(commit: Commit.Commit) -> bool:
    return len(commit.parents) > 1


def files_for_review(
    pull: PullRequest.PullRequest, patterns: List[str]
) -> Iterable[Tuple[str, Commit.Commit, str]]:
    changes = {}
    commits = pull.get_commits()
    for commit in commits:
        if is_merge_commit(commit):
            info(f"skipping commit {commit.sha} because it's a merge commit")
            continue
        for file in commit.files:
            if file.status in ("unchanged", "removed"):
                info(
                    f"skipping file {file.filename} in commit {commit.sha} because its status is {file.status}"
                )
                continue
            if file.status == "renamed":
                info(
                    f"Skipping file {file.filename} in commit {commit.sha} because it was renamed from {file.previous_filename}"
                )
                if file.previous_filename in changes:
                    # rename the key in the changes dict to ensure review is done on the correct file
                    info(
                        f"renaming file {file.previous_filename} to {file.filename} in changes"
                    )
                    changes[file.filename] = changes.pop(file.previous_filename)

                continue
            if not file.patch or file.patch == "":
                info(
                    f"skipping file {file.filename} in commit {commit.sha} because it has no patch"
                )
                continue

            if any(
                fnmatch(file.filename.strip(), pattern.strip()) for pattern in patterns
            ):
                changes[file.filename] = {
                    "sha": commit.sha,
                    "filename": file.filename,
                }
                info(f"adding file {file.filename} to review")

    return changes.items()


def review(
    filename: str,
    content: str,
    model: str,
    temperature: float,
    max_tokens: int,
    pr_description: str,
    comments: List[str],
    readme: str,
) -> str:
    x = 0
    while True:
        try:
            prompt_text = prompt(filename, content, pr_description, comments, readme)
            info(f"requesting OpenAI review for file {filename}")
            info(f"prompt text:\n{prompt_text}")
            chat_review = (
                openai.ChatCompletion.create(
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt_text,
                        }
                    ],
                )
                .choices[0]
                .message.content
            )
            return f"*ChatGPT review for {filename}:*\n" f"{chat_review}"
        except openai.error.RateLimitError:
            if x < OPENAI_MAX_RETRIES:
                info("OpenAI rate limit hit, backing off and trying again...")
                sleep(OPENAI_BACKOFF_SECONDS)
                x += 1
            else:
                raise Exception(
                    f"finally failing request to OpenAI platform for code review, max retries {OPENAI_MAX_RETRIES} exceeded"
                )


def main():
    parser = ArgumentParser()
    parser.add_argument("--openai_api_key", required=True, help="OpenAI API Key")
    parser.add_argument("--github_token", required=True, help="Github Access Token")
    parser.add_argument(
        "--github_pr_id", required=True, type=int, help="Github PR ID to review"
    )
    parser.add_argument(
        "--openai_model",
        default="gpt-5-nano",
        help="GPT model to use. Options: gpt-5-nano, "
        "gpt-5-mini, gpt-4o-mini. Recommended: gpt-5-nano",
    )
    parser.add_argument(
        "--openai_temperature",
        default=0.5,
        type=float,
        help="Sampling temperature to use, a float [0, 1]. Higher values "
        "mean the model will take more risks. Recommended: 0.5",
    )
    parser.add_argument(
        "--openai_max_tokens",
        default=2048,
        type=int,
        help="The maximum number of tokens to generate in the completion.",
    )
    parser.add_argument(
        "--files",
        help="Comma separated list of UNIX file patterns to target for review",
    )
    parser.add_argument(
        "--logging",
        default="warning",
        type=str,
        help="logging level",
        choices=["debug", "info", "warning", "error"],
    )
    args = parser.parse_args()

    basicConfig(encoding="utf-8", level=getLevelName(args.logging.upper()))
    file_patterns = args.files.split(",")
    openai.api_key = args.openai_api_key
    g = Github(args.github_token)

    repo = g.get_repo(os.getenv("GITHUB_REPOSITORY"))
    pull = repo.get_pull(args.github_pr_id)
    files = files_for_review(pull, file_patterns)

    n_files = len(files)
    if n_files > MAX_FILES_ALLOWED_FOR_REVIEW:
        raise Exception(
            f"too many files to review ({n_files}), limit is {MAX_FILES_ALLOWED_FOR_REVIEW}"
            "Make sure to target specific files using the --files argument in action configuration"
        )

    info(f"files for review: {files}")
    pr_description, pr_comments, readme = fetch_contextual_info(pull, repo)
    comments = []
    for filename, commit in files:
        commit_sha = commit["sha"]
        commit_filename = commit["filename"]

        debug(f"starting review for file {filename} and commit sha {commit_sha}")
        content = repo.get_contents(commit_filename, commit_sha).decoded_content.decode(
            "utf8"
        )
        if len(content) == 0:
            info(
                f"skipping file {filename} in commit {commit_sha} because the file is empty"
            )
            continue
        body = review(
            filename,
            content,
            args.openai_model,
            args.openai_temperature,
            args.openai_max_tokens,
            pr_description,
            pr_comments,
            readme,
        )
        if body and body != "":
            debug(f"attaching comment body to review:\n{body}")
            comments.append(
                {
                    "path": filename,
                    # "line": line,
                    "position": 1,
                    "body": body,
                }
            )

    if len(comments) > 0:
        pull.create_review(
            body="**ChatGPT code review**", event="COMMENT", comments=comments
        )


if __name__ == "__main__":
    main()
    print(fnmatch("main.py", "*.py"))
