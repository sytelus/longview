from typing import Dict, Any, Iterator, Union
from .zmq_stream import ZmqStream
from .file_stream import FileStream
from .stream import Stream
from .stream_union import StreamUnion

class StreamFactory:

    def __init__(self)->None:
        self._reset()

    def _reset(self):
        self._streams:Dict[str, Stream] = {}
        self.closed = False

    def close(self):
        if not self.closed:
            for stream in self._streams.values():
                stream.close()
            self._reset()
            self.closed = True

    def __enter__(self):
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def get_streams(self, stream_types:Sequence[str], for_write:bool=None)->Stream:
        streams = [self._create_stream_by_string(stream_type, for_write) for stream_type in stream_types]
        return streams

    def get_combined_stream(self, stream_types:Sequence[str], for_write:bool=None)->Stream:
        streams = [self._create_stream_by_string(stream_type, for_write) for stream_type in stream_types]
        if len(streams) == 1:
            return _streams[0]
        else:
            # we create new union of child but this is not necessory
            return StreamUnion(streams, for_write=for_write)

    def _create_stream_by_string(self, stream_type:str, for_write:bool)->Stream:
        parts = stream_type.split(':', 1) if stream_type is not None else ['']
        stream_type = parts[0]
        stream_args = parts[1] if len(parts) > 1 else None

        if stream_type == 'tcp':
            port_offset = int(stream_args or 0)
            stream_name = '{}:{}'.format(stream_type, port_offset)
            if stream_name not in self._streams:
                self._streams[stream_name] = ZmqStream(for_write=for_write, 
                    port_offset=port_offset, stream_name=stream_name, block_until_connected=False)
            # else we already have this stream
            return self._streams[stream_name]

        if stream_type == 'file':
            if stream_args is None:
                raise ValueError('File name must be specified for stream type "file"')
            stream_name = '{}:{}'.format(stream_type, stream_args)
            if stream_name not in self._streams:
                self._streams[stream_name] = FileStream(for_write=for_write, 
                    file_name=stream_args, stream_name=stream_name)
            # else we already have this stream
            return self._streams[stream_name]

        if stream_type == '':
            return Stream()

        raise ValueError('stream_type "{}" has unknown type'.format(stream_type))


