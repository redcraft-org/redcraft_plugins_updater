from utils.plugin_info import extract_plugin_info_from_binary

class PluginPostprocessor():

    def process(self, downloaded_binary, source, name, url, **kwargs):
        plugin_info = extract_plugin_info_from_binary(downloaded_binary)

        name = '{}-{}.jar'.format(name, plugin_info['version'])

        return downloaded_binary, source, name, url
