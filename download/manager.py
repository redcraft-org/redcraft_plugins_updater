
from download.sources.spigotmc_source import SpigotMcSource


class DownloadManager():
    spigotmc_source = None

    def __init__(self):
        self.spigotmc_source = SpigotMcSource()
