import os
from zipfile import ZipFile

import yaml
from tqdm import tqdm

def get_existing_plugins(output_folder):
    plugins = {}

    # Iterate through the folder and explore plugin metadata
    for file_name in tqdm(os.listdir(output_folder), desc='Exploring current versions'):
        file = os.path.join(output_folder, file_name)
        if file.endswith('.jar'):
            try:
                plugin_metadata = extract_plugin_info(file)
                plugin_name = plugin_metadata['name']
                plugins[plugin_name] = plugin_metadata
            except Exception as e:
                print('An exception occurred while reading {} ({})'.format(file, e))

    return plugins


def extract_plugin_info(file):
    # In order to be compatible with Bukkit and BungeeCord plugins, we need to check two files
    possible_plugin_metadata_files = ['plugin.yml', 'bungee.yml']
    last_exception = None
    for possible_plugin_metadata_file in possible_plugin_metadata_files:
        try:
            with ZipFile(file, 'r') as plugin_contents:
                with plugin_contents.open(possible_plugin_metadata_file) as plugin_meta_file:
                    # Load yml file and check metadata
                    plugin_metadata = yaml.safe_load(plugin_meta_file)
                    plugin_name = plugin_metadata.get('name')
                    plugin_version = plugin_metadata.get('version')
                    if not plugin_name or not plugin_version:
                        raise ValueError('{} is not a valid plugin metadata file'.format(possible_plugin_metadata_file))
                    return {
                        'name': plugin_name,
                        'version': plugin_version
                    }
        except Exception as e:
            last_exception = e

    # If we're here, it means we didn't return and everything failed, so we return the last exception we saw
    raise last_exception
