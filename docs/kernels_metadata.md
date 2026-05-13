# Kernel Metadata (`kernel-metadata.json`)

Source: https://github.com/Kaggle/kaggle-api/blob/main/docs/kernels_metadata.md

A `kernel-metadata.json` file is required to push a kernel via `kaggle kernels push`.

Generate a blank template with:
```bash
kaggle kernels init -p /path/to/kernel
```

Pull metadata for an existing kernel with:
```bash
kaggle kernels pull -p /path/to/download -k username/kernel-slug -m
```

---

## Example

```json
{
  "id": "timoboz/my-awesome-kernel",
  "id_no": 12345,
  "title": "My Awesome Kernel",
  "code_file": "my-awesome-kernel.ipynb",
  "language": "python",
  "kernel_type": "notebook",
  "is_private": "false",
  "enable_gpu": "false",
  "enable_internet": "false",
  "dataset_sources": ["timoboz/my-awesome-dataset"],
  "competition_sources": [],
  "kernel_sources": [],
  "model_sources": []
}
```

---

## Field Reference

| Field | Required | Description |
|---|---|---|
| `id` | One of `id`/`id_no` | `username/kernel-slug`. Slug = title lowercased, spaces → dashes |
| `id_no` | One of `id`/`id_no` | Numeric kernel ID. Takes precedence over `id` if both set |
| `title` | Required for new kernels | Human-readable title. Renaming changes the slug — update `id` too after rename |
| `code_file` | Required | Path to kernel source (`.py`, `.ipynb`, `.Rmd`). Relative to `kernel-metadata.json` location |
| `language` | Required | `python`, `r`, or `rmarkdown` |
| `kernel_type` | Required | `script` or `notebook` |
| `is_private` | Optional | `true` or `false`. Defaults to `true` |
| `enable_gpu` | Optional | `true` or `false`. Defaults to `false` |
| `enable_internet` | Optional | `true` or `false`. Defaults to `false` |
| `dataset_sources` | Optional | Array of `"username/dataset-slug"` |
| `competition_sources` | Optional | Array of `"competition-slug"` |
| `kernel_sources` | Optional | Array of `"username/kernel-slug"` |
| `model_sources` | Optional | Array of `"username/model-slug/framework/variation-slug/version-number"` |

---

## Notes

- A kernel slug is always the title lowercased with dashes replacing spaces.
- When renaming a kernel, change both `title` and `id` — but update `id` **after** the rename completes.
- `enable_gpu` and related fields accept string `"true"`/`"false"` or boolean `true`/`false`.
