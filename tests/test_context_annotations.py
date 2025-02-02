import json
import os.path

import unittest

from sparc.curation.tools import context_annotations
from sparc.curation.tools.contextinfo import ContextInfoAnnotation
from sparc.curation.tools.utilities import convert_to_bytes

from gitresources import dulwich_checkout, setup_resources, dulwich_proper_stash_and_drop

here = os.path.abspath(os.path.dirname(__file__))


class ScaffoldAnnotationTestCase(unittest.TestCase):

    _repo = None

    @classmethod
    def setUpClass(cls):
        cls._repo = setup_resources()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._repo.close()

    def setUp(self):
        dulwich_checkout(self._repo, b"main")
        self._max_size = convert_to_bytes("2MiB")

    def tearDown(self):
        dulwich_proper_stash_and_drop(self._repo)

    def test_context_info_annotations(self):
        dulwich_checkout(self._repo, b"origin/scaffold_annotations_correct")
        dataset_dir = os.path.join(here, "resources")
        context_files = context_annotations.search_for_context_data_files(dataset_dir, convert_to_bytes("2MiB"))

        self.assertEqual(1, len(context_files))
        with open(context_files[0]) as f:
            content = json.load(f)

        self.assertEqual("0.1.0", content["version"])
        self.assertEqual("Generic rat brainstem scaffold", content["heading"])

        ci = ContextInfoAnnotation(os.path.basename(context_files[0]), context_files[0])
        self._compare_update(ci, content, "Generic rat brainstem scaffold")

    def test_context_info_bare_scaffold_new_layout(self):
        dulwich_checkout(self._repo, b"origin/no_banner_no_scaffold_annotations_II")
        dataset_dir = os.path.join(here, "resources")
        context_files = context_annotations.search_for_context_data_files(dataset_dir, convert_to_bytes("2MiB"))

        self.assertEqual(1, len(context_files))
        with open(context_files[0]) as f:
            content = json.load(f)

        self.assertEqual("0.1.0", content["version"])
        self.assertEqual("Generic rat brainstem scaffold", content["heading"])

        ci = ContextInfoAnnotation(os.path.basename(context_files[0]), context_files[0])
        self._compare_update(ci, content, "Generic rat brainstem scaffold")

    def test_context_info_bare_scaffold_multiple_views_thumbnails(self):
        dulwich_checkout(self._repo, b"origin/no_scaffold_annotations_multiple_views")
        dataset_dir = os.path.join(here, "resources")
        context_files = context_annotations.search_for_context_data_files(dataset_dir, convert_to_bytes("2MiB"))

        self.assertEqual(1, len(context_files))
        with open(context_files[0]) as f:
            content = json.load(f)

        self.assertEqual("0.1.0", content["version"])
        self.assertEqual("Generic rat brainstem scaffold", content["heading"])

        ci = ContextInfoAnnotation(os.path.basename(context_files[0]), context_files[0])
        self._compare_update(ci, content, "Generic rat brainstem scaffold", 2)

    def test_context_info_bare_multiple_scaffolds(self):
        dulwich_checkout(self._repo, b"origin/no_scaffold_annotations_multiple_scaffolds")
        dataset_dir = os.path.join(here, "resources")
        context_files = context_annotations.search_for_context_data_files(dataset_dir, convert_to_bytes("2MiB"))

        self.assertEqual(1, len(context_files))
        with open(context_files[0]) as f:
            content = json.load(f)

        self.assertEqual("0.1.0", content["version"])
        self.assertEqual("Generic rat brainstem scaffold", content["heading"])

        ci = ContextInfoAnnotation(os.path.basename(context_files[0]), context_files[0])
        self._compare_update(ci, content, "Generic rat brainstem scaffold")

    def test_context_info_multiple_metadata(self):
        dulwich_checkout(self._repo, b"origin/context_annotation_multiple_metadata")
        dataset_dir = os.path.join(here, "resources")
        context_files = context_annotations.search_for_context_data_files(dataset_dir, convert_to_bytes("2MiB"))

        self.assertEqual(2, len(context_files))
        with open(context_files[0]) as f:
            content = json.load(f)

        self.assertEqual("0.1.0", content["version"])
        self.assertEqual("Distribution of 5-HT", content["heading"])

        ci = ContextInfoAnnotation(os.path.basename(context_files[0]), context_files[0])
        self._compare_update(ci, content, "Distribution of 5-HT", 1, 1)

    def test_context_info_scaffold_with_additional_images(self):
        dulwich_checkout(self._repo, b"origin/no_scaffold_annotations_extra_images")
        dataset_dir = os.path.join(here, "resources")
        context_files = context_annotations.search_for_context_data_files(dataset_dir, convert_to_bytes("2MiB"))

        self.assertEqual(1, len(context_files))
        with open(context_files[0]) as f:
            content = json.load(f)

        self.assertEqual("0.1.0", content["version"])
        self.assertEqual("Generic rat brainstem scaffold", content["heading"])

        ci = ContextInfoAnnotation(os.path.basename(context_files[0]), context_files[0])
        self._compare_update(ci, content, "Generic rat brainstem scaffold")

    def _compare_update(self, ci, content, heading='', views_len=0, samples_len=0):
        self.assertEqual("0.2.0", ci.get_version())
        self.assertEqual('', ci.get_heading())
        self.assertEqual(0, len(ci.get_views()))
        self.assertEqual(0, len(ci.get_samples()))

        ci.update(content)

        self.assertEqual("0.2.0", ci.get_version())
        self.assertEqual(heading, ci.get_heading())
        self.assertEqual(views_len, len(ci.get_views()))
        self.assertEqual(samples_len, len(ci.get_samples()))


def dump_json(files):
    for c in files:
        with open(c) as f:
            print(json.load(f))


if __name__ == "__main__":
    unittest.main()
