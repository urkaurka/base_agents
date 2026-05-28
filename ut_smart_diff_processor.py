#!/usr/bin/env python3
"""
Smart diff processor: applies intelligent truncation strategies.
- Strategy 1: Context-aware truncation based on file size
- Strategy 2: Budget-aware prioritization for very large diffs
"""

import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional


@dataclass
class FileChange:
    path: str
    status: str  # M (modified), A (added), D (deleted)
    lines_added: int
    lines_removed: int
    content: list[str]  # The actual diff lines

    @property
    def total_lines(self) -> int:
        return self.lines_added + self.lines_removed

    @property
    def priority(self) -> int:
        """Priority for budget allocation (lower = higher priority)"""
        # M > A > D; more changes = higher priority
        status_priority = {"M": 0, "A": 1, "D": 2}
        return status_priority.get(self.status, 3) * 1000 + self.total_lines


class DiffParser:
    """Parse git diff output into structured file changes"""

    def __init__(self, diff_text: str):
        self.diff_text = diff_text
        self.files: list[FileChange] = []
        self.parse()

    def parse(self) -> None:
        """Parse the diff into FileChange objects"""
        lines = self.diff_text.split('\n')
        current_file: Optional[FileChange] = None
        added = removed = 0

        i = 0
        while i < len(lines):
            line = lines[i]

            # Detect file header: diff --git a/path b/path
            if line.startswith('diff --git'):
                # Save previous file if exists
                if current_file:
                    current_file.lines_added = added
                    current_file.lines_removed = removed
                    self.files.append(current_file)

                # Parse new file
                match = re.match(r'diff --git a/(.*) b/\1', line)
                path = match.group(1) if match else ''
                # Determine status from next line
                i += 1
                status = 'M'
                if i < len(lines):
                    if lines[i].startswith('new file'):
                        status = 'A'
                    elif lines[i].startswith('deleted file'):
                        status = 'D'

                current_file = FileChange(
                    path=path,
                    status=status,
                    lines_added=0,
                    lines_removed=0,
                    content=[]
                )
                added = removed = 0

            # Count additions/deletions and store content
            if current_file:
                if line.startswith('+') and not line.startswith('+++'):
                    added += 1
                    current_file.content.append(line)
                elif line.startswith('-') and not line.startswith('---'):
                    removed += 1
                    current_file.content.append(line)
                elif line.startswith('@@'):
                    current_file.content.append(line)
                elif not line.startswith('diff --git'):
                    current_file.content.append(line)

            i += 1

        # Save last file
        if current_file:
            current_file.lines_added = added
            current_file.lines_removed = removed
            self.files.append(current_file)


