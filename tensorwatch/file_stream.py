from .stream import Stream
import pickle
from typing import Any
from . import utils
from .lv_types import StreamItem

class FileStream(Stream):
    def __init__(self, for_write:bool, file_name:str, stream_name:str=None, console_debug:bool=False):
        super(FileStream, self).__init__(stream_name=stream_name or file_name, console_debug=console_debug)

        self._file = open(file_name, 'wb' if for_write else 'rb')
        self.file_name = file_name
        self.for_write = for_write
        utils.debug_log('FileStream started', self.file_name, verbosity=1)

    def close(self):
        if not self.file.closed:
            self._file.close()
            self._file = None
            utils.debug_log('FileStream is closed', self.file_name, verbosity=1)
        super(ZmqStream, self).close()

    def write(self, val:Any, topic=None):
        super(FileStream, self).write(val)
        if self.for_write:
            pickle.dump(val, self._file)

    def read_all(self):
        if self.for_write:
            raise IOError('Cannot use read_all because FileSteam is opened with for_write=True')
        if self._file is not None:
            while not utils.is_eof(self._file):
                stream_item = pickle.load(self._file)
                self.write(stream_item)
