# Kaggle Models Commands

Source: https://github.com/Kaggle/kaggle-api/blob/main/docs/models.md

Commands for managing Kaggle Models, Variations, and Versions.

---

## `kaggle models list`

Lists available models.

**Usage:**
```bash
kaggle models list [options]
```

**Options:**
- `--owner <OWNER>`: Filter by user or organization
- `--sort-by <SORT_BY>`: Sort order (`hotness`, `downloadCount`, `voteCount`, `notebookCount`, `createTime`)
- `-s, --search <TERM>`: Search term
- `--page-size <SIZE>`: Items per page (default: 20)
- `--page-token <TOKEN>`: Page token for paging
- `-v, --csv`: Print in CSV format

**Examples:**
```bash
kaggle models list -s gemini --page-size 5
kaggle models list --owner $KAGGLE_DEVELOPER --sort-by createTime -v
```

---

## `kaggle models init`

Creates a `model-metadata.json` template.

**Usage:**
```bash
kaggle models init -p <FOLDER_PATH>
```

**Example:**
```bash
mkdir my-model
kaggle models init -p my-model
# edit my-model/model-metadata.json
```

---

## `kaggle models create`

Creates a new model on Kaggle.

**Usage:**
```bash
kaggle models create -p <FOLDER_PATH>
```

**Example:**
```bash
kaggle models create -p ./my-model
```

---

## `kaggle models get`

Downloads `model-metadata.json` for an existing model.

**Usage:**
```bash
kaggle models get <MODEL> -p <FOLDER_PATH>
```

**Example:**
```bash
kaggle models get $KAGGLE_DEVELOPER/test-model -p ./tmp
```

---

## `kaggle models update`

Updates an existing model's metadata.

**Usage:**
```bash
kaggle models update -p <FOLDER_PATH>
```

**Example:**
```bash
kaggle models update -p ./my-model
```

---

## `kaggle models delete`

Permanently deletes a model and all its variations/versions.

**Usage:**
```bash
kaggle models delete <MODEL> [options]
```

**Options:**
- `-y, --yes`: Auto-confirm

**Example:**
```bash
kaggle models delete $KAGGLE_DEVELOPER/test-model -y
```

---

## Model Variations

```bash
# Initialize variation metadata
kaggle models variations init -p ./my-model   # creates model-instance-metadata.json

# Create the variation (uploads files + metadata)
kaggle models variations create -p ./my-model

# Update an existing variation
kaggle models variations update -p ./my-model

# Delete a variation
kaggle models variations delete owner/model-slug/framework/variation-slug -y
```

---

## Model Variation Versions

```bash
# Create a new version of a variation
kaggle models variations versions create \
  YOUR_USERNAME/my-model/pytorch/my-variation \
  -p ./my-model \
  -n "v2 - improved weights"

# Download a specific version
kaggle models instances versions download \
  YOUR_USERNAME/my-model/pytorch/my-variation/1 \
  -p ./downloaded-model
```

---

## `model-metadata.json` format

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

---

## `model-instance-metadata.json` format (variation)

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

**Valid `framework` values:** `tensorflow`, `pytorch`, `jax`, `sklearn`, `transformers`, `other`

---

## Full model creation workflow

```bash
# 1. Create model record
mkdir my-model && cd my-model
kaggle models init
# edit model-metadata.json ...
kaggle models create -p .

# 2. Add model files and create a variation
echo "weights" > weights.bin
kaggle models variations init        # creates model-instance-metadata.json
# edit model-instance-metadata.json ...
kaggle models variations create -p .

# 3. Later: add a new version with updated files
echo "weights-v2" > weights_v2.bin
kaggle models variations versions create \
  YOUR_USERNAME/my-awesome-ai-model/pytorch/pytorch-implementation \
  -p . -n "v2 improved"
```
