import os
import unittest

from download.post_processors.plugin_post_processor import PluginPostProcessor


class PluginPostProcessorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plugin_post_processor = PluginPostProcessor()

        fake_plugin = os.path.join(
            os.path.dirname(__file__), "fixtures/fake_plugin.jar"
        )

        with open(fake_plugin, "rb") as fake_plugin_file:
            cls.fake_plugin_contents = fake_plugin_file.read()

    def test_extract_plugin_info(self):
        expected_output = {"name": "MockedPlugin", "version": "0.69.420-SNAPSHOT"}

        actual_output = self.plugin_post_processor.extract_plugin_info(
            self.fake_plugin_contents
        )

        self.assertEqual(expected_output, actual_output)
