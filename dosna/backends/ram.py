#!/usr/bin/env python
"""backend RAM keeps every data structure in memory"""

import logging

import numpy as np

from dosna.backends import Backend
from dosna.backends.base import (BackendConnection, BackendDataChunk,
                                 BackendDataset)

log = logging.getLogger(__name__)


class MemConnection(BackendConnection):
    """
    A Memory Connection represents a dictionary.
    """

    def __init__(self, *args, **kwargs):
        super(MemConnection, self).__init__(*args, **kwargs)
        self.datasets = {}

    def create_dataset(self, name, shape=None, dtype=np.float32, fillvalue=0,
                       data=None, chunks=None):

        if not ((shape is not None and dtype is not None) or data is not None):
            raise Exception('Provide `shape` and `dtype` or `data`')
        if self.has_dataset(name):
            raise Exception('Dataset `%s` already exists' % name)

        if data is not None:
            shape = data.shape
            dtype = data.dtype

        if chunks is None:
            csize = shape
        else:
            csize = chunks
        chunks_needed = (np.ceil(np.asarray(shape, float) / csize)).astype(int)

        log.debug('Creating Dataset `%s`', name)
        self.datasets[name] = None  # Key `name` has to exist
        dataset = MemDataset(self, name, shape, dtype, fillvalue,
                             chunks_needed, csize)
        self.datasets[name] = dataset
        return dataset

    def get_dataset(self, name):
        if not self.has_dataset(name):
            raise Exception('Dataset `%s` does not exist' % name)
        return self.datasets[name]

    def has_dataset(self, name):
        return name in self.datasets

    def del_dataset(self, name):
        if not self.has_dataset(name):
            raise Exception('Dataset `%s` does not exist' % name)
        log.debug('Removing Dataset `%s`', name)
        del self.datasets[name]


class MemDataset(BackendDataset):

    def __init__(self, pool, name, shape, dtype, fillvalue, chunks, csize):
        super(MemDataset, self).__init__(pool, name, shape, dtype, fillvalue,
                                         chunks, csize)
        self.data_chunks = {}
        self._populate_chunks()

    def _populate_chunks(self):
        for idx in np.ndindex(*self.chunks):
            self.create_chunk(idx)

    def create_chunk(self, idx, data=None, slices=None):
        if self.has_chunk(idx):
            raise Exception('DataChunk `{}` already exists'.format(idx))

        self.data_chunks[idx] = None

        chunk = MemDataChunk(self, idx, 'Chunk {}'.format(idx),
                             self.chunk_size, self.dtype, self.fillvalue)
        if data is not None:
            slices = slices or slice(None)
            chunk.set_data(data, slices=slices)

        self.data_chunks[idx] = chunk
        return chunk

    def get_chunk(self, idx):
        if self.has_chunk(idx):
            return self.data_chunks[idx]
        return self.create_chunk(idx)

    def has_chunk(self, idx):
        return idx in self.data_chunks

    def del_chunk(self, idx):
        if self.has_chunk(idx):
            del self.data_chunks[idx]


class MemDataChunk(BackendDataChunk):

    def __init__(self, dataset, idx, name, shape, dtype, fillvalue):
        super(MemDataChunk, self).__init__(dataset, idx, name, shape,
                                           dtype, fillvalue)
        self.data = np.full(shape, fillvalue, dtype)

    def get_data(self, slices=None):
        return self.data[slices]

    def set_data(self, values, slices=None):
        self.data[slices] = values


_backend = Backend('ram', MemConnection, MemDataset, MemDataChunk)
