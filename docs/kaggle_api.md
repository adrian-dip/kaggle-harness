# Kaggle API Reference

Source: [github.com/Kaggle/kaggle-api](https://github.com/Kaggle/kaggle-api) · [kaggle.com/docs/api](https://www.kaggle.com/docs/api)

---

## Installation

```sh
pip install kaggle        # requires Python 3.11+
```

If `kaggle` is not found after install, add the scripts directory to PATH:
- **Linux/macOS**: `~/.local/bin`
- **Windows**: `%PYTHON_HOME%\Scripts`

---

## Authentication

You need a Kaggle account first: https://www.kaggle.com/account/login

### Option 1 — OAuth (recommended, interactive)

```sh
kaggle auth login
```

Opens a browser-based authorization flow and stores credentials automatically.

### Option 2 — Environment variable

```sh
export KAGGLE_API_TOKEN="<token-from-settings>"
# Windows PowerShell:
$env:KAGGLE_API_TOKEN = "<token-from-settings>"
```

Get the token value from https://www.kaggle.com/settings/api → "Generate New Token".

### Option 3 — API token file

Store your token at `~/.kaggle/access_token` (plain text, no JSON).

### Option 4 — Legacy `kaggle.json` (most widely supported)

1. Go to https://www.kaggle.com/settings/api
2. Under "Legacy API Credentials", click **Create Legacy API Key**
3. Save the downloaded file to `~/.kaggle/kaggle.json`
4. Restrict permissions: `chmod 600 ~/.kaggle/kaggle.json`

The file looks like:
```json
{"username": "YOUR_USERNAME", "key": "YOUR_API_KEY"}
```

`authenticate()` checks env vars first, then falls back to the config file.

### Python API authentication

```python
from kaggle.api.kaggle_api_extended import KaggleApi

api = KaggleApi()
api.authenticate()
```

---

## Competitions

### CLI commands

```sh
# List / search competitions
kaggle competitions list
kaggle competitions list -s "nlp"          # search by keyword
kaggle competitions list --csv             # output as CSV

# List data files for a competition
kaggle competitions files -c titanic

# Download competition data
kaggle competitions download -c titanic                    # all files as zip
kaggle competitions download -c titanic -f train.csv      # single file
kaggle competitions download -c titanic -p ./data         # custom path
kaggle competitions download -c titanic --unzip

# Submit predictions
kaggle competitions submit titanic -f submission.csv -m "first attempt"

# Submit from a kernel (code competitions)
kaggle competitions submit <competition> \
  -k <username>/<notebook-slug> \
  -f <output-filename> \
  -v <notebook-version> \
  -m "description"

# View your submissions and scores
kaggle competitions submissions -c titanic
kaggle competitions submissions -c titanic --csv

# View leaderboard
kaggle competitions leaderboard titanic
kaggle competitions leaderboard titanic --download        # saves CSV
```

> **Important**: You must join a competition and accept its rules on kaggle.com before you can download data or submit.

### Python API

```python
import os

# List competitions
comps = api.competitions_list(search="nlp", page=1)
for c in comps:
    print(c)

# Download all competition files
api.competition_download_files("titanic", path="./data", unzip=True)

# Download a single file
api.competition_download_file("titanic", "train.csv", path="./data")

# Submit predictions
api.competition_submit("submission.csv", "my message", "titanic")

# List your submissions
subs = api.competitions_submissions_list("titanic")
for s in subs:
    print(s.ref, s.publicScore, s.privateScore, s.status)

# View leaderboard
board = api.competition_view_leaderboard("titanic")
```

### Polling submission status

The submission API does not provide an async handle — check periodically:

```python
import time

api.competition_submit("submission.csv", "run 1", "titanic")

while True:
    subs = api.competitions_submissions_list("titanic")
    latest = subs[0]
    print(f"Status: {latest.status}  Score: {latest.publicScore}")
    if latest.status not in ("pending", "running"):
        break
    time.sleep(30)
```

---

## Datasets

### CLI commands

```sh
# Search / list datasets
kaggle datasets list
kaggle datasets list -s "iris"
kaggle datasets list --mine                            # only your datasets
kaggle datasets list --csv

# List files in a dataset
kaggle datasets files -d uciml/iris

# Download a dataset
kaggle datasets download -d uciml/iris                # full zip
kaggle datasets download -d uciml/iris --unzip
kaggle datasets download -d uciml/iris -f Iris.csv    # single file
kaggle datasets download -d uciml/iris -p ./data

# Create a new dataset
kaggle datasets init                                   # generates dataset-metadata.json
kaggle datasets create -p .                            # upload current dir
kaggle datasets create -p ./my-dataset --public

# Update / new version
kaggle datasets version -p . -m "version notes"
kaggle datasets version -p . -m "added new file" --dir-mode zip

# Get or update metadata
kaggle datasets metadata -d uciml/iris                # download metadata
kaggle datasets metadata -d uciml/iris -u             # update from local file

# Check upload status
kaggle datasets status uciml/iris

# Delete
kaggle datasets delete -d YOUR_USERNAME/my-dataset
```

### `dataset-metadata.json` format

Generated by `kaggle datasets init`, then edited:

```json
{
  "title": "My Sample Dataset",
  "id": "YOUR_USERNAME/my-sample-dataset",
  "licenses": [{"name": "CC0-1.0"}],
  "subtitle": "A short subtitle (20-80 chars)",
  "description": "Longer description of the dataset.",
  "keywords": ["tabular", "classification"],
  "expectedUpdateFrequency": "monthly",
  "resources": [
    {
      "path": "sample_data.csv",
      "description": "Main data file",
      "schema": {
        "fields": [
          {"name": "id",    "title": "Row index", "type": "integer"},
          {"name": "col_a", "title": "Feature A",  "type": "number"}
        ]
      }
    }
  ]
}
```

**Field constraints:**
- `title`: 6–50 characters (required)
- `id`: `username/slug` where slug is 3–50 characters (required)
- `licenses`: exactly one entry (required). Common values: `CC0-1.0`, `CC-BY-4.0`, `CC-BY-SA-4.0`, `GPL-2`, `ODbL-1.0`, `other`
- `subtitle`: 20–80 characters (optional)
- `image`: relative path to a `.png/.jpg/.jpeg/.webp` file, minimum 560×280 px

### Create dataset — full workflow

```sh
mkdir my-dataset && cd my-dataset
echo "id,value" > data.csv && echo "1,42" >> data.csv
kaggle datasets init                   # writes dataset-metadata.json
# edit dataset-metadata.json ...
kaggle datasets create -p .            # upload + publish draft
kaggle datasets status YOUR_USERNAME/my-sample-dataset   # poll until ready
```

### Python API

```python
# Search
datasets = api.dataset_list(search="iris", mine=False)

# Download
api.dataset_download_files("uciml/iris", path="./data", unzip=True)
api.dataset_download_file("uciml/iris", "Iris.csv", path="./data")

# Create new dataset
api.dataset_create_new(folder="./my-dataset", public=True, quiet=False)

# Create new version
api.dataset_create_version(folder="./my-dataset", version_notes="v2 data", quiet=False)

# Check status
status = api.dataset_status("YOUR_USERNAME/my-sample-dataset")
print(status)
```

---

## Kernels (Notebooks & Scripts)

Kernels are Kaggle's hosted notebooks/scripts. Pushing a kernel runs it on Kaggle's servers.

### CLI commands

```sh
# List / search kernels
kaggle kernels list
kaggle kernels list -s "titanic" --mine
kaggle kernels list --language python --kernel-type notebook

# Pull kernel source + metadata to a local folder
kaggle kernels pull YOUR_USERNAME/my-kernel -p ./my-kernel-dir -m

# Initialize metadata for a NEW kernel
kaggle kernels init -p ./my-kernel-dir      # writes kernel-metadata.json

# Push (upload + run)
kaggle kernels push -p ./my-kernel-dir

# Check run status
kaggle kernels status YOUR_USERNAME/my-kernel

# Get output files from latest run
kaggle kernels output YOUR_USERNAME/my-kernel -p ./output
kaggle kernels output YOUR_USERNAME/my-kernel -p ./output --force

# List output files
kaggle kernels files YOUR_USERNAME/my-kernel

# Delete
kaggle kernels delete YOUR_USERNAME/my-kernel
```

### `kernel-metadata.json` format

Generated by `kaggle kernels init` or `kaggle kernels pull -m`:

```json
{
  "id": "YOUR_USERNAME/my-kernel-slug",
  "title": "My Kernel Title",
  "code_file": "my_script.py",
  "language": "python",
  "kernel_type": "script",
  "is_private": true,
  "enable_gpu": false,
  "enable_tpu": false,
  "enable_internet": false,
  "dataset_sources": ["uciml/iris"],
  "competition_sources": ["titanic"],
  "kernel_sources": [],
  "model_sources": []
}
```

**Field reference:**
| Field | Values | Notes |
|---|---|---|
| `id` | `username/kernel-slug` | slug = title lowercased, spaces → dashes |
| `language` | `python`, `r`, `rmarkdown` | |
| `kernel_type` | `script`, `notebook` | |
| `enable_gpu` | `true`/`false` | defaults to `false` |
| `enable_tpu` | `true`/`false` | defaults to `false` |
| `enable_internet` | `true`/`false` | defaults to `false` |
| `dataset_sources` | `["owner/slug"]` | datasets the kernel can access |
| `competition_sources` | `["competition-name"]` | |
| `kernel_sources` | `["owner/slug"]` | other kernels to import |

Available accelerators for `enable_gpu`/TPU: `NvidiaH100`, `TpuV6E8`, and others (availability varies by competition and account).

### Push and poll — full workflow

```sh
# 1. Pull existing kernel with metadata
kaggle kernels pull YOUR_USERNAME/my-kernel -p ./my-kernel -m

# 2. Edit the script / notebook
#    e.g., edit ./my-kernel/my-kernel.py

# 3. Push (uploads + triggers run)
kaggle kernels push -p ./my-kernel

# 4. Poll until done
while true; do
  STATUS=$(kaggle kernels status YOUR_USERNAME/my-kernel)
  echo "$STATUS"
  echo "$STATUS" | grep -qE "complete|error" && break
  sleep 30
done

# 5. Download output
kaggle kernels output YOUR_USERNAME/my-kernel -p ./output
```

### Python API

```python
# Pull
api.kernels_pull("YOUR_USERNAME/my-kernel", path="./my-kernel", metadata=True)

# Push
api.kernels_push("./my-kernel")

# Poll status
import time

while True:
    status = api.kernels_status("YOUR_USERNAME/my-kernel")
    print(status)
    if status in ("complete", "error", "cancel"):
        break
    time.sleep(30)

# Get output
api.kernels_output("YOUR_USERNAME/my-kernel", path="./output", force=True)

# List output files
files = api.kernels_list_files("YOUR_USERNAME/my-kernel")
```

---

## Models

```sh
# List models
kaggle models list
kaggle models list -s "bert"

# Initialize metadata
kaggle models init -p ./my-model        # creates model-metadata.json

# Create model (metadata only, no files)
kaggle models create -p ./my-model

# Create a variation (framework-specific files)
kaggle models variations init -p ./my-model
kaggle models variations create -p ./my-model

# Create a new version of a variation
kaggle models variations versions create \
  YOUR_USERNAME/my-model/pytorch/my-variation \
  -p ./my-model \
  -n "v2 - improved weights"

# Download model
kaggle models instances versions download \
  YOUR_USERNAME/my-model/pytorch/my-variation/1 \
  -p ./downloaded-model
```

### `model-metadata.json` format

```json
{
  "ownerSlug": "YOUR_USERNAME",
  "title": "My Awesome AI Model",
  "slug": "my-awesome-ai-model",
  "isPrivate": true,
  "description": "Model description here.",
  "publishTime": "",
  "licenses": [{"name": "Apache 2.0"}]
}
```

### `model-instance-metadata.json` format (variation)

```json
{
  "ownerSlug": "YOUR_USERNAME",
  "modelSlug": "my-awesome-ai-model",
  "instanceSlug": "pytorch-implementation",
  "framework": "pytorch",
  "overview": "PyTorch implementation of my model.",
  "usage": "Load with torch.load()",
  "licenseName": "Apache 2.0",
  "fineTunable": false,
  "trainingData": [],
  "modelInstanceFiles": []
}
```

---

## Configuration

```sh
kaggle config set -n <key> -v <value>    # set a config value
kaggle config view                        # show current config
kaggle config unset -n <key>
```

Common keys: `competition`, `path` (default download path), `proxy`.

---

## Environment Variables

| Variable | Purpose |
|---|---|
| `KAGGLE_API_TOKEN` | Full token string (new auth) |
| `KAGGLE_USERNAME` | Username (legacy auth) |
| `KAGGLE_KEY` | API key (legacy auth) |
| `KAGGLE_CONFIG_DIR` | Override `~/.kaggle` config dir |

---

## Common Patterns for This Harness

### Run a script on Kaggle and get results

```python
import time
from kaggle.api.kaggle_api_extended import KaggleApi

api = KaggleApi()
api.authenticate()

# Push kernel (runs immediately on Kaggle)
api.kernels_push("./my-kernel")

# Poll until finished
kernel_id = "YOUR_USERNAME/my-kernel-slug"
while True:
    status = api.kernels_status(kernel_id)
    print(f"[{time.strftime('%H:%M:%S')}] status: {status}")
    if status in ("complete", "error", "cancel"):
        break
    time.sleep(60)

if status == "complete":
    api.kernels_output(kernel_id, path="./results", force=True)
    print("Output downloaded to ./results/")
else:
    print(f"Kernel ended with status: {status}")
```

### Upload a dataset, use it in a kernel

```python
# 1. Create / update dataset
api.dataset_create_version(folder="./my-data", version_notes="fresh run", quiet=False)

# 2. Poll dataset ready
import time
slug = "YOUR_USERNAME/my-dataset-slug"
while True:
    s = api.dataset_status(slug)
    if s == "ready":
        break
    time.sleep(15)

# 3. Push kernel that references dataset
# (kernel-metadata.json must list the dataset in dataset_sources)
api.kernels_push("./my-kernel")
```

### Submit to competition from file

```python
api.competition_submit(
    file_name="./results/submission.csv",
    message="automated submission v3",
    competition="titanic",
)

# Check result
time.sleep(10)
subs = api.competitions_submissions_list("titanic")
print(subs[0].publicScore, subs[0].status)
```

---

## Quick Reference

| Task | CLI | Python |
|---|---|---|
| Login | `kaggle auth login` | `api.authenticate()` |
| List competitions | `kaggle competitions list` | `api.competitions_list()` |
| Download competition data | `kaggle competitions download -c <id>` | `api.competition_download_files(id)` |
| Submit predictions | `kaggle competitions submit <id> -f file.csv -m "msg"` | `api.competition_submit(file, msg, id)` |
| List submissions | `kaggle competitions submissions -c <id>` | `api.competitions_submissions_list(id)` |
| List datasets | `kaggle datasets list -s <query>` | `api.dataset_list(search=q)` |
| Download dataset | `kaggle datasets download -d owner/slug` | `api.dataset_download_files(slug)` |
| Create dataset | `kaggle datasets init` then `create -p .` | `api.dataset_create_new(folder)` |
| Update dataset | `kaggle datasets version -p . -m "notes"` | `api.dataset_create_version(folder, notes)` |
| Dataset status | `kaggle datasets status owner/slug` | `api.dataset_status(slug)` |
| Pull kernel | `kaggle kernels pull owner/slug -m` | `api.kernels_pull(slug, metadata=True)` |
| Push kernel | `kaggle kernels push -p .` | `api.kernels_push(folder)` |
| Kernel status | `kaggle kernels status owner/slug` | `api.kernels_status(slug)` |
| Kernel output | `kaggle kernels output owner/slug -p ./out` | `api.kernels_output(slug, path)` |

---

Sources:
- [Kaggle API GitHub (kaggle-api)](https://github.com/Kaggle/kaggle-api)
- [Kaggle CLI docs — README](https://github.com/Kaggle/kaggle-api/blob/main/docs/README.md)
- [Kaggle CLI docs — competitions](https://github.com/Kaggle/kaggle-api/blob/main/docs/competitions.md)
- [Kaggle CLI docs — datasets](https://github.com/Kaggle/kaggle-api/blob/main/docs/datasets.md)
- [Kaggle CLI docs — kernels](https://github.com/Kaggle/kaggle-api/blob/main/docs/kernels.md)
- [Kaggle CLI docs — tutorials](https://github.com/Kaggle/kaggle-api/blob/main/docs/tutorials.md)
- [Kaggle official API docs](https://www.kaggle.com/docs/api)
