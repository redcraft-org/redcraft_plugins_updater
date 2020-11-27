import io
from zipfile import ZipFile

class PaperclipPostProcessor():

    def process(self, downloaded_binary, source, name, url, **kwargs):
        with ZipFile(io.BytesIO(downloaded_binary), 'r') as server_jar:
            with server_jar.open('patch.properties') as patch_meta_file:
                # Load properties file and check metadata
                properties_content = patch_meta_file.read().decode('utf-8')
                # UGLY: Could not be bothered to do better
                version = properties_content.split('version=')[1].split('\n')[0].strip()

                if not version:
                    raise ValueError('{} does not contain a valid patch.properties file'.format(name))

                name = '{}-{}.jar'.format(name, version)

        return downloaded_binary, source, name, url