class DiffTruncator:
    """Apply intelligent truncation strategies"""

    # Strategy 1 thresholds (lines of change)
    SMALL_FILE_THRESHOLD = 300
    MEDIUM_FILE_THRESHOLD = 1500

    # Context windows
    SMALL_CONTEXT = 100
    LARGE_CONTEXT = 10

    # Strategy 2: token budget
    TOKEN_BUDGET = 30000  # Conservative estimate for Claude's context
    OVERHEAD_TOKENS = 5000  # Reserved for prompt + other context

    def __init__(self, files: list[FileChange]):
        self.files = files

    def truncate_all(self) -> dict:
        """Apply truncation strategies and return summary"""
        # First pass: Strategy 1 (context-aware)
        truncated_files = []
        total_tokens = 0

        for file in self.files:
            truncated, tokens = self.truncate_file(file)
            truncated_files.append((file, truncated, tokens))
            total_tokens += tokens

        # Second pass: Strategy 2 (budget-aware) if needed
        if total_tokens > self.TOKEN_BUDGET - self.OVERHEAD_TOKENS:
            truncated_files = self.apply_budget_strategy(truncated_files)

        return {
            'files': truncated_files,
            'total_tokens': total_tokens,
            'truncated': total_tokens > self.TOKEN_BUDGET - self.OVERHEAD_TOKENS,
        }

    def truncate_file(self, file: FileChange) -> tuple[str, int]:
        """Apply Strategy 1: context-aware truncation"""
        total_lines = file.total_lines

        if total_lines < self.SMALL_FILE_THRESHOLD:
            # Show everything
            content = '\n'.join(file.content)
            return content, self.estimate_tokens(content)

        elif total_lines < self.MEDIUM_FILE_THRESHOLD:
            # Show beginning + end with omission
            lines = file.content
            mid_start = self.SMALL_CONTEXT
            mid_end = len(lines) - self.SMALL_CONTEXT

            if mid_end <= mid_start:
                # File is small enough to show completely
                content = '\n'.join(lines)
            else:
                omitted = mid_end - mid_start
                beginning = '\n'.join(lines[:mid_start])
                end = '\n'.join(lines[mid_end:])
                content = f"{beginning}\n\n... ({omitted} lines omitted) ...\n\n{end}"

            return content, self.estimate_tokens(content)

        else:
            # Show only chunks with context
            content = self.extract_chunks(file)
            return content, self.estimate_tokens(content)

    def extract_chunks(self, file: FileChange) -> str:
        """Extract only meaningful chunks for very large files"""
        lines = file.content
        chunks = []
        context_size = self.LARGE_CONTEXT

        # Find lines with actual changes (+ or -)
        i = 0
        while i < len(lines):
            if lines[i].startswith(('+', '-')) and not lines[i].startswith(('+++', '---')):
                # Found a change, extract chunk around it
                start = max(0, i - context_size)
                end = min(len(lines), i + context_size + 1)

                chunk = lines[start:end]
                chunks.append('\n'.join(chunk))

                i = end
            else:
                i += 1

        if not chunks:
            # No changes found (shouldn't happen), return first part
            return '\n'.join(lines[:100])

        return '\n\n... (chunk separator) ...\n\n'.join(chunks)

    def apply_budget_strategy(self, truncated_files) -> list:
        """Strategy 2: Prioritize files by importance when budget is exceeded"""
        # Sort by priority (M > A > D, more lines = higher priority)
        indexed = [(i, file, trunc, tokens) for i, (file, trunc, tokens) in enumerate(truncated_files)]
        indexed.sort(key=lambda x: x[1].priority, reverse=True)

        available_budget = self.TOKEN_BUDGET - self.OVERHEAD_TOKENS
        allocated = 0
        result = []

        for i, file, trunc, file_tokens in indexed:
            if allocated + file_tokens < available_budget:
                # Allocate full context
                result.append((i, file, trunc, file_tokens))
                allocated += file_tokens
            else:
                # Use summary/minimal version
                summary = f"File: {file.path} ({file.status}) - {file.total_lines} lines changed"
                summary_tokens = self.estimate_tokens(summary)
                result.append((i, file, summary, summary_tokens))
                allocated += summary_tokens

        # Restore original order
        result.sort(key=lambda x: x[0])
        return [(file, trunc, tok) for _, file, trunc, tok in result]

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough token estimate: ~4 chars per token"""
        return len(text) // 4

    @staticmethod
    def format_output(truncated_files: list, total_tokens: int, was_truncated: bool) -> str:
        """Format the processed diff for output"""
        output_lines = []

        if was_truncated:
            output_lines.append(
                "# ⚠️  Smart Diff Processing Applied (Token Budget Exceeded)\n"
            )
            output_lines.append(
                f"Total tokens used: ~{total_tokens} (budget: {DiffTruncator.TOKEN_BUDGET})\n"
            )
            output_lines.append("---\n")

        for file, truncated_content, _ in truncated_files:
            output_lines.append(f"\n## File: {file.path} ({file.status})")
            output_lines.append(f"Changes: +{file.lines_added} -{file.lines_removed}\n")
            output_lines.append(truncated_content)
            output_lines.append("\n---\n")

        return '\n'.join(output_lines)


def get_git_diff(cached: bool = False) -> str:
    """Get the current git diff (staged if cached=True, unstaged otherwise)"""
    try:
        cmd = ['git', 'diff']
        if cached:
            cmd.append('--cached')
        cmd.append('--no-ext-diff')

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout
    except FileNotFoundError:
        print("Error: git not found", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    # Get diff (staged first, then unstaged)
    diff_text = get_git_diff(cached=True)
    if not diff_text:
        diff_text = get_git_diff(cached=False)

    if not diff_text:
        print("No changes in working tree")
        return

    # Parse and truncate
    parser = DiffParser(diff_text)
    truncator = DiffTruncator(parser.files)
    result = truncator.truncate_all()

    # Output
    output = truncator.format_output(
        result['files'],
        result['total_tokens'],
        result['truncated']
    )
    print(output)


if __name__ == '__main__':
    main()
