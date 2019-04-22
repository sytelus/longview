from typing import Dict, Any
from .zmq_publisher import ZmqPublisher
from .publisher import Publisher


class PublisherFactory:
    def __init__(self):
        self._publishers:Dict[str, Publisher] = {}

    def append(self, normalized_name:str, publisher:Publisher):
        self._publishers[normalized_name] = publisher

    def create_publisher(self, name:str, default_spec:Any=None):
        normalized_name, parts = PublisherFactory.normalize_name(name, default_spec)
        publisher = self._publishers.get(normalized_name, None)
        if publisher is not None:
            return publisher

        if parts[0] == 'zmq':
            publisher = ZmqPublisher(int(parts[1]), name=normalized_name, 
                                     block_until_connected=False) # should this be configurable? Is it even needed?
        else:
             raise ValueError('Publisher name "{}" has unknown type'.format(name))

        self.append(normalized_name, publisher)
        return publisher

    @staticmethod
    def normalize_name(name:str, default_spec:Any)->str:
        parts = name.split(':', 1)

        if len(parts) < 1:
            raise ValueError('Publisher name "{}" must have at least one part'.format(name))
        if len(parts[0]) <= 1: # no type specified or is drive letter
            if len(parts) > 1:
                raise ValueError('Publisher name "{}" must not have more than drive or type specifiers'.format(name))
            return 'file:' + name, ['file', name]
        if parts[0] == 'file':
            if len(parts) < 2:
                if default_spec is None:
                    raise ValueError('File publisher name "{}" must have file name'.format(name))
                return 'file:' + default_spec, ['file', default_spec]
            return name, parts
        if parts[0] == 'zmq':
            if len(parts) < 2:
                return 'zmq:0', ['zmq', default_spec or 0]
            return name, parts
        raise ValueError('Publisher name "{}" has unknown type'.format(name))

