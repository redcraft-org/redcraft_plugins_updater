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

    def test_extract_paper_plugin_info(self):
        # Modern Paper plugins ship only paper-plugin.yml, with no plugin.yml
        # alongside it (e.g. AntiRedstoneClock-Remastered).
        jar_buffer = io.BytesIO()
        with ZipFile(jar_buffer, "w") as jar_contents:
            jar_contents.writestr(
                "paper-plugin.yml",
                'name: MockedPaperPlugin\nversion: 2.9.1\napi-version: "1.19"\n',
            )

        expected_output = {"name": "MockedPaperPlugin", "version": "2.9.1"}

        actual_output = self.plugin_post_processor.extract_plugin_info(
            jar_buffer.getvalue()
        )

        self.assertEqual(expected_output, actual_output)

    def test_plugin_yml_wins_over_paper_plugin_yml(self):
        # A plugin shipping both must keep the name it resolved to before
        # paper-plugin.yml was added, so bucket keys stay stable.
        jar_buffer = io.BytesIO()
        with ZipFile(jar_buffer, "w") as jar_contents:
            jar_contents.writestr("plugin.yml", "name: Legacy\nversion: 1.0.0\n")
            jar_contents.writestr("paper-plugin.yml", "name: Modern\nversion: 2.0.0\n")

        expected_output = {"name": "Legacy", "version": "1.0.0"}

        actual_output = self.plugin_post_processor.extract_plugin_info(
            jar_buffer.getvalue()
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
