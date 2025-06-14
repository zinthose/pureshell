import re
import subprocess

import pytest


# Helper function to extract python code blocks from markdown
def extract_python_code_blocks(markdown_content):
    code_blocks = re.findall(r"```python\n(.*?)\n```", markdown_content, re.DOTALL)
    return code_blocks


# Helper function to group python code blocks by markdown heading
def group_code_blocks_by_heading(markdown_content: str):
    groups = []
    current_heading_text = "Top Level (before first heading)"
    # Stores individual code blocks for the current heading
    current_blocks_for_heading = []

    lines = markdown_content.splitlines()
    in_python_code_block = False
    current_block_lines = []

    def finalize_current_heading_group():
        nonlocal current_blocks_for_heading, current_heading_text
        if current_blocks_for_heading:
            merged_code = "\\n\\n".join(current_blocks_for_heading)
            groups.append({"heading": current_heading_text, "code": merged_code})
        current_blocks_for_heading = []

    for line in lines:
        if line.startswith("#"):  # New heading
            if in_python_code_block:
                # Current block is terminated by a new heading
                current_blocks_for_heading.append("\\n".join(current_block_lines))
                current_block_lines = []
                in_python_code_block = False

            finalize_current_heading_group()  # Finalize blocks for the PREVIOUS heading
            current_heading_text = line.strip()
            continue

        if line.strip() == "```python":
            # A ```python inside another, treat as end of prior
            if in_python_code_block:
                current_blocks_for_heading.append("\\n".join(current_block_lines))
                # current_block_lines are reset below

            in_python_code_block = True
            current_block_lines = []  # Reset for the new block
            continue

        if line.strip() == "```" and in_python_code_block:
            # Normal end of a python code block
            current_blocks_for_heading.append("\\n".join(current_block_lines))
            current_block_lines = []
            in_python_code_block = False
            continue

        if in_python_code_block:
            current_block_lines.append(line)

    # After loop, handle any unterminated block
    if in_python_code_block:
        current_blocks_for_heading.append("\\n".join(current_block_lines))

    # Finalize the very last group of blocks
    finalize_current_heading_group()

    return groups


# Test to run readme examples
def test_readme_examples(capsys):
    with open("README.md", "r", encoding="utf-8") as f:
        readme_content = f.read()

    code_groups = group_code_blocks_by_heading(readme_content)

    if not code_groups:
        pytest.skip("No code groups found in README.md")

    for i, group in enumerate(code_groups):
        if not group["code"].strip():  # Skip if no actual code in this group
            print(f"Skipping empty code group under heading: {group['heading']}")
            continue

        print(f"Testing code group under heading: {group['heading']}")

        try:
            subprocess.run(
                ["python", "-c", group["code"]],
                capture_output=True,
                text=True,
                check=True,
                cwd=".",  # Run from project root
            )
        except subprocess.CalledProcessError as e:
            pytest.fail(
                f"README.md code under heading '{group['heading']}' "
                f"(group {i}) failed:\n"
                f"Code:\n{group['code']}\n"
                f"Error:\n{e.stderr}"
            )
        except FileNotFoundError:
            pytest.fail("Python interpreter not found. Ensure python is in your PATH.")
