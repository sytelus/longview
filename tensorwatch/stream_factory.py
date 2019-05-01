from typing import Dict, Any
from .zmq_stream import ZmqStream
from .stream import Stream


class StreamFactory:
    def __init__(self):
        self._streams:Dict[str, Stream] = {}

    def append(self, normalized_name:str, stream:Stream):
        self._streams[normalized_name] = stream

    def create_stream(self, name:str, default_spec:Any=None):
        normalized_name, parts = StreamFactory.normalize_name(name, default_spec)
        stream = self._streams.get(normalized_name, None)
        if stream is not None:
            return stream

        if parts[0] == 'zmqpub':
            stream = ZmqStream(for_write=True, port_offset=int(parts[1]), stream_name=normalized_name, 
                                     block_until_connected=False) # should this be configurable? Is it even needed?
        else:
             raise ValueError('Stream name "{}" has unknown type'.format(name))

        self.append(normalized_name, stream)
        return stream

    @staticmethod
    def normalize_name(name:str, default_spec:Any)->str:
        parts = name.split(':', 1)

        if len(parts) < 1:
            raise ValueError('Stream name "{}" must have at least one part'.format(name))
        if len(parts[0]) <= 1: # no type specified or is drive letter
            if len(parts) > 1:
                raise ValueError('Stream name "{}" must not have more than drive or type specifiers'.format(name))
            return 'file:' + name, ['file', name]
        if parts[0] == 'file':
            if len(parts) < 2:
                if default_spec is None:
                    raise ValueError('File stream name "{}" must have file name'.format(name))
                return 'file:' + default_spec, ['file', default_spec]
            return name, parts
        if parts[0] == 'zmqpub':
            if len(parts) < 2:
                return 'zmqpub:0', ['zmqpub', default_spec or 0]
            return name, parts
        raise ValueError('Stream name "{}" has unknown type'.format(name))

