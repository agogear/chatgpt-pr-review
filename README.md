# ChatGPT Pull Request Review Action

## Introduction

This GitHub action autonomously reviews pull requests by supplying the contents of changed files (introduced via a simple prompt) to ChatGPT.

## Usage

### ChatGPT integration

The action integrates with OpenAI's v2 ChatGPT API, and thus requires access to a valid API key with which to authenticate requests to OpenAI platforms. Sign up and generate your own key [here](https://platform.openai.com) (once logged in, navigate to Personal > View API keys). The most secure way to expose your key to the action is via [GitHub secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets).

### GitHub integration

The action submits reviews to a pull request via the GitHub REST API. The easiest way to authenticate the action to the GitHub API is to make use of the token that GitHub generates at the start of each workflow run. Beware that this token is, by default, only granted read permissions for the target repository - you will need to [grant the token write permissions](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository#configuring-the-default-github_token-permissions).

### Files

The action targets all new or modified files for review, you can (and probably should) limit the scope of the review by providing a comma separated list of Unix file patterns to the `file` action input. For example:

-   `"*.java"` targets all Java files
-   `"*.py,src/*"` targets all Python files _and_ all files in the `src` directory

### Workflow configuration

Configuration:

-   the action is designed to review pull requests, as such the workflow should be triggered on `pull_request`
-   the OpenAI API key is provided as a GitHub secret, you may need to adjust this configuration to extract the secret you created above
-   the action makes use of the default GitHub token (as discussed above), this token is exposed as a GitHub secret `secrets.GITHUB_TOKEN`
-   An example is provided below: .github/workflows/pr-chat-review.yaml (.yaml file must be inside .github/workflows/ folder)
  
```yaml
name: pr-review
on:
    pull_request:
        types: [opened, synchronize]
jobs:
    review:
        name: ChatGPT code review
        runs-on: ubuntu-latest
        steps:
            - uses: agogear/chatgpt-pr-review@0.0.16
              with:
                  openai_api_key: ${{ secrets.OPENAI_API_KEY }}
                  github_token: ${{ secrets.GITHUB_TOKEN }}
                  github_pr_id: ${{ github.event.number }}
                  files: "*.js, *ts, *.py, *.cpp, *.java"
                  openai_model: gpt-5-nano
```

### Optional: Pull Request template configuration

While not strictly necessary, it is recommended to include a [pull request template](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository) in your repository to guide contributors in providing the necessary information for the action to review the pull request as well as to provide context for the reviewer.

An example template is provided below:

Copy the following template to `.github/PULL_REQUEST_TEMPLATE.md` in your repository:

```markdown
# Pull Request Template

## Description

Please include a summary of the change and which issue is fixed. Include the motivation and context, and list any dependencies that are required for this change.

Fixes # (issue number)

## Type of change

Please delete options that are not relevant.

-   [ ] Bug fix (non-breaking change which fixes an issue)
-   [ ] New feature (non-breaking change which adds functionality)
-   [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
-   [ ] This change requires a documentation update

## How Has This Been Tested?

Please describe the tests that you ran to verify your changes. Provide instructions so we can reproduce. Please also list any relevant details for your test configuration.

-   [ ] Test A
-   [ ] Test B

## Dependencies

Mention any dependencies this PR relies on or blocks

Depends on # (PR)
Blocks # (PR)

## Screenshots/Documentation

Include any relevant screenshots or gifs that demonstrate the UI changes. Include links to updated documentation if applicable.

## Checklist for Reviewers

-   [ ] Code follows the project's style guidelines
-   [ ] Adequate tests have been added
-   [ ] Functionality and bug fixes are confirmed via tests
-   [ ] Existing tests have been adapted to accommodate the changes
-   [ ] The changes do not generate new warnings/errors

## Request for Specific Feedback

Optional: Mention any particular aspects of the PR where you would like to receive specific feedback.

## Additional Information

Anything else you want to add (links to documentation, style guides, etc.)
```
