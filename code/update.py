import collections
import pathlib

import yaml


def _initialize_dandi_client():
    from dandi.dandiapi import DandiAPIClient

    return DandiAPIClient(api_url="https://api-dandi.emberarchive.org/api")


def _extract_content_id(content_url: str) -> str:
    if "blobs" in content_url:
        return content_url.split("/")[-1]
    return content_url.split("/")[-2]


def _run(base_directory: pathlib.Path, /) -> None:
    content_id_to_dandiset_paths: dict[str, dict[str, set[str]]] = collections.defaultdict(dict)

    client = _initialize_dandi_client()
    for dandiset in client.get_dandisets():
        for asset in dandiset.get_assets():
            content_url = asset.get_content_url(follow_redirects=1, strip_query=True)
            content_id = _extract_content_id(content_url=content_url)

            dandiset_id = dandiset.identifier
            path_in_dandiset = asset.path

            if content_id not in content_id_to_dandiset_paths:
                content_id_to_dandiset_paths[content_id] = collections.defaultdict(set)

            content_id_to_dandiset_paths[content_id][dandiset_id].add(path_in_dandiset)

    content_id_to_dandiset_paths_frozen: dict[str, dict[str, list[str]]] = {
        content_id: {
            dandiset_id: sorted(list(paths_in_dandiset)) for dandiset_id, paths_in_dandiset in dandiset_paths.items()
        }
        for content_id, dandiset_paths in content_id_to_dandiset_paths.items()
    }

    output_file_path = base_directory / "derivatives" / "content_id_to_dandiset_paths.yaml"
    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    with output_file_path.open(mode="w") as file_stream:
        yaml.safe_dump(data=content_id_to_dandiset_paths_frozen, stream=file_stream)


if __name__ == "__main__":
    repo_head = pathlib.Path(__file__).parent.parent

    _run(repo_head)
