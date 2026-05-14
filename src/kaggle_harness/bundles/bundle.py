from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass

from kaggle_harness.bundles.manifest import ExperimentManifest


@dataclass(frozen=True)
class Bundle:
    bundle_id: str
    manifest: ExperimentManifest

    @classmethod
    def from_zip_bytes(cls, bundle_id: str, data: bytes) -> "Bundle":
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = zf.namelist()
            if "experiment.yaml" not in names:
                raise ValueError("Bundle zip must contain experiment.yaml at root")
            manifest_text = zf.read("experiment.yaml").decode()
        manifest = ExperimentManifest.from_yaml(manifest_text)
        return cls(bundle_id=bundle_id, manifest=manifest)
