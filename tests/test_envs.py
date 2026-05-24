import pathlib
import tomllib
import unittest


class TestEnvsProject(unittest.TestCase):
    def test_envs_pyproject_has_workflow_dependencies(self):
        repo_head = pathlib.Path(__file__).resolve().parent.parent
        pyproject_path = repo_head / "envs" / "pyproject.toml"
        lock_path = repo_head / "envs" / "uv.lock"

        self.assertTrue(pyproject_path.exists())
        self.assertTrue(lock_path.exists())

        with pyproject_path.open("rb") as file_stream:
            pyproject = tomllib.load(file_stream)
        with lock_path.open("rb") as file_stream:
            lock_file = tomllib.load(file_stream)

        dependencies = pyproject["project"]["dependencies"]
        locked_package_names = {package["name"] for package in lock_file["package"]}
        self.assertTrue(any(dependency.startswith("dandi") for dependency in dependencies))
        self.assertTrue(any(dependency.startswith("s5cmd") for dependency in dependencies))
        self.assertIn("dandi", locked_package_names)
        self.assertIn("s5cmd", locked_package_names)
