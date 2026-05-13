# Kaggle CLI Tutorials

Source: https://github.com/Kaggle/kaggle-api/blob/main/docs/tutorials.md

Step-by-step tutorials for common Kaggle CLI workflows.

---

## Prerequisites

1. Install the Kaggle CLI: `pip install kaggle`
2. Set up API credentials (see [kaggle_api.md](./kaggle_api.md#authentication))
3. Log in to kaggle.com in a browser to verify results in [Your Work](https://www.kaggle.com/work)

---

## Tutorial: Create a Dataset

```bash
# 1. Create a directory with your data
mkdir my-new-dataset && cd my-new-dataset
echo "id,col_a,col_b,col_c" > sample_data.csv
echo "1,0.5,0.2,0.8" >> sample_data.csv
echo "2,0.1,0.7,0.3" >> sample_data.csv

# 2. Generate metadata template
kaggle datasets init

# 3. Edit dataset-metadata.json:
#    - Set "title" (6-50 chars)
#    - Set "id" to "YOUR_USERNAME/my-sample-dataset"
#    - Set "licenses" to [{"name": "CC0-1.0"}]

# 4. Upload
kaggle datasets create -p .
# Add --public to publish immediately

# 5. Verify at https://www.kaggle.com/work/datasets
```

---

## Tutorial: Find and Download a Dataset

```bash
# 1. Search for datasets
kaggle datasets list -s iris

# 2. Download by dataset ID (owner/slug)
mkdir iris-data && cd iris-data
kaggle datasets download -d uciml/iris

# 3. Unzip (or use --unzip flag in step 2)
unzip iris.zip
```

---

## Tutorial: Update a Kernel (Notebook)

```bash
# 1. Pull kernel + metadata from Kaggle
mkdir my-kernel && cd my-kernel
kaggle kernels pull YOUR_USERNAME/my-cli-test-kernel -m
# Downloads: my-cli-test-kernel.ipynb + kernel-metadata.json

# 2. Edit the notebook or script locally

# 3. Push changes (uploads and triggers run)
kaggle kernels push -p .

# 4. Verify at https://www.kaggle.com/work/code
```

---

## Tutorial: Submit to a Standard Competition

```bash
# 1. Join the competition and accept rules on kaggle.com first!

# 2. Download competition data
mkdir titanic && cd titanic
kaggle competitions download -c titanic
unzip titanic.zip

# 3. Generate your submission file (must match competition format)
#    For Titanic: columns PassengerId, Survived
cp gender_submission.csv my_submission.csv

# 4. Submit
kaggle competitions submit titanic -f my_submission.csv -m "My first submission"

# 5. Check status
kaggle competitions submissions -c titanic
# Check https://www.kaggle.com/c/titanic/submissions
```

---

## Tutorial: Submit to a Code Competition

```bash
# 1. Download competition data
kaggle competitions download -c <competition-name>

# 2. Create or update your notebook (see kernel tutorials above)
#    Push it to Kaggle with the competition in competition_sources

# 3. Submit from notebook output
kaggle competitions submit <competition-name> \
  -k <username>/<notebook-slug> \
  -f submission.csv \
  -v 3 \
  -m "notebook v3"

# 4. Check leaderboard
kaggle competitions leaderboard <competition-name>
```

---

## Tutorial: Create a Model

```bash
mkdir my-model && cd my-model

# 1. Initialize metadata
kaggle models init
# Edit model-metadata.json: set ownerSlug, title, slug

# 2. Create the model record
kaggle models create -p .

# 3. Add a variation with framework-specific files
echo "placeholder weights" > weights.bin
kaggle models variations init
# Edit model-instance-metadata.json: set ownerSlug, modelSlug, instanceSlug, framework

kaggle models variations create -p .

# 4. Later: add a new version
echo "v2 weights" > weights_v2.bin
kaggle models variations versions create \
  YOUR_USERNAME/my-model/pytorch/my-variation \
  -p . -n "v2 updated weights"
```

---

## Tutorial: Full Script Automation (Push → Poll → Download)

```python
import time
from kaggle.api.kaggle_api_extended import KaggleApi

api = KaggleApi()
api.authenticate()

KERNEL = "YOUR_USERNAME/my-kernel-slug"
KERNEL_DIR = "./my-kernel"
OUTPUT_DIR = "./results"

# Push kernel (triggers run)
api.kernels_push(KERNEL_DIR)
print("Kernel pushed, waiting for completion...")

# Poll until done
while True:
    status = api.kernels_status(KERNEL)
    print(f"[{time.strftime('%H:%M:%S')}] {status}")
    if status in ("complete", "error", "cancel"):
        break
    time.sleep(60)

# Download output if successful
if status == "complete":
    api.kernels_output(KERNEL, path=OUTPUT_DIR, force=True)
    print(f"Output saved to {OUTPUT_DIR}/")
else:
    print(f"Kernel ended with status: {status}")
```
