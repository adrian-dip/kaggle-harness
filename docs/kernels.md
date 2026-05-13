# Kaggle Kernels Commands

Source: https://github.com/Kaggle/kaggle-api/blob/main/docs/kernels.md

Commands for interacting with Kaggle Kernels (notebooks and scripts).

---

## `kaggle kernels list`

Lists available kernels.

**Usage:**
```bash
kaggle kernels list [options]
```

**Options:**
- `-m, --mine`: Display only your kernels
- `-p, --page <PAGE>`: Page number (default: 1)
- `--page-size <SIZE>`: Items per page (default: 20)
- `-s, --search <TERM>`: Search term
- `-v, --csv`: Print in CSV format
- `--parent <PARENT_KERNEL>`: Filter by parent kernel (`owner/kernel-slug`)
- `--competition <SLUG>`: Filter by competition
- `--dataset <SLUG>`: Filter by dataset (`owner/dataset-slug`)
- `--user <USER>`: Filter by user
- `--language <LANGUAGE>`: Filter by language (`all`, `python`, `r`, `sqlite`, `julia`)
- `--kernel-type <TYPE>`: Filter by type (`all`, `script`, `notebook`)
- `--output-type <TYPE>`: Filter by output (`all`, `visualizations`, `data`)
- `--sort-by <SORT_BY>`: Sort order (`hotness`, `commentCount`, `dateCreated`, `dateRun`, `relevance`, `scoreAscending`, `scoreDescending`, `viewCount`, `voteCount`)

**Examples:**
```bash
# Your kernels containing "Exercise", page 2, CSV format, sorted by run date
kaggle kernels list -m -s Exercise --page-size 5 -p 2 -v --sort-by dateRun

# Children of a specific kernel
kaggle kernels list --parent $KAGGLE_DEVELOPER/exercise-lists

# First 5 kernels for a competition
kaggle kernels list --competition house-prices-advanced-regression-techniques --page-size 5

# Kernels associated with a dataset
kaggle kernels list --dataset dansbecker/home-data-for-ml-course --page-size 5

# Python notebooks by a user that output data
kaggle kernels list --user $KAGGLE_DEVELOPER --language python --kernel-type notebook --output-type data
```

---

## `kaggle kernels files`

Lists output files for a specific kernel.

**Usage:**
```bash
kaggle kernels files <KERNEL> [options]
```

**Arguments:**
- `<KERNEL>`: Kernel URL suffix (`owner/kernel-slug`)

**Options:**
- `-v, --csv`: Print in CSV format
- `--page-token <TOKEN>`: Page token for paging
- `--page-size <SIZE>`: Items per page (default: 20, max: 200)

**Example:**
```bash
kaggle kernels files kerneler/sqlite-global-default -v --page-size=1
```

---

## `kaggle kernels init`

Creates a template `kernel-metadata.json` for a new kernel.

**Usage:**
```bash
kaggle kernels init -p <FOLDER_PATH>
```

**Options:**
- `-p, --path <FOLDER_PATH>`: Path to create the metadata file (default: current dir)

**Example:**
```bash
kaggle kernels init -p ./my-kernel
```

---

## `kaggle kernels push`

Pushes code/notebook and metadata to Kaggle, then runs the kernel.

**Usage:**
```bash
kaggle kernels push -p <FOLDER_PATH> [options]
```

**Options:**
- `-p, --path <FOLDER_PATH>`: Path to folder containing kernel file and `kernel-metadata.json`
- `--accelerator <ACCELERATOR_ID>`: GPU/TPU accelerator to use
- `-t, --timeout <SECONDS>`: Maximum run time in seconds

**Available accelerators (as of Feb 2026):**
- `NvidiaTeslaP100` (default GPU)
- `NvidiaTeslaT4`
- `NvidiaTeslaT4Highmem`
- `NvidiaTeslaA100`
- `NvidiaL4`
- `NvidiaL4X1`
- `NvidiaH100`
- `NvidiaRtxPro6000`
- `TpuV38`
- `Tpu1VmV38`
- `TpuV5E8`
- `TpuV6E8`

