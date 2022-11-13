import os
import shutil
import tempfile
import uuid
from subprocess import DEVNULL
from unittest import TestCase, skipIf

import cwltool.factory
import pkg_resources
import yaml
from cwltool.context import RuntimeContext
from cwltool.errors import WorkflowException

class TestConsoleScripts(TestCase):
    maxDiff = None
    here = os.path.abspath(os.path.dirname(__file__))
    repo_like_dir = os.path.join(here, 'repo-like')
    repo_like_dir_imports = os.path.join(here, 'repo-like-with-imports')

    @skipIf("TRAVIS_IGNORE_DOCKER" in os.environ and os.environ["TRAVIS_IGNORE_DOCKER"] == "true",
            "Skipping this test on Travis CI.")
    def test_repo2cwl(self):
        output_dir = tempfile.mkdtemp()
        print(f'output directory:\t{output_dir}')
        repo2cwl = pkg_resources.load_entry_point('ipython2cwl', 'console_scripts', 'jupyter-repo2cwl')
        self.assertEqual(
            0,
            repo2cwl(['-o', output_dir, self.repo_like_dir])
        )
        self.assertListEqual(['example1.cwl'], [f for f in os.listdir(output_dir) if not f.startswith('.')])

        with open(os.path.join(output_dir, 'example1.cwl')) as f:
            print('workflow file')
            print(20 * '=')
            print(f.read())
            print(20 * '=')

        runtime_context = RuntimeContext()
        runtime_context.outdir = output_dir
        runtime_context.basedir = output_dir
        runtime_context.default_stdout = DEVNULL
        runtime_context.default_stderr = DEVNULL
        fac = cwltool.factory.Factory(runtime_context=runtime_context)

        example1_tool = fac.make(os.path.join(output_dir, 'example1.cwl'))
        result = example1_tool(
            datafilename={
                'class': 'File', 'location': os.path.join(self.repo_like_dir, 'data.yaml')
            },
            messages=["hello", "test", "!!!"]
        )
        with open(result['results_filename']['location'][7:]) as f:
            new_data = yaml.safe_load(f)
        self.assertDictEqual({'entry1': 2, 'entry2': 'foo', 'entry3': 'bar'}, new_data)
        with open(result['messages_outputs']['location'][7:]) as f:
            message = f.read()
        self.assertEqual("hello test !!!", message)
        shutil.rmtree(output_dir)

    @skipIf("TRAVIS_IGNORE_DOCKER" in os.environ and os.environ["TRAVIS_IGNORE_DOCKER"] == "true",
            "Skipping this test on Travis CI.")
    def test_repo2cwl_with_imports(self):
        output_dir = tempfile.mkdtemp()
        print(f'output directory:\t{output_dir}')
        repo2cwl = pkg_resources.load_entry_point('ipython2cwl', 'console_scripts', 'jupyter-repo2cwl')
        self.assertEqual(
            0,
            repo2cwl(['-o', output_dir, self.repo_like_dir_imports])
        )
        self.assertListEqual(['example1_import.cwl'], [f for f in os.listdir(output_dir) if not f.startswith('.')])

        with open(os.path.join(output_dir, 'example1_import.cwl')) as f:
            print('workflow file')
            print(20 * '=')
            print(f.read())
            print(20 * '=')

        runtime_context = RuntimeContext()
        runtime_context.outdir = output_dir
        runtime_context.basedir = output_dir
        runtime_context.default_stdout = DEVNULL
        runtime_context.default_stderr = DEVNULL
        fac = cwltool.factory.Factory(runtime_context=runtime_context)

        try:
            example1_tool = fac.make(os.path.join(output_dir, 'example1_import.cwl'))
        except WorkflowException:
            self.fail("Execution failed")


        result = example1_tool(
            datafilename={
                'class': 'File', 'location': os.path.join(self.repo_like_dir, 'data.yaml')
            },
            messages=["hello", "test", "!!!"]
        )
        with open(result['results_filename']['location'][7:]) as f:
            new_data = yaml.safe_load(f)
        self.assertDictEqual({'entry1': 2, 'entry2': 'foo', 'entry3': 'bar'}, new_data)
        with open(result['messages_outputs']['location'][7:]) as f:
            message = f.read()
        self.assertEqual("hello test !!!", message)
        shutil.rmtree(output_dir)

    def test_repo2cwl_output_dir_does_not_exists(self):
        random_dir_name = str(uuid.uuid4())
        repo2cwl = pkg_resources.load_entry_point('ipython2cwl', 'console_scripts', 'jupyter-repo2cwl')
        with self.assertRaises(SystemExit):
            repo2cwl(['-o', random_dir_name, self.repo_like_dir])
