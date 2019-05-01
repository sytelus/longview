from .stream import Stream
import pickle

class FileStream(Stream):
    def __init__(self, for_write:bool, file_name:str, stream_name:str=None, console_debug:bool=False):
        super(FileStream, self).__init__(name=stream_name, console_debug=console_debug)

        self._file = open(file_name, 'wb' if for_write else 'rb')
        self.file_name = file_name
        self.for_write = for_write
        utils.debug_log('FileStream started', self.file_name, verbosity=1)

    def close(self):
        if not self.file.closed:
            self._file.close()
            utils.debug_log('FileStream is closed', self.file_name, verbosity=1)

    def __enter__(self):
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def write(self, val:Any, topic=None):
        super(FileStream, self).write(val)
        if self.for_write:
            pickle.dump(val, self._file)

    def read_all(self):
        if self.for_write:
            raise IOError('Cannot use read_all because FileSteam is opened in for_write=True mode')
        if self._file is not None:
            vals = []
            while True:
                try:
                    val = pickle.load(self._file)
                    vals.append(val)
                except EOFError as ex:
                    break
            stream_item = StreamItem(item_index=0, value=vals,
                stream_name=self.stream_name, source_id='', stream_index=0)
            self.write(stream_item)