> Some accelerators are only available to participants of specific competitions or Kaggle admins.

**Examples:**
```bash
kaggle kernels push -p ./my-kernel
kaggle kernels push -p ./my-kernel --accelerator NvidiaTeslaT4
```

---

## `kaggle kernels pull`

Downloads kernel source code and optional metadata.

**Usage:**
```bash
kaggle kernels pull <KERNEL> [options]
```

**Arguments:**
- `<KERNEL>`: Kernel URL suffix (`owner/kernel-slug`)

**Options:**
- `-p, --path <PATH>`: Folder to download files to
- `-w, --wp`: Download to current working directory
- `-m, --metadata`: Also download `kernel-metadata.json`

**Examples:**
```bash
kaggle kernels pull $KAGGLE_DEVELOPER/exercise-as-with -p ./my-kernel -m
kaggle kernels pull --wp $KAGGLE_DEVELOPER/exercise-as-with
```

---

## `kaggle kernels output`

Gets data output files from the latest kernel run.

**Usage:**
```bash
kaggle kernels output <KERNEL> [options]
```

**Arguments:**
- `<KERNEL>`: Kernel URL suffix (`owner/kernel-slug`)

**Options:**
- `-p, --path <PATH>`: Folder to download output files to
- `-w, --wp`: Download to current working directory
- `-o, --force`: Force overwrite of existing files
- `-q, --quiet`: Suppress output
- `--file-pattern <REGEX>`: Regex to filter filenames (only matching files downloaded)

**Examples:**
```bash
kaggle kernels output kerneler/sqlite-global-default -p ./output -o
kaggle kernels output my-kernel --file-pattern ".*\.csv$"   # CSV files only
kaggle kernels output my-kernel --file-pattern ".*\.png$"   # PNG files only
```

---

## `kaggle kernels status`

Shows the status of the latest kernel run.

**Usage:**
```bash
kaggle kernels status <KERNEL>
```

**Arguments:**
- `<KERNEL>`: Kernel URL suffix (`owner/kernel-slug`)

**Possible statuses:** `queued`, `running`, `complete`, `error`, `cancel`

**Example:**
```bash
kaggle kernels status kerneler/sqlite-global-default
```

**Polling until done (shell):**
```bash
while true; do
  STATUS=$(kaggle kernels status YOUR_USERNAME/my-kernel | grep -oE 'complete|error|cancel|running|queued')
  echo "Status: $STATUS"
  [[ "$STATUS" == "complete" || "$STATUS" == "error" || "$STATUS" == "cancel" ]] && break
  sleep 30
done
```

---

## `kaggle kernels delete`

Permanently deletes a kernel.

**Usage:**
```bash
kaggle kernels delete <KERNEL> [options]
```

**Options:**
- `-y, --yes`: Auto-confirm without prompting

**Example:**
```bash
kaggle kernels delete $KAGGLE_DEVELOPER/exercise-delete --yes
```

---

## Full push-poll-retrieve workflow

```bash
# 1. Pull existing kernel with metadata
kaggle kernels pull YOUR_USERNAME/my-kernel -p ./my-kernel -m

# 2. Edit the script / notebook locally
#    e.g. vim ./my-kernel/my-kernel.py

# 3. Push (uploads and triggers run on Kaggle)
kaggle kernels push -p ./my-kernel

# 4. Poll status
while true; do
  STATUS=$(kaggle kernels status YOUR_USERNAME/my-kernel | grep -oE 'complete|error|cancel|running|queued')
  echo "[$(date +%H:%M:%S)] $STATUS"
  [[ "$STATUS" == "complete" || "$STATUS" == "error" || "$STATUS" == "cancel" ]] && break
  sleep 30
done

# 5. Download output
kaggle kernels output YOUR_USERNAME/my-kernel -p ./results -o
```
