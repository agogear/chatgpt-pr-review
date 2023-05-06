from fnmatch import fnmatch
from logging import info
from time import sleep
import os
from typing import Iterable, List, Tuple
from argparse import ArgumentParser
from re import search
import openai
from github import Github, PullRequest, Commit

OPENAI_BACKOFF_SECONDS = 20  # 3 requests per minute
OPENAI_MAX_RETRIES = 3


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


def prompt(filename: str, contents: str) -> str:
    code = "code"
    type = code_type(filename)
    if type:
        code = f"{type} {code}"

    return (
        f"Please evaluate the {code} below.\n"
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


def is_merge_commit(commit: Commit.Commit) -> bool:
    return len(commit.parents) > 1


def line_start_patch(patch: str) -> int:
    match = search(r"^@@ [-+](\d*),", patch)
    return int(match.group(1))


def files_for_review(
    pull: PullRequest.PullRequest, patterns: List[str]
) -> Iterable[Tuple[str, int, Commit.Commit]]:
    changes = {}
    commits = pull.get_commits()
    for commit in commits:
        if is_merge_commit(commit):
            info(f"skipping commit {commit.sha} because it's a merge commit")
            continue
        for file in commit.files:
            if file.status in ["unchanged", "removed"]:
                info(
                    f"skipping file {file.filename} in commit {commit.sha} because its status is {file.status}"
                )
                continue
            if not file.patch:
                info(
                    f"skipping file {file.filename} in commit {commit.sha} because it has no patch"
                )
                continue
            for pattern in patterns:
                if fnmatch(file.filename, pattern):
                    changes[file.filename] = (line_start_patch(file.patch), commit)

    return [(x[0], max(1, x[1][0]), x[1][1]) for x in changes.items()]


def review(
    filename: str, content: str, model: str, temperature: float, max_tokens: int
) -> str:
    for _ in range(OPENAI_MAX_RETRIES):
        try:
            chat_review = (
                openai.ChatCompletion.create(
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt(filename, content),
                        }
                    ],
                )
                .choices[0]
                .message.content
            )
            return f"*ChatGPT review for {filename}:*\n" f"{chat_review}"
        except openai.error.RateLimitError:
            info("OpenAI rate limit hit, backing off and trying again...")
            sleep(OPENAI_BACKOFF_SECONDS)
    Exception(
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
        default="gpt-3.5-turbo",
        help="GPT-3 model to use. Options: gpt-3.5-turbo, text-davinci-002, "
        "text-babbage-001, text-curie-001, text-ada-001. Recommended: gpt-3.5-turbo",
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
    args = parser.parse_args()

    file_patterns = args.files.split(",")
    openai.api_key = args.openai_api_key
    g = Github(args.github_token)

    repo = g.get_repo(os.getenv("GITHUB_REPOSITORY"))
    pull = repo.get_pull(args.github_pr_id)
    comments = []
    for filename, line, commit in files_for_review(pull, file_patterns):
        content = repo.get_contents(filename, commit.sha).decoded_content.decode("utf8")
        if len(content) == 0:
            info(
                f"skipping file {filename} in commit {commit.sha} because the file is empty"
            )
            continue
        comments.append(
            {
                "path": filename,
                "line": line,
                "body": review(
                    filename,
                    content,
                    args.openai_model,
                    args.openai_temperature,
                    args.openai_max_tokens,
                ),
            }
        )

    if len(comments) > 0:
        pull.create_review(
            body="**ChatGPT code review**", event="COMMENT", comments=comments
        )


if __name__ == "__main__":
    main()
