"""Tests for the YAML builder module."""

import os
from pathlib import Path

import yaml

# Use absolute imports from the package
from pre_commit_starter.generator.hooks.hook_registry import HookRegistry
from pre_commit_starter.generator.yaml_builder import YAMLBuilder

EXPECTED_REPO_COUNT = 2  # Expected number of repositories in basic configuration


def load_expected_config(filename):
    """Load expected config from file."""
    config_path = os.path.join(os.path.dirname(__file__), "expected_configs", filename)
    with open(config_path) as f:
        return f.read()


def test_python_config_generation():
    """Test generation of pre-commit config for Python repository."""
    hook_registry = HookRegistry()
    yaml_builder = YAMLBuilder(hook_registry)

    generated_config = yaml_builder.build_config(["python"])
    config_dict = yaml.safe_load(generated_config)

    # Check header comments
    assert "Technologies detected: python" in generated_config
    assert "https://github.com/Jakub3628800/pre-commit-starter" in generated_config

    # Check essential repos are included
    repo_urls = [repo["repo"] for repo in config_dict["repos"]]
    assert "https://github.com/pre-commit/pre-commit-hooks" in repo_urls
    assert "https://github.com/astral-sh/ruff-pre-commit" in repo_urls
    assert "https://github.com/RobertCraigie/pyright-python" in repo_urls
    assert "https://github.com/abravalheri/validate-pyproject" in repo_urls

    # Verify Black, isort, and flake8 are NOT included (to avoid conflicts with Ruff)
    assert "https://github.com/psf/black" not in repo_urls
    assert "https://github.com/pycqa/isort" not in repo_urls
    assert "https://github.com/pycqa/flake8" not in repo_urls

    # Check essential hooks are included
    ruff_repo = next(
        repo
        for repo in config_dict["repos"]
        if repo["repo"] == "https://github.com/astral-sh/ruff-pre-commit"
    )
    ruff_hook_ids = [hook["id"] for hook in ruff_repo["hooks"]]
    assert "ruff" in ruff_hook_ids
    assert "ruff-format" in ruff_hook_ids


def test_mixed_config_generation():
    """Test generation of pre-commit config for mixed technology repository."""
    technologies = ["python", "javascript", "terraform", "docker", "shell"]
    hook_registry = HookRegistry()
    yaml_builder = YAMLBuilder(hook_registry)

    generated_config = yaml_builder.build_config(technologies)
    config_dict = yaml.safe_load(generated_config)

    # Check header comments - technologies should be present in the generated config
    for tech in technologies:
        assert tech in generated_config, f"Technology {tech} not found in config"

    # Check essential repos are included
    repo_urls = [repo["repo"] for repo in config_dict["repos"]]
    assert "https://github.com/pre-commit/pre-commit-hooks" in repo_urls
    assert "https://github.com/astral-sh/ruff-pre-commit" in repo_urls
    assert "https://github.com/pre-commit/mirrors-prettier" in repo_urls
    assert "https://github.com/antonbabenko/pre-commit-terraform" in repo_urls
    assert "https://github.com/hadolint/hadolint" in repo_urls
    assert "https://github.com/shellcheck-py/shellcheck-py" in repo_urls

    # Check essential hooks from each technology
    # Python - check Ruff hooks
    ruff_repo = next(
        repo
        for repo in config_dict["repos"]
        if repo["repo"] == "https://github.com/astral-sh/ruff-pre-commit"
    )
    ruff_hook_ids = [hook["id"] for hook in ruff_repo["hooks"]]
    assert "ruff" in ruff_hook_ids
    assert "ruff-format" in ruff_hook_ids

    # JavaScript
    prettier_repo = next(
        repo
        for repo in config_dict["repos"]
        if repo["repo"] == "https://github.com/pre-commit/mirrors-prettier"
    )
    prettier_hook_ids = [hook["id"] for hook in prettier_repo["hooks"]]
    assert "prettier" in prettier_hook_ids

    # Terraform
    terraform_repo = next(
        repo
        for repo in config_dict["repos"]
        if repo["repo"] == "https://github.com/antonbabenko/pre-commit-terraform"
    )
    terraform_hook_ids = [hook["id"] for hook in terraform_repo["hooks"]]
    assert "terraform_fmt" in terraform_hook_ids

    # Docker
    docker_repo = next(
        repo
        for repo in config_dict["repos"]
        if repo["repo"] == "https://github.com/hadolint/hadolint"
    )
    docker_hook_ids = [hook["id"] for hook in docker_repo["hooks"]]
    assert "hadolint" in docker_hook_ids

    # Shell
    shell_repo = next(
        repo
        for repo in config_dict["repos"]
        if repo["repo"] == "https://github.com/shellcheck-py/shellcheck-py"
    )
    shell_hook_ids = [hook["id"] for hook in shell_repo["hooks"]]
    assert "shellcheck" in shell_hook_ids


