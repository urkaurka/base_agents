#!/usr/bin/env python3
"""
Script per generare automaticamente messaggi di commit usando GPT-4.1.

Verifica:
1. Se la directory è dentro un repo git
2. Se ci sono file staged
3. Estrae il diff delle modifiche staged
4. Usa GPT-4.1 per generare un messaggio di commit (lingua configurabile)
5. Effettua il commit
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Tuple

try:
    from openai import OpenAI
except ImportError:
    print("❌ Errore: openai library non installata. Installa con: pip install openai")
    sys.exit(1)

from ut_locales import get_messages


class GitCommitHelper:
    """Helper class per gestire git commits con GPT-4.1."""

    def __init__(self, language: str = "it"):
        self.language = language
        self.messages = get_messages(language)

        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            self._error(self.messages["api_key_missing"])
            sys.exit(1)

        self.client = OpenAI(api_key=self.api_key)
        self.current_dir = Path.cwd()

    def _error(self, msg: str) -> None:
        """Stampa un messaggio di errore."""
        print(msg, file=sys.stderr)

    def _success(self, msg: str) -> None:
        """Stampa un messaggio di successo."""
        print(msg)

    def _info(self, msg: str) -> None:
        """Stampa un messaggio informativo."""
        print(msg)

    def is_git_repo(self) -> bool:
        """Verifica se la directory attuale è dentro un repo git."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.current_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def get_staged_files(self) -> Tuple[bool, list]:
        """
        Recupera la lista dei file staged.

        Returns:
            Tuple[bool, list]: (success, list_of_files)
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=self.current_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                files = result.stdout.strip().split("\n") if result.stdout.strip() else []
                return True, files
            return False, []
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False, []

    def get_diff(self) -> Optional[str]:
        """
        Recupera il diff dei file staged.

        Returns:
            str: il diff completo, o None se errore
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--cached"],
                cwd=self.current_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout
            return None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def truncate_diff(self, diff: str, max_length: int = 20_000) -> Tuple[str, bool]:
        """
        Tronca il diff se troppo lungo.

        Args:
            diff: il diff completo
            max_length: lunghezza massima

        Returns:
            Tuple[str, bool]: (diff_troncato, is_truncated)
        """
        if len(diff) > max_length:
            return diff[:max_length] + "\n... [TRUNCATED] ...", True
        return diff, False

    def generate_commit_message(self, diff: str) -> Optional[str]:
        """
        Usa GPT-4.1 per generare un messaggio di commit.

        Args:
            diff: il diff delle modifiche

        Returns:
            str: il messaggio di commit generato, o None se errore
        """
        diff_truncated, was_truncated = self.truncate_diff(diff)

        if was_truncated:
            self._info(self.messages["diff_truncated"])

        prompt = self.messages["prompt_instruction"].format(diff=diff_truncated)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            content = response.choices[0].message.content
            if not content:
                self._error(self.messages["api_error"].format(error="Empty response from API"))
                return None
            return content.strip()

        except Exception as e:
            self._error(self.messages["api_error"].format(error=str(e)))
            return None

    def validate_commit_message(self, message: str) -> Tuple[bool, str]:
        """
        Valida il messaggio di commit.

        Args:
            message: il messaggio da validare

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        lines = message.split("\n")

        if not lines:
            return False, self.messages["empty_message"]

        # Controlla titolo (prima riga)
        title = lines[0]
        if len(title) > 50:
            return True, self.messages["title_too_long"].format(length=len(title))

        if len(title) == 0:
            return False, self.messages["empty_title"]

        # Controlla righe del corpo (max 80 caratteri)
        for i, line in enumerate(lines[1:], start=2):
            if len(line) > 80 and line.strip():  # Ignora righe vuote
                return True, self.messages["line_too_long"].format(line_num=i, length=len(line))

        return True, ""

    def make_commit(self, message: str) -> bool:
        """
        Esegue il commit con il messaggio fornito.

        Args:
            message: il messaggio di commit

        Returns:
            bool: True se il commit ha successo, False altrimenti
        """
        try:
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.current_dir,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                output = result.stderr + result.stdout
                self._success(self.messages["commit_success"])
                print(output)
                return True
            else:
                self._error(self.messages["commit_error"].format(error=result.stderr))
                return False

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self._error(self.messages["commit_exec_error"].format(error=str(e)))
            return False

    def run(self) -> int:
        """
        Executa la procedura completa di commit.

        Returns:
            int: codice di uscita (0 = successo, 1 = errore)
        """
        print(self.messages["header"])
        print(self.messages["separator"])

        # Step 1: Verifica repo git
        self._info(self.messages["checking_git_repo"])
        if not self.is_git_repo():
            self._error(self.messages["git_repo_invalid"])
            return 1
        self._success(self.messages["git_repo_valid"])

        # Step 2: Verifica file staged
        self._info(self.messages["checking_staged"])
        success, staged_files = self.get_staged_files()
        if not success:
            self._error(self.messages["error_staged_fetch"])
            return 1

        if not staged_files:
            self._error(self.messages["no_staged_files"])
            return 1

        self._success(self.messages["found_staged_files"].format(count=len(staged_files)))
        for file in staged_files:
            if file:  # Ignora stringhe vuote
                print(f"  - {file}")

        # Step 3: Estrai diff
        self._info(self.messages["extracting_diff"])
        diff = self.get_diff()
        if not diff:
            self._error(self.messages["error_diff_fetch"])
            return 1
        self._success(self.messages["diff_extracted"].format(length=len(diff)))

        # Step 4: Genera messaggio con GPT-4.1
        self._info(self.messages["generating_message"])
        commit_message = self.generate_commit_message(diff)
        if not commit_message:
            self._error(self.messages["error_generation"])
            return 1

        # Step 5: Valida messaggio
        self._info(self.messages["validating_message"])
        is_valid, error_msg = self.validate_commit_message(commit_message)
        if not is_valid:
            self._error(self.messages["invalid_message"].format(error=error_msg))
            print(f"\n{self.messages['message_generated_label']}\n{commit_message}")
            return 1
        self._success(self.messages["message_valid"])

        # Step 6: Mostra messaggio
        print("\n" + self.messages["commit_separator"])
        print(self.messages["commit_header"])
        print(self.messages["commit_separator"])
        print(commit_message)
        print(self.messages["commit_separator"] + "\n")

        # Step 7: Esegui commit
        if self.make_commit(commit_message):
            return 0
        else:
            return 1


def main() -> None:
    """Entry point dello script."""
    parser = argparse.ArgumentParser(
        description="Generate commit messages automatically using GPT-4.1"
    )
    parser.add_argument(
        "--lang",
        choices=["en", "it"],
        default="it",
        help="Language for commit message (default: it)"
    )
    args = parser.parse_args()

    helper = GitCommitHelper(language=args.lang)
    exit_code = helper.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
