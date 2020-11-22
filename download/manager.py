import traceback

from tqdm import tqdm

from download.sources.spigotmc_source import SpigotMcSource
from download.sources.jenkins_source import JenkinsSource


class DownloadManager():
    spigotmc_source = None
    jenkins_source = None

    def __init__(self):
        self.spigotmc_source = SpigotMcSource()
        self.jenkins_source = JenkinsSource()

    def download(self, source, name, url, type, **kwargs):
        source_manager = None

        try:
            source_manager = getattr(self, '{}_source'.format(source))
        except AttributeError:
            pass

        if not source_manager:
            raise ValueError('Source {} is not supported'.format(source))

        downloaded_binary = source_manager.download_element(url, **kwargs)

        print('{} type {} size {}'.format(name, type, len(downloaded_binary)))

    def download_resources(self, resources):
        for resource in tqdm(resources):
            try:
                self.download(**resource)
            except:
                traceback.print_exc()
