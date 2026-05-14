import io
import zipfile

import pytest

from kaggle_harness.bundles.bundle import Bundle
from kaggle_harness.bundles.manifest import ExperimentManifest


VALID_YAML = """
name: my-experiment
entrypoint: python train.py
resources:
  cpu: 2
  memory: 8G
  gpu: false
"""

INVALID_NAME_YAML = """
name: MY EXPERIMENT
entrypoint: python train.py
"""


def _make_zip(yaml_content: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("experiment.yaml", yaml_content)
    return buf.getvalue()


def test_manifest_parses_valid_yaml():
    m = ExperimentManifest.from_yaml(VALID_YAML)
    assert m.name == "my-experiment"
    assert m.entrypoint == "python train.py"
    assert m.resources.cpu == 2
    assert m.memory_mb() == 8192


def test_manifest_rejects_bad_name():
    with pytest.raises(Exception):
        ExperimentManifest.from_yaml(INVALID_NAME_YAML)


def test_manifest_defaults():
    m = ExperimentManifest.from_yaml(VALID_YAML)
    assert m.runtime.image == "runner-base:py311"
    assert m.resources.gpu is False
    assert m.inputs.competitions == []
    assert m.submit is None


def test_bundle_from_zip():
    data = _make_zip(VALID_YAML)
    bundle = Bundle.from_zip_bytes("abc123", data)
    assert bundle.bundle_id == "abc123"
    assert bundle.manifest.name == "my-experiment"


def test_bundle_rejects_zip_without_manifest():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("train.py", "print('hello')")
    with pytest.raises(ValueError, match="experiment.yaml"):
        Bundle.from_zip_bytes("x", buf.getvalue())