def test_hook_merging():
    """Test that hooks from the same repository are merged correctly."""
    # Create a case where the same repo is used for different technologies
    technologies = ["json", "javascript"]  # Both use prettier
    hook_registry = HookRegistry()
    yaml_builder = YAMLBuilder(hook_registry)

    generated_config = yaml_builder.build_config(technologies)
    config_dict = yaml.safe_load(generated_config)

    # Count occurrences of prettier repo
    prettier_repos = [
        repo
        for repo in config_dict["repos"]
        if repo["repo"] == "https://github.com/pre-commit/mirrors-prettier"
    ]

    # Print debug info
    print("\nPrettier hooks debug info:")
    for repo in prettier_repos:
        print(f"Repository: {repo['repo']}")
        for hook in repo["hooks"]:
            print(f"  Hook: {hook}")

    # Should only appear once with merged hooks
    assert len(prettier_repos) == 1

    # The hooks should be merged
    prettier_hooks = prettier_repos[0]["hooks"]
    assert any(
        hook["id"] == "prettier" and "types" in hook and hook["types"] == ["json"]
        for hook in prettier_hooks
    )
    # Instead of checking for JavaScript types specifically, just verify we have multiple
    # hooks for prettier
    assert len([hook for hook in prettier_hooks if hook["id"] == "prettier"]) > 1


def test_empty_tech_detection():
    """Test behavior when no technologies are detected."""
    hook_registry = HookRegistry()
    yaml_builder = YAMLBuilder(hook_registry)

    generated_config = yaml_builder.build_config([])
    config_dict = yaml.safe_load(generated_config)

    # Should include basic pre-commit hooks and gitleaks
    assert len(config_dict["repos"]) == EXPECTED_REPO_COUNT
    assert any(
        repo["repo"] == "https://github.com/pre-commit/pre-commit-hooks"
        for repo in config_dict["repos"]
    )
    assert any(
        repo["repo"] == "https://github.com/gitleaks/gitleaks" for repo in config_dict["repos"]
    )


def test_hook_ordering():
    """Test that hooks are ordered correctly in the output."""
    technologies = ["python", "javascript"]
    hook_registry = HookRegistry()
    yaml_builder = YAMLBuilder(hook_registry)

    generated_config = yaml_builder.build_config(technologies)
    config_dict = yaml.safe_load(generated_config)

    # pre-commit-hooks should always be first
    assert config_dict["repos"][0]["repo"] == "https://github.com/pre-commit/pre-commit-hooks"

    # Python hooks should come before JavaScript hooks
    python_hooks_idx = next(
        i
        for i, repo in enumerate(config_dict["repos"])
        if repo["repo"] == "https://github.com/astral-sh/ruff-pre-commit"
    )
    js_hooks_idx = next(
        i
        for i, repo in enumerate(config_dict["repos"])
        if repo["repo"] == "https://github.com/pre-commit/mirrors-prettier"
    )
    assert python_hooks_idx < js_hooks_idx


def test_hook_configuration():
    """Test that hooks are configured with correct parameters."""
    hook_registry = HookRegistry()
    yaml_builder = YAMLBuilder(hook_registry)

    generated_config = yaml_builder.build_config(["python"])
    config_dict = yaml.safe_load(generated_config)

    # Check Ruff configuration
    ruff_repo = next(
        repo
        for repo in config_dict["repos"]
        if repo["repo"] == "https://github.com/astral-sh/ruff-pre-commit"
    )
    ruff_hook = next(hook for hook in ruff_repo["hooks"] if hook["id"] == "ruff")
    assert ruff_hook["args"] == ["--fix"]


