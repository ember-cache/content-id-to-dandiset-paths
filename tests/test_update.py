import importlib.util
import pathlib
import tempfile
import types
import unittest
from unittest.mock import patch

import yaml


def _load_update_module():
    module_path = pathlib.Path(__file__).resolve().parents[1] / "code" / "update.py"
    spec = importlib.util.spec_from_file_location("cache_update", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestUpdate(unittest.TestCase):
    def test_initialize_dandi_client_uses_ember_api_url(self):
        update = _load_update_module()

        called_kwargs = {}

        class FakeDandiAPIClient:
            def __init__(self, **kwargs):
                called_kwargs.update(kwargs)

        fake_dandiapi = types.ModuleType("dandi.dandiapi")
        fake_dandiapi.DandiAPIClient = FakeDandiAPIClient

        fake_dandi = types.ModuleType("dandi")
        fake_dandi.dandiapi = fake_dandiapi

        with patch.dict("sys.modules", {"dandi": fake_dandi, "dandi.dandiapi": fake_dandiapi}):
            update._initialize_dandi_client()

        self.assertEqual(called_kwargs, {"api_url": "https://api-dandi.emberarchive.org/api"})

    def test_run_writes_content_id_mapping(self):
        update = _load_update_module()

        class FakeAsset:
            def __init__(self, path, url):
                self.path = path
                self._url = url

            def get_content_url(self, follow_redirects, strip_query):
                self._last_call = (follow_redirects, strip_query)
                return self._url

        class FakeDandiset:
            def __init__(self, identifier, assets):
                self.identifier = identifier
                self._assets = assets

            def get_assets(self):
                return self._assets

        class FakeClient:
            def __init__(self, dandisets):
                self._dandisets = dandisets

            def get_dandisets(self):
                return self._dandisets

        fake_client = FakeClient(
            [
                FakeDandiset(
                    "000001",
                    [
                        FakeAsset("sub-001/file-a.nwb", "https://example.org/blobs/content-one"),
                        FakeAsset("sub-001/file-b.nwb", "https://example.org/blobs/content-one"),
                    ],
                ),
                FakeDandiset(
                    "000002",
                    [
                        FakeAsset("sub-002/file-c.nwb", "https://example.org/assets/content-two/download"),
                    ],
                ),
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            base_directory = pathlib.Path(tmpdir)
            with patch.object(update, "_initialize_dandi_client", return_value=fake_client):
                update._run(base_directory)

            output_file_path = base_directory / "derivatives" / "content_id_to_dandiset_paths.yaml"
            with output_file_path.open("r") as file_stream:
                output = yaml.safe_load(file_stream)

        self.assertEqual(
            output,
            {
                "content-one": {"000001": ["sub-001/file-a.nwb", "sub-001/file-b.nwb"]},
                "content-two": {"000002": ["sub-002/file-c.nwb"]},
            },
        )


if __name__ == "__main__":
    unittest.main()
