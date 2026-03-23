# Git Auto-Commit Helper (GPT-4.1)

Script Python che genera automaticamente messaggi di commit in italiano usando GPT-4.1.

## Features

✅ Verifica che siamo in un repo git valido  
✅ Controlla che ci sono file staged  
✅ Estrae il diff delle modifiche  
✅ Usa GPT-4.1 (OpenAI) per generare il messaggio in italiano  
✅ Valida il formato del messaggio (titolo max 50 caracteri, righe max 80)  
✅ Esegue il commit automaticamente  

## Prerequisites

- Python 3.8+
- Git installato e configurato
- Chiave API OpenAI disponibile come variabile d'ambiente `OPENAI_API_KEY`

## Installation

```bash
# 1. Nella directory del workspace
pip install openai

# 2. Rendi lo script eseguibile
chmod +x commit_helper.py

# 3. Configura la chiave API (se non già fatto)
export OPENAI_API_KEY="sk-your-api-key-here"
```

## Usage

### Via CLI diretta

```bash
# Naviga nella directory del tuo repo git
cd /path/to/your/repo

# Prepara i file da committare
git add file1.txt file2.py

# Esegui lo script
python /path/to/commit_helper.py
```

### Via shebang (se reso eseguibile)

```bash
cd /path/to/your/repo
git add .
/path/to/commit_helper.py
```

## How it works

1. **Validazione Git**: Verifica che siamo in un repository git valido
2. **Controllo Staged Files**: Verifica che ci sono file staged (altrimenti esce con errore)
3. **Estrazione Diff**: Recupera il diff completo delle modifiche staged
4. **Generazione Messaggio**: Passa il diff a GPT-4.1 che genera un messaggio di commit in italiano
5. **Validazione**: Verifica che il messaggio segua le regole:
   - Titolo: max 50 caratteri
   - Corpo: righe max 80 caratteri
6. **Commit**: Esegue `git commit` con il messaggio generato

## Examples

### Esempio 1: Nuovo file

```bash
$ echo "import sys" > app.py
$ git add app.py
$ ./commit_helper.py

🚀 Git Auto-Commit Helper (GPT-4.1)
--------------------------------------------------
ℹ️ Verificando se siamo in un repo git...
✅ Siamo in un repo git valido
ℹ️ Verificando file staged...
✅ Trovati 1 file staged:
  - app.py
ℹ️ Estraendo diff...
✅ Diff estratto (45 caratteri)
ℹ️ Generando messaggio di commit con GPT-4.1...
ℹ️ Validando messaggio di commit...
✅ Messaggio valido!

==================================================
MESSAGGIO DI COMMIT GENERATO:
==================================================
Aggiunto file app.py con modulo principale

Nuovo file con struttura base per l'applicazione.
==================================================

✅ Commit eseguito con successo!
[main abc1234] Aggiunto file app.py con modulo principale
 1 file changed, 1 insertion(+)
 create mode 100644 app.py
```

### Esempio 2: Modifica file

```bash
$ echo "print('hello')" >> app.py
$ git add app.py
$ ./commit_helper.py

[Genera messaggio come "Aggiunto print statement in app.py"]
[Esegue il commit]
```

## Error Handling

Lo script esce con codice di errore `1` se:

- ❌ Non siamo in un repository git valido
- ❌ Non ci sono file staged
- ❌ Il diff non può essere recuperato
- ❌ Non è possibile contattare GPT-4.1
- ❌ Il messaggio generato non valida le constraints (titolo, lunghezza righe)

## Environment Variables

### Obbligatorio

- `OPENAI_API_KEY` — Chiave API OpenAI (da https://platform.openai.com/api-keys)

### Opzionale

- `OPENAI_MODEL` — Modello da usare (default: `gpt-4-turbo`)

## Limitations

- Il diff è limitato a 2000 caratteri per evitare sovraccarico dell'API
- Se il diff è troppo lungo, viene troncato con un messaggio di avviso
- La generazione del messaggio dipende dalla qualità di GPT-4.1
- Ogni commit utilizza crediti dalla tua account OpenAI

## Troubleshooting

### Errore: "OPENAI_API_KEY non trovata"

```bash
# Soluzione: Configura la chiave API
export OPENAI_API_KEY="sk-your-api-key-here"

# Oppure add al .bashrc per rendere permanente
echo 'export OPENAI_API_KEY="sk-your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### Errore: "Non siamo in un repo git valido!"

```bash
# Soluzione: Naviga a un repo git valido o initializza uno nuovo
cd /path/to/repo
# oppure
git init
git config user.email "your@email.com"
git config user.name "Your Name"
```

### Errore: "Nessun file staged"

```bash
# Soluzione: Aggiungi i file con git add
git add .
# oppure per file specifici
git add file1.txt file2.py
```

## License

MIT

## Notes

- Lo script è compatibile con Linux, macOS e Windows (WSL)
- Ogni commit consuma crediti dall'account OpenAI
- Monitora l'utilizzo API da https://platform.openai.com/account/usage