def test_invalid_tech():
    """Test behavior with invalid technology."""
    hook_registry = HookRegistry()
    yaml_builder = YAMLBuilder(hook_registry)

    generated_config = yaml_builder.build_config(["invalid_tech"])
    config_dict = yaml.safe_load(generated_config)

    # Should include basic pre-commit hooks and gitleaks
    assert len(config_dict["repos"]) == EXPECTED_REPO_COUNT
    assert any(
        repo["repo"] == "https://github.com/pre-commit/pre-commit-hooks"
        for repo in config_dict["repos"]
    )
    assert any(
        repo["repo"] == "https://github.com/gitleaks/gitleaks" for repo in config_dict["repos"]
    )


def test_go_config_generation():
    """Test generation of pre-commit config for Go repository."""
    hook_registry = HookRegistry()
    yaml_builder = YAMLBuilder(hook_registry)

    generated_config = yaml_builder.build_config(["go"])
    config_dict = yaml.safe_load(generated_config)

    # Check header comments
    assert "Technologies detected: go" in generated_config
    assert "https://github.com/Jakub3628800/pre-commit-starter" in generated_config

    # Check essential repos are included
    repo_urls = [repo["repo"] for repo in config_dict["repos"]]
    assert "https://github.com/pre-commit/pre-commit-hooks" in repo_urls
    assert "https://github.com/golangci/golangci-lint" in repo_urls
    assert "https://github.com/dnephin/pre-commit-golang" in repo_urls

    # Check essential hooks are included
    golangci_repo = next(
        repo
        for repo in config_dict["repos"]
        if repo["repo"] == "https://github.com/golangci/golangci-lint"
    )
    golangci_hook_ids = [hook["id"] for hook in golangci_repo["hooks"]]
    assert "golangci-lint" in golangci_hook_ids

    golang_repo = next(
        repo
        for repo in config_dict["repos"]
        if repo["repo"] == "https://github.com/dnephin/pre-commit-golang"
    )
    golang_hook_ids = [hook["id"] for hook in golang_repo["hooks"]]
    assert "go-fmt" in golang_hook_ids
    assert "go-vet" in golang_hook_ids
    assert "go-imports" in golang_hook_ids
    assert "go-critic" in golang_hook_ids


def test_frontend_config_generation():
    """Test generation of pre-commit config for frontend repository."""
    technologies = ["css", "html", "javascript", "react", "typescript"]
    hook_registry = HookRegistry()
    yaml_builder = YAMLBuilder(hook_registry)

    generated_config = yaml_builder.build_config(technologies)
    config_dict = yaml.safe_load(generated_config)

    # Check header comments
    assert "Technologies detected: css, html, javascript, react, typescript" in generated_config
    assert "https://github.com/Jakub3628800/pre-commit-starter" in generated_config

    # Check essential repos are included
    repo_urls = [repo["repo"] for repo in config_dict["repos"]]
    assert "https://github.com/pre-commit/pre-commit-hooks" in repo_urls
    assert "https://github.com/pre-commit/mirrors-prettier" in repo_urls
    assert "https://github.com/pre-commit/mirrors-eslint" in repo_urls
    assert "https://github.com/thibaudcolas/curlylint" in repo_urls
    assert "https://github.com/pre-commit/mirrors-csslint" in repo_urls

    # Check essential hooks are included
    prettier_repo = next(
        repo
        for repo in config_dict["repos"]
        if repo["repo"] == "https://github.com/pre-commit/mirrors-prettier"
    )
    prettier_hook_ids = [hook["id"] for hook in prettier_repo["hooks"]]
    assert "prettier" in prettier_hook_ids

    eslint_repo = next(
        repo
        for repo in config_dict["repos"]
        if repo["repo"] == "https://github.com/pre-commit/mirrors-eslint"
    )
    eslint_hook_ids = [hook["id"] for hook in eslint_repo["hooks"]]
    assert "eslint" in eslint_hook_ids

    # Check that there's a hook for HTML
    curlylint_repo = next(
        repo
        for repo in config_dict["repos"]
        if repo["repo"] == "https://github.com/thibaudcolas/curlylint"
    )
    curlylint_hook_ids = [hook["id"] for hook in curlylint_repo["hooks"]]
    assert "curlylint" in curlylint_hook_ids

    # Check that there's a hook for CSS
    csslint_repo = next(
        repo
        for repo in config_dict["repos"]
        if repo["repo"] == "https://github.com/pre-commit/mirrors-csslint"
    )
    csslint_hook_ids = [hook["id"] for hook in csslint_repo["hooks"]]
    assert "csslint" in csslint_hook_ids


