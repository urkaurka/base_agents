"""Localized messages for commit helper (EN + IT)."""

MESSAGES = {
    "en": {
        "import_error": "❌ Errore: openai library non installata. Installa con: pip install openai",
        "api_key_missing": "❌ OPENAI_API_KEY non trovata. Configura la variabile d'ambiente.",
        "diff_truncated": "⚠️ Diff troncato per evitare sovraccarico API",
        "prompt_instruction": """Ti passo il diff di un commit su git:

Proponimi un testo in inglese preciso e dettagliato per il commit composto da una prima riga lunga al massimo 50 caratteri seguita da due caratteri di capo e poi tutto il testo che ritieni necessario in linee lunghe al massimo 80 caratteri.

Cerca di essere esplicito e non dire di leggere il codice per capire o appoggiarsi ad un diff: chi lo legge deve capire a cosa sono servite le modifiche collegate a quel commit e quali nuove features ha ora il codice

DIFF:
```
{diff}
```

RISPOSTA (SOLO il messaggio di commit, senza spiegazioni aggiuntive):""",
        "api_error": "❌ Errore durante la chiamata a GPT-4.1: {error}",
        "empty_message": "Messaggio vuoto",
        "title_too_long": "Titolo troppo lungo: {length} > 50 caratteri",
        "empty_title": "Titolo vuoto",
        "line_too_long": "Riga {line_num} troppo lunga: {length} > 80 caratteri",
        "header": "🚀 Git Auto-Commit Helper (GPT-4.1)",
        "separator": "-" * 50,
        "checking_git_repo": "ℹ️ Verificando se siamo in un repo git...",
        "git_repo_invalid": "❌ Non siamo in un repo git valido!",
        "git_repo_valid": "✅ Siamo in un repo git valido",
        "checking_staged": "ℹ️ Verificando file staged...",
        "error_staged_fetch": "❌ Errore nel recupero dei file staged",
        "no_staged_files": "❌ Nessun file staged. Usa 'git add' prima di eseguire questo script.",
        "found_staged_files": "✅ Trovati {count} file staged:",
        "extracting_diff": "ℹ️ Estraendo diff...",
        "error_diff_fetch": "❌ Errore nel recupero del diff",
        "diff_extracted": "✅ Diff estratto ({length} caratteri)",
        "generating_message": "ℹ️ Generando messaggio di commit con GPT-4.1...",
        "error_generation": "❌ Errore nella generazione del messaggio di commit",
        "validating_message": "ℹ️ Validando messaggio di commit...",
        "invalid_message": "❌ Messaggio di commit non valido: {error}",
        "message_generated_label": "Messaggio generato:",
        "message_valid": "✅ Messaggio valido!",
        "commit_header": "MESSAGGIO DI COMMIT GENERATO:",
        "commit_separator": "=" * 50,
        "commit_success": "✅ Commit eseguito con successo!",
        "commit_error": "❌ Errore durante il commit: {error}",
        "commit_exec_error": "❌ Errore durante l'esecuzione di git commit: {error}",
    },
    "it": {
        "import_error": "❌ Errore: openai library non installata. Installa con: pip install openai",
        "api_key_missing": "❌ OPENAI_API_KEY non trovata. Configura la variabile d'ambiente.",
        "diff_truncated": "⚠️ Diff troncato per evitare sovraccarico API",
        "prompt_instruction": """Ti passo il diff di un commit su git:

Proponimi un testo in italiano preciso e dettagliato per il commit composto da una prima riga lunga al massimo 50 caratteri seguita da due caratteri di capo e poi tutto il testo che ritieni necessario in linee lunghe al massimo 80 caratteri.

Cerca di essere esplicito e non dire di leggere il codice per capire o appoggiarsi ad un diff: chi lo legge deve capire a cosa sono servite le modifiche collegate a quel commit e quali nuove features ha ora il codice

DIFF:
```
{diff}
```

RISPOSTA (SOLO il messaggio di commit, senza spiegazioni aggiuntive):""",
        "api_error": "❌ Errore durante la chiamata a GPT-4.1: {error}",
        "empty_message": "Messaggio vuoto",
        "title_too_long": "Titolo troppo lungo: {length} > 50 caratteri",
        "empty_title": "Titolo vuoto",
        "line_too_long": "Riga {line_num} troppo lunga: {length} > 80 caratteri",
        "header": "🚀 Git Auto-Commit Helper (GPT-4.1)",
        "separator": "-" * 50,
        "checking_git_repo": "ℹ️ Verificando se siamo in un repo git...",
        "git_repo_invalid": "❌ Non siamo in un repo git valido!",
        "git_repo_valid": "✅ Siamo in un repo git valido",
        "checking_staged": "ℹ️ Verificando file staged...",
        "error_staged_fetch": "❌ Errore nel recupero dei file staged",
        "no_staged_files": "❌ Nessun file staged. Usa 'git add' prima di eseguire questo script.",
        "found_staged_files": "✅ Trovati {count} file staged:",
        "extracting_diff": "ℹ️ Estraendo diff...",
        "error_diff_fetch": "❌ Errore nel recupero del diff",
        "diff_extracted": "✅ Diff estratto ({length} caratteri)",
        "generating_message": "ℹ️ Generando messaggio di commit con GPT-4.1...",
        "error_generation": "❌ Errore nella generazione del messaggio di commit",
        "validating_message": "ℹ️ Validando messaggio di commit...",
        "invalid_message": "❌ Messaggio di commit non valido: {error}",
        "message_generated_label": "Messaggio generato:",
        "message_valid": "✅ Messaggio valido!",
        "commit_header": "MESSAGGIO DI COMMIT GENERATO:",
        "commit_separator": "=" * 50,
        "commit_success": "✅ Commit eseguito con successo!",
        "commit_error": "❌ Errore durante il commit: {error}",
        "commit_exec_error": "❌ Errore durante l'esecuzione di git commit: {error}",
    },
}


def get_messages(language: str) -> dict:
    """Get messages for a specific language."""
    if language not in MESSAGES:
        raise ValueError(f"Unsupported language: {language}. Supported: {', '.join(MESSAGES.keys())}")
    return MESSAGES[language]
