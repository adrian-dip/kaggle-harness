# Dataset Metadata (`dataset-metadata.json`)

Source: https://github.com/Kaggle/kaggle-api/blob/main/docs/datasets_metadata.md

The `dataset-metadata.json` file follows the [Data Package specification](https://specs.frictionlessdata.io/data-package/).

Generate a blank template with:
```bash
kaggle datasets init
```

---

## Minimal example

```json
{
  "title": "My Sample Dataset",
  "id": "YOUR_USERNAME/my-sample-dataset",
  "licenses": [{"name": "CC0-1.0"}]
}
```

---

## Full example

```json
{
  "title": "My Sample Dataset",
  "id": "YOUR_USERNAME/my-sample-dataset",
  "licenses": [{"name": "CC0-1.0"}],
  "subtitle": "A short subtitle between 20 and 80 characters",
  "description": "Longer description of the dataset and its contents.",
  "id_no": 123456,
  "keywords": ["tabular", "classification", "beginner"],
  "expectedUpdateFrequency": "monthly",
  "userSpecifiedSources": ["https://example.com/source"],
  "image": "cover.png",
  "resources": [
    {
      "path": "data.csv",
      "description": "Main data file",
      "schema": {
        "fields": [
          {"name": "id",    "title": "Row index", "type": "integer"},
          {"name": "col_a", "title": "Feature A",  "type": "number"},
          {"name": "label", "title": "Class label", "type": "string"}
        ]
      }
    }
  ]
}
```

---

## Field Reference

| Field | Required | Constraints | Description |
|---|---|---|---|
| `title` | Yes | 6–50 chars | Human-readable dataset title |
| `id` | Yes | `username/slug`, slug 3–50 chars | URL identifier |
| `licenses` | Yes | Exactly one entry | Array with `{"name": "<license>"}` |
| `subtitle` | No | 20–80 chars | Short subtitle |
| `description` | No | — | Full description (Markdown OK) |
| `id_no` | No | — | Numeric dataset ID (assigned by Kaggle) |
| `keywords` | No | — | Array of existing Kaggle tags |
| `expectedUpdateFrequency` | No | — | e.g. `"never"`, `"daily"`, `"weekly"`, `"monthly"`, `"quarterly"`, `"annually"` |
| `userSpecifiedSources` | No | — | Array of source URLs |
| `image` | No | Min 560×280px, `.png`/`.jpg`/`.jpeg`/`.webp` | Cover image path (sibling to metadata file) |
| `resources` | No | — | Array of file descriptors |

### `resources[].schema.fields` types

Valid `type` values: `string`, `number`, `integer`, `boolean`, `object`, `array`, `date`, `time`, `datetime`, `duration`, `geopoint`, `geojson`, `any`

> **Note**: The `fields` array must include ALL columns in order, or columns will not match correctly.

---

## Common license names

| License | Name value |
|---|---|
| Creative Commons Zero | `CC0-1.0` |
| Creative Commons Attribution | `CC-BY-4.0` |
| Creative Commons Attribution-ShareAlike | `CC-BY-SA-4.0` |
| GPL v2 | `GPL-2` |
| Open Database License | `ODbL-1.0` |
| Other | `other` |