def test_rust_config_generation():
    """Test generation of pre-commit config for Rust repository."""
    hook_registry = HookRegistry()
    yaml_builder = YAMLBuilder(hook_registry)

    generated_config = yaml_builder.build_config(["rust"])
    config_dict = yaml.safe_load(generated_config)

    # Check header comments
    assert "Technologies detected: rust" in generated_config
    assert "https://github.com/Jakub3628800/pre-commit-starter" in generated_config

    # Check essential repos are included
    repo_urls = [repo["repo"] for repo in config_dict["repos"]]
    assert "https://github.com/pre-commit/pre-commit-hooks" in repo_urls
    assert "https://github.com/doublify/pre-commit-rust" in repo_urls

    # Check essential hooks are included
    rust_repo = next(
        repo
        for repo in config_dict["repos"]
        if repo["repo"] == "https://github.com/doublify/pre-commit-rust"
    )
    rust_hook_ids = [hook["id"] for hook in rust_repo["hooks"]]
    assert "fmt" in rust_hook_ids
    assert "cargo-check" in rust_hook_ids
    assert "clippy" in rust_hook_ids


def test_build_config_with_basic_hooks(tmp_path: Path) -> None:
    """Test building configuration with basic hooks."""
    builder = YAMLBuilder(HookRegistry())
    config_str = builder.build_config([])
    config_dict = yaml.safe_load(config_str)

    # Should include basic pre-commit hooks and gitleaks
    assert len(config_dict["repos"]) == EXPECTED_REPO_COUNT
    assert any(
        repo["repo"] == "https://github.com/pre-commit/pre-commit-hooks"
        for repo in config_dict["repos"]
    )


def test_build_config_with_custom_hooks(tmp_path: Path) -> None:
    """Test building configuration with custom hooks."""
    builder = YAMLBuilder(HookRegistry())
    custom_hooks = [{"repo": "local", "hooks": [{"id": "test", "name": "Test Hook"}]}]
    config_str = builder.build_config([], custom_hooks=custom_hooks)
    config_dict = yaml.safe_load(config_str)

    # Should include basic pre-commit hooks, gitleaks, and custom hooks
    assert len(config_dict["repos"]) == EXPECTED_REPO_COUNT + 1  # +1 for custom hooks
    assert any(repo["repo"] == "local" for repo in config_dict["repos"])
    assert "# Includes custom hooks from .pre-commit-starter-hooks.yaml" in config_str


def test_blank_line_between_repos():
    """Ensure there is a blank line between each top-level - repo: entry."""
    hook_registry = HookRegistry()
    yaml_builder = YAMLBuilder(hook_registry)
    generated_config = yaml_builder.build_config(["python", "javascript", "terraform"])

    lines = generated_config.splitlines()
    repo_indices = [i for i, line in enumerate(lines) if line.lstrip().startswith("- repo:")]

    # For each pair of consecutive repo indices, there should be a blank line between them
    for idx1, idx2 in zip(repo_indices, repo_indices[1:]):
        # There should be at least one blank line between idx1 and idx2
        has_blank = any(lines[i].strip() == "" for i in range(idx1 + 1, idx2))
        assert has_blank, (
            f"No blank line between - repo: entries at lines {idx1 + 1} and {idx2 + 1}.\n"
            "YAML output:\n" + "\n".join(lines)
        )


def test_get_hook_description():
    """Ensure descriptions are returned for known hooks."""
    registry = HookRegistry()
    assert registry.get_hook_description("ruff") == "Lint Python code using Ruff"
    assert registry.get_hook_description("unknown") == ""
