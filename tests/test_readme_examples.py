import subprocess
import os

import pytest
from markdown_it import MarkdownIt


# Helper function to group python code blocks by markdown heading using markdown-it-py
def get_readme_code_groups_markdown_it(markdown_content: str):
    md = MarkdownIt()
    tokens = md.parse(markdown_content)

    groups = []
    current_heading_text = "Top Level (before first heading)"
    current_blocks_for_heading = []

    def finalize_current_heading_group():
        nonlocal current_blocks_for_heading, current_heading_text
        if current_blocks_for_heading:
            merged_code = "\n\n".join(current_blocks_for_heading).strip()
            if merged_code:  # Only add if there's actual code
                groups.append({"heading": current_heading_text, "code": merged_code})
        current_blocks_for_heading = []

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token.type == "heading_open":
            # Finalize blocks for the PREVIOUS heading
            finalize_current_heading_group()

            # Extract heading text
            i += 1
            current_heading_text = "Unnamed Heading"  # Default
            if i < len(tokens) and tokens[i].type == "inline":
                inline_token_children = tokens[i].children
                if inline_token_children:  # Explicitly check for None
                    current_heading_text = "".join(
                        t.content for t in inline_token_children if t.type == "text"
                    ).strip()

            # Skip to heading_close
            while i < len(tokens) and tokens[i].type != "heading_close":
                i += 1

        elif token.type == "fence" and token.info.strip().lower() == "python":
            if token.content:
                current_blocks_for_heading.append(token.content.strip())

        i += 1

    # Finalize the very last group of blocks
    finalize_current_heading_group()

    return groups


# Test to run readme examples
def test_readme_examples(capsys):
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            readme_content = f.read()
    except FileNotFoundError:
        pytest.skip("README.md not found.")

    code_groups = get_readme_code_groups_markdown_it(readme_content)

    if not code_groups:
        pytest.skip(
            "No Python code groups found in README.md by markdown-it-py parser."
        )

    all_tests_passed = True
    for i, group in enumerate(code_groups):
        if not group["code"].strip():
            print(f"Skipping empty code group under heading: {group['heading']}")
            continue

        print(f"Testing code group under heading: {group['heading']}")

        try:
            current_env = os.environ.copy()
            project_root = os.getcwd()

            # Prepend project root to PYTHONPATH for the subprocess
            existing_pythonpath = current_env.get("PYTHONPATH", "")
            if existing_pythonpath:
                current_env["PYTHONPATH"] = (
                    project_root + os.pathsep + existing_pythonpath
                )
            else:
                current_env["PYTHONPATH"] = project_root

            process = subprocess.run(
                ["python", "-c", group["code"]],
                capture_output=True,
                text=True,
                check=False,  # We'll check manually to provide better error messages
                cwd=".",
                env=current_env,  # Use the modified environment
            )
            if process.returncode != 0:
                all_tests_passed = False
                pytest.fail(
                    f"README.md code under heading '{group['heading']}' "
                    f"(group {i}) failed:\n"
                    f"Return Code: {process.returncode}\n"
                    f"Code:\n{group['code']}\n"
                    f"Stdout:\n{process.stdout}\n"
                    f"Stderr:\n{process.stderr}"
                )

        except FileNotFoundError:
            all_tests_passed = False
            pytest.fail("Python interpreter not found. Ensure python is in your PATH.")
        except Exception as e:
            all_tests_passed = False
            pytest.fail(
                f"An unexpected error occurred while testing code group "
                f"'{group['heading']}' (group {i}):\n"
                f"Error: {e}\n"
                f"Code:\n{group['code']}"
            )

    assert all_tests_passed, "One or more README example code blocks failed."
