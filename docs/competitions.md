# Kaggle Competitions Commands

Source: https://github.com/Kaggle/kaggle-api/blob/main/docs/competitions.md

Commands for managing and participating in Kaggle competitions.

---

## `kaggle competitions list`

Lists available competitions.

**Usage:**
```bash
kaggle competitions list [options]
```

**Options:**
- `-g, --group <GROUP>`: Filter by group (`general`, `entered`, `inClass`)
- `-c, --category <CATEGORY>`: Filter by category (`all`, `featured`, `research`, `recruitment`, `gettingStarted`, `masters`, `playground`)
- `--sort-by <SORT_BY>`: Sort results (`grouped`, `prize`, `earliestDeadline`, `latestDeadline`, `numberOfTeams`, `recentlyCreated`)
- `-p, --page <PAGE>`: Page number (default: 1)
- `-s, --search <TERM>`: Search term
- `-v, --csv`: Print results in CSV format

**Examples:**
```bash
kaggle competitions list
kaggle competitions list -s "nlp"
kaggle competitions list --category featured --sort-by prize
kaggle competitions list --csv
```

---

## `kaggle competitions files`

Lists data files for a competition.

**Usage:**
```bash
kaggle competitions files -c <COMPETITION> [options]
```

**Options:**
- `-c, --competition <COMPETITION>`: Competition URL suffix (e.g. `titanic`)
- `-v, --csv`: Print in CSV format
- `-q, --quiet`: Suppress output
- `--page-token <TOKEN>`: Page token for paging
- `--page-size <SIZE>`: Number of items per page

**Example:**
```bash
kaggle competitions files -c titanic
```

---

## `kaggle competitions download`

Downloads competition data files.

> **Note**: You must join the competition and accept its rules on kaggle.com before downloading.

**Usage:**
```bash
kaggle competitions download -c <COMPETITION> [options]
```

**Options:**
- `-c, --competition <COMPETITION>`: Competition URL suffix
- `-f, --file <FILE>`: File name to download (omit to download all)
- `-p, --path <PATH>`: Folder to download to (default: current dir)
- `-o, --force`: Force overwrite of existing files
- `-q, --quiet`: Suppress output

**Examples:**
```bash
kaggle competitions download -c titanic
kaggle competitions download -c titanic --unzip
kaggle competitions download -c titanic -f train.csv
kaggle competitions download -c titanic -p ./data -o
```

---

## `kaggle competitions submit`

Submits a file to a competition for scoring.

**Usage:**
```bash
kaggle competitions submit <COMPETITION> -f <FILE> -m <MESSAGE> [options]
```

**Options:**
- `-f, --file <FILE>`: Path to the submission file
- `-m, --message <MESSAGE>`: Submission description (required)
- `-q, --quiet`: Suppress output

**For code competitions (kernel-based submission):**
```bash
kaggle competitions submit <COMPETITION> \
  -k <username>/<notebook-slug> \
  -f <output-filename> \
  -v <notebook-version> \
  -m <message>
```

**Examples:**
```bash
# Standard submission
kaggle competitions submit titanic -f submission.csv -m "first attempt"

# Code competition — submit from a specific notebook version
kaggle competitions submit my-comp \
  -k myuser/my-notebook \
  -f submission.csv \
  -v 3 \
  -m "run 3 with tuned hyperparams"
```

---

## `kaggle competitions submissions`

Lists your previous submissions and their scores.

**Usage:**
```bash
kaggle competitions submissions -c <COMPETITION> [options]
```

**Options:**
- `-c, --competition <COMPETITION>`: Competition URL suffix
- `-v, --csv`: Print in CSV format
- `-q, --quiet`: Suppress output

**Examples:**
```bash
kaggle competitions submissions -c titanic
kaggle competitions submissions -c titanic --csv
```

**Polling submission status (shell):**
```bash
# Submit then poll until complete
kaggle competitions submit titanic -f submission.csv -m "run"
while true; do
  STATUS=$(kaggle competitions submissions -c titanic --csv | awk -F',' 'NR==2{print $3}')
  echo "Status: $STATUS"
  [[ "$STATUS" == "complete" || "$STATUS" == "error" ]] && break
  sleep 30
done
```

---

## `kaggle competitions leaderboard`

Views the competition leaderboard.

**Usage:**
```bash
kaggle competitions leaderboard <COMPETITION> [options]
```

**Options:**
- `-d, --download`: Download leaderboard as CSV
- `-p, --path <PATH>`: Folder to save downloaded leaderboard
- `-v, --csv`: Print in CSV format
- `-q, --quiet`: Suppress output

**Examples:**
```bash
kaggle competitions leaderboard titanic
kaggle competitions leaderboard titanic --download -p ./data
```

---

## `kaggle competitions topics`

Browses discussion topics for a competition.

**Usage:**
```bash
kaggle competitions topics <COMPETITION> [options]
```

**Options:**
- `--sort-by <SORT_BY>`: Sort order (`hot`, `top`, `new`, `recent`, `active`, `relevance`)
- `--page-size <SIZE>`: Items per page
- `--page-token <TOKEN>`: Page token for pagination
- `-s, --search <TERM>`: Search term
- `-v, --csv`: CSV format
- `-q, --quiet`: Suppress output

---

## `kaggle competitions topics show`

Displays a competition discussion topic with all comments in tree form.

**Usage:**
```bash
kaggle competitions topics show <COMPETITION>/<TOPIC_ID>
```

**Example:**
```bash
kaggle competitions topics show titanic/12345
```
