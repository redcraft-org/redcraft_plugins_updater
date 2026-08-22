import io
import json
import os
import unittest
from zipfile import ZipFile

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

    def test_extract_velocity_plugin_info(self):
        jar_buffer = io.BytesIO()
        with ZipFile(jar_buffer, "w") as jar_contents:
            jar_contents.writestr(
                "velocity-plugin.json",
                json.dumps({"id": "mockedvelocityplugin", "version": "1.2.3"}),
            )

        expected_output = {"name": "mockedvelocityplugin", "version": "1.2.3"}

        actual_output = self.plugin_post_processor.extract_plugin_info(
            jar_buffer.getvalue()
        )

        self.assertEqual(expected_output, actual_output)
