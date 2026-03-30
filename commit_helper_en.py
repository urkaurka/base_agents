#!/usr/bin/env python3
"""
Script per generare automaticamente messaggi di commit in inglese usando GPT-4.1.

Verifica:
1. Se la directory è dentro un repo git
2. Se ci sono file staged
3. Estrae il diff delle modifiche staged
4. Usa GPT-4.1 per generare un messaggio di commit in inglese
5. Effettua il commit
"""

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


class GitCommitHelper:
    """Helper class per gestire git commits con GPT-4.1."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            self._error("❌ OPENAI_API_KEY non trovata. Configura la variabile d'ambiente.")
            sys.exit(1)

        self.client = OpenAI(api_key=self.api_key)
        self.current_dir = Path.cwd()

    def _error(self, msg: str) -> None:
        """Stampa un messaggio di errore."""
        print(msg, file=sys.stderr)

    def _success(self, msg: str) -> None:
        """Stampa un messaggio di successo."""
        print(f"✅ {msg}")

    def _info(self, msg: str) -> None:
        """Stampa un messaggio informativo."""
        print(f"ℹ️ {msg}")

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
        Usa GPT-4.1 per generare un messaggio di commit in inglese.

        Args:
            diff: il diff delle modifiche

        Returns:
            str: il messaggio di commit generato, o None se errore
        """
        diff_truncated, was_truncated = self.truncate_diff(diff)

        if was_truncated:
            self._info("⚠️ Diff troncato per evitare sovraccarico API")

        prompt = f"""
Ti passo il diff di un commit su git:

Proponimi un testo in inglese preciso e dettagliato per il commit composto da una prima riga lunga al massimo 50 caratteri seguita da due caratteri di capo e poi tutto il testo che ritieni necessario in linee lunghe al massimo 80 caratteri.

Cerca di essere esplicito e non dire di leggere il codice per capire o appoggiarsi ad un diff: chi lo legge deve capire a cosa sono servite le modifiche collegate a quel commit e quali nuove features ha ora il codice

DIFF:
```
{diff_truncated}
```

RISPOSTA (SOLO il messaggio di commit, senza spiegazioni aggiuntive):"""

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

            commit_message = response.choices[0].message.content.strip()
            return commit_message

        except Exception as e:
            self._error(f"❌ Errore durante la chiamata a GPT-4.1: {str(e)}")
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
            return False, "Messaggio vuoto"

        # Controlla titolo (prima riga)
        title = lines[0]
        if len(title) > 50:
            return True, f"Titolo troppo lungo: {len(title)} > 50 caratteri"

        if len(title) == 0:
            return False, "Titolo vuoto"

        # Controlla righe del corpo (max 80 caratteri)
        for i, line in enumerate(lines[1:], start=2):
            if len(line) > 80 and line.strip():  # Ignora righe vuote
                return True, f"Riga {i} troppo lunga: {len(line)} > 80 caratteri"

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
                # Estrai l'hash del commit dalla risposta
                output = result.stderr + result.stdout
                self._success(f"Commit eseguito con successo!")
                print(output)
                return True
            else:
                self._error(f"❌ Errore durante il commit: {result.stderr}")
                return False

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self._error(f"❌ Errore durante l'esecuzione di git commit: {str(e)}")
            return False

    def run(self) -> int:
        """
        Executa la procedura completa di commit.

        Returns:
            int: codice di uscita (0 = successo, 1 = errore)
        """
        print("🚀 Git Auto-Commit Helper (GPT-4.1)")
        print("-" * 50)

        # Step 1: Verifica repo git
        self._info("Verificando se siamo in un repo git...")
        if not self.is_git_repo():
            self._error("❌ Non siamo in un repo git valido!")
            return 1
        self._success("Siamo in un repo git valido")

        # Step 2: Verifica file staged
        self._info("Verificando file staged...")
        success, staged_files = self.get_staged_files()
        if not success:
            self._error("❌ Errore nel recupero dei file staged")
            return 1

        if not staged_files:
            self._error("❌ Nessun file staged. Usa 'git add' prima di eseguire questo script.")
            return 1

        self._success(f"Trovati {len(staged_files)} file staged:")
        for file in staged_files:
            if file:  # Ignora stringhe vuote
                print(f"  - {file}")

        # Step 3: Estrai diff
        self._info("Estraendo diff...")
        diff = self.get_diff()
        if not diff:
            self._error("❌ Errore nel recupero del diff")
            return 1
        self._success(f"Diff estratto ({len(diff)} caratteri)")

        # Step 4: Genera messaggio con GPT-4.1
        self._info("Generando messaggio di commit con GPT-4.1...")
        commit_message = self.generate_commit_message(diff)
        if not commit_message:
            self._error("❌ Errore nella generazione del messaggio di commit")
            return 1

        # Step 5: Valida messaggio
        self._info("Validando messaggio di commit...")
        is_valid, error_msg = self.validate_commit_message(commit_message)
        if not is_valid:
            self._error(f"❌ Messaggio di commit non valido: {error_msg}")
            print(f"\nMessaggio generato:\n{commit_message}")
            return 1
        self._success("Messaggio valido!")

        # Step 6: Mostra messaggio e chiedi conferma
        print("\n" + "=" * 50)
        print("MESSAGGIO DI COMMIT GENERATO:")
        print("=" * 50)
        print(commit_message)
        print("=" * 50 + "\n")

        # Step 7: Esegui commit
        if self.make_commit(commit_message):
            return 0
        else:
            return 1


def main():
    """Entry point dello script."""
    helper = GitCommitHelper()
    exit_code = helper.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
