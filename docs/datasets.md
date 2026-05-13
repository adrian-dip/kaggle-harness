# Kaggle Datasets Commands

Source: https://github.com/Kaggle/kaggle-api/blob/main/docs/datasets.md

Commands for searching, downloading, and managing Kaggle datasets.

---

## `kaggle datasets list`

Discovers available datasets.

**Usage:**
```bash
kaggle datasets list [options]
```

**Options:**
- `--sort-by <SORT_BY>`: Sort order (`hottest`, `votes`, `updated`, `active`, `published`)
- `--size <SIZE>`: Filter by size (`all`, `small`, `medium`, `large`)
- `--file-type <TYPE>`: Filter by file type (`all`, `csv`, `sqlite`, `json`, `bigQuery`)
- `--license <LICENSE>`: Filter by license (`all`, `cc`, `gpl`, `odb`, `other`)
- `--tags <TAGS>`: Comma-separated tag IDs
- `-s, --search <TERM>`: Search term
- `--user <USER>`: Filter by user/org
- `--mine`: Show only your datasets
- `-p, --page <PAGE>`: Page number (default: 1)
- `--max-size <BYTES>`: Max size in bytes
- `--min-size <BYTES>`: Min size in bytes
- `-v, --csv`: Print in CSV format

**Examples:**
```bash
kaggle datasets list
kaggle datasets list -s iris
kaggle datasets list --mine
kaggle datasets list --file-type csv --sort-by votes
```

---

## `kaggle datasets files`

Lists files within a specific dataset.

**Usage:**
```bash
kaggle datasets files -d <DATASET> [options]
```

**Options:**
- `-d, --dataset <DATASET>`: Dataset URL suffix (`owner/dataset-slug`)
- `-v, --csv`: Print in CSV format
- `--page-token <TOKEN>`: Page token
- `--page-size <SIZE>`: Items per page

**Example:**
```bash
kaggle datasets files -d uciml/iris
```

---

## `kaggle datasets download`

Downloads dataset files.

**Usage:**
```bash
kaggle datasets download -d <DATASET> [options]
```

**Options:**
- `-d, --dataset <DATASET>`: Dataset URL suffix (`owner/dataset-slug`)
- `-f, --file <FILE>`: Specific file to download (omit for all)
- `-p, --path <PATH>`: Download destination folder
- `--unzip`: Automatically unzip after download
- `-o, --force`: Overwrite existing files
- `-q, --quiet`: Suppress output

**Examples:**
```bash
kaggle datasets download -d uciml/iris
kaggle datasets download -d uciml/iris --unzip
kaggle datasets download -d uciml/iris -f Iris.csv
kaggle datasets download -d uciml/iris -p ./data --unzip -o
```

---

## `kaggle datasets init`

Generates a `dataset-metadata.json` template for creating a new dataset.

**Usage:**
```bash
kaggle datasets init [-p <FOLDER_PATH>]
```

**Options:**
- `-p, --path <FOLDER_PATH>`: Folder to create the metadata file (default: current dir)

**Example:**
```bash
cd my-new-dataset
kaggle datasets init
# Edit dataset-metadata.json, then:
kaggle datasets create -p .
```

---

## `kaggle datasets create`

Uploads files and creates a new dataset on Kaggle.

**Usage:**
```bash
kaggle datasets create -p <FOLDER_PATH> [options]
```

**Options:**
- `-p, --path <FOLDER_PATH>`: Folder containing data files and `dataset-metadata.json`
- `--public`: Make the dataset public immediately (default: private/draft)
- `-u, --upload-dir <DIR>`: Sub-directory with files to upload
- `-t, --keep-tabular`: Do not convert tabular files to CSV
- `-r, --dir-mode <MODE>`: How to handle directories (`skip`, `zip`, `tar`)
- `-q, --quiet`: Suppress output

**Example:**
```bash
kaggle datasets create -p ./my-dataset
kaggle datasets create -p ./my-dataset --public
```

---

## `kaggle datasets version`

Creates a new version of an existing dataset.

**Usage:**
```bash
kaggle datasets version -p <FOLDER_PATH> -m <MESSAGE> [options]
```

**Options:**
- `-p, --path <FOLDER_PATH>`: Folder with updated files and `dataset-metadata.json`
- `-m, --message <MESSAGE>`: Version notes (required)
- `--delete-old-versions`: Delete previous versions
- `-t, --keep-tabular`: Do not convert tabular files
- `-r, --dir-mode <MODE>`: Directory handling (`skip`, `zip`, `tar`)
- `-q, --quiet`: Suppress output

**Example:**
```bash
kaggle datasets version -p . -m "added 2026 data"
kaggle datasets version -p . -m "v3 fix" --delete-old-versions
```

---

## `kaggle datasets metadata`

Downloads or updates dataset metadata.

**Usage:**
```bash
kaggle datasets metadata -d <DATASET> [options]
```

**Options:**
- `-d, --dataset <DATASET>`: Dataset URL suffix
- `-p, --path <PATH>`: Folder to save metadata file
- `-u, --update`: Update metadata on Kaggle from local `dataset-metadata.json`

**Examples:**
```bash
# Download metadata
kaggle datasets metadata -d uciml/iris -p ./meta

# Update metadata from local file
kaggle datasets metadata -d YOUR_USERNAME/my-dataset -u
```

---

## `kaggle datasets status`

Checks whether dataset creation or update completed.

**Usage:**
```bash
kaggle datasets status <DATASET>
```

**Example:**
```bash
kaggle datasets status YOUR_USERNAME/my-dataset
```

**Polling (shell):**
```bash
while true; do
  STATUS=$(kaggle datasets status YOUR_USERNAME/my-dataset)
  echo "Status: $STATUS"
  [[ "$STATUS" == *"ready"* ]] && break
  sleep 15
done
```

---

## `kaggle datasets delete`

Permanently removes a dataset.

**Usage:**
```bash
kaggle datasets delete -d <DATASET> [options]
```

**Options:**
- `-y, --yes`: Auto-confirm

**Example:**
```bash
kaggle datasets delete -d YOUR_USERNAME/my-dataset -y
```

---

## `kaggle datasets topics` / `topics show`

Browse discussion threads for a dataset.

```bash
kaggle datasets topics -d uciml/iris --sort-by hot
kaggle datasets topics show uciml/iris/12345
```

---

## Full create workflow

```bash
mkdir my-dataset && cd my-dataset
echo "id,value" > data.csv && echo "1,42" >> data.csv
kaggle datasets init                                 # creates dataset-metadata.json
# edit dataset-metadata.json ...
kaggle datasets create -p . --public
kaggle datasets status YOUR_USERNAME/my-dataset      # poll until "ready"
```
