from fnmatch import fnmatch
from logging import info
from typing import Iterable, List, Tuple
from re import search
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
            if not file.patch or file.patch == "":
                info(
                    f"skipping file {file.filename} in commit {commit.sha} because it has no patch"
                )
                continue
            for pattern in patterns:
                if fnmatch(file.filename, pattern):
                    changes[file.filename] = commit
    return changes.items()


def main():
    file_patterns = "*"
    g = Github("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")
    prId = 6

    repo = g.get_repo("agogear/chatgpt-test")
    pull = repo.get_pull(prId)
    comments = []
    for filename, commit in files_for_review(pull, file_patterns):
        content = repo.get_contents(filename, commit.sha).decoded_content.decode("utf8")
        if len(content) == 0:
            info(
                f"skipping file {filename} in commit {commit.sha} because the file is empty"
            )
            continue
        comments.append(
            {
                "path": filename,
                # "line": line,
                "position": 1,
                "body": "reviewed!",
            }
        )

    if len(comments) > 0:
        pull.create_review(
            body="**ChatGPT code review**", event="COMMENT", comments=comments
        )


if __name__ == "__main__":
    main()