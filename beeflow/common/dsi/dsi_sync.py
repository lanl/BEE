from dsi.core import Sync

from beeflow.common.paths import workdir

class DSISync:
    def __init__(self):
        self.sync = Sync(f'{workdir()}/dsi_fs.db')
    



dsi_sync = DSISync()
