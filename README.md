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

- `"*.java"` targets all Java files
- `"*.py,src/*"` targets all Python files *and* all files in the `src` directory  

### Workflow configuration

An example configuration, note:

- the action is designed to review pull requests, as such the workflow should be triggered on `pull_request`
- the OpenAI API key is provided as a GitHub secret, you may need to adjust this configuration to extract the secret you created above
- the action makes use of the default GitHub token (as discussed above), this token is exposed as a GitHub secret `secrets.GITHUB_TOKEN`

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
      - uses: agogear/chatgpt-pr-review@latest # or a specific version
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
          github_pr_id: ${{ github.event.number }}
```
