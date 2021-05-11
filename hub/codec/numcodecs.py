from io import BytesIO
from abc import ABC, abstractmethod  # type: ignore
import numcodecs  # type: ignore

import numpy as np


class BaseNumCodec(ABC):
    """Base class for numcodec compressors"""

    @abstractmethod
    def encode(self, array: np.ndarray) -> bytes:
        pass

    @abstractmethod
    def decode(self, bytes: bytes) -> np.ndarray:
        pass


class NumPy(BaseNumCodec):
    def __init__(self):
        super().__init__()

    @property
    def __name__(self):
        return "numpy"

    def encode(self, array: np.ndarray) -> bytes:
        """
        Encode given array

        Example:
            arr = np.arange(100, 100, 2, dtype='uint8')
            arr_encoded = numpy_codec.encode(x)

        Args:
            array (np.ndarray): Data to be encoded

        Returns:
            Encoded data.
        """
        with BytesIO() as f:
            np.save(f, array, allow_pickle=True)
            return f.getvalue()

    def decode(self, bytes_: bytes) -> np.ndarray:
        """
        Decode data from buffer.

        Example:
            arr_decoded = numpy_codec.decode(arr_encoded)

        Args:
            bytes_ (bytes): Encoded data

        Returns:
            Decoded data.
        """
        with BytesIO(bytes_) as f:
            return np.load(f, allow_pickle=True)


class Lz4(BaseNumCodec):
    def __init__(self, **kwargs):
        """
        Initialize Lz4 compressor

        Args:
            acceleration (int): Acceleration level.
            The larger the acceleration value, the faster the algorithm, but also the lesser the compression.
        """
        if kwargs and "acceleration" not in kwargs:
            raise ValueError("Invalid args:", kwargs.keys())
        acceleration = kwargs.get("acceleration", numcodecs.lz4.DEFAULT_ACCELERATION)
        self.compressor = numcodecs.lz4.LZ4(acceleration)
        self._msgpack = numcodecs.MsgPack()

    @property
    def __name__(self):
        return "lz4"

    def encode(self, array: np.ndarray) -> bytes:
        """
        Encode given array

        Example:
            arr = np.arange(100, 100, 2, dtype='uint8')
            arr_encoded = lz4_codec.encode(x)

        Args:
            array (np.ndarray): Data to be encoded

        Returns:
            Encoded data.
        """
        return self._msgpack.encode(
            [
                {
                    "item": self.compressor.encode(array),
                    "dtype": array.dtype.name,
                    "shape": array.shape,
                }
            ]
        )

    def decode(self, bytes_: bytes) -> np.ndarray:
        """
        Decode data from buffer.

        Example:
            arr_decoded = lz4_codec.decode(arr_encoded)

        Args:
            bytes_ (bytes): Encoded data

        Returns:
            Decoded data.
        """
        data = self._msgpack.decode(bytes_)[0]
        decoded_buf = self.compressor.decode(data["item"])
        arr = np.frombuffer(decoded_buf, dtype=np.dtype(data["dtype"]))
        arr = arr.reshape(data["shape"])
        return arr


class Zstd(BaseNumCodec):
    def __init__(self, **kwargs):
        """
        Initialize Zstd compressor

        Args:
            level (int): Compression level (1-22).
        """
        if kwargs and "level" not in kwargs:
            raise ValueError("Invalid args:", kwargs.keys())
        level = kwargs.get("level", numcodecs.zstd.DEFAULT_CLEVEL)
        self.compressor = numcodecs.zstd.Zstd(level)
        self._msgpack = numcodecs.MsgPack()

    @property
    def __name__(self):
        return "zstd"

    def encode(self, array: np.ndarray) -> bytes:
        """
        Encode given array

        Example:
            arr = np.arange(100, 100, 2, dtype='uint8')
            arr_encoded = zstd_codec.encode(x)

        Args:
            array (np.ndarray): Data to be encoded

        Returns:
            Encoded data.
        """
        return self._msgpack.encode(
            [
                {
                    "item": self.compressor.encode(array),
                    "dtype": array.dtype.name,
                    "shape": array.shape,
                }
            ]
        )

    def decode(self, bytes_: bytes) -> np.ndarray:
        """
        Decode data from buffer.

        Example:
            arr_decoded = zstd_codec.decode(arr_encoded)

        Args:
            bytes_ (bytes): Encoded data

        Returns:
            Decoded data.
        """
        data = self._msgpack.decode(bytes_)[0]
        decoded_buf = self.compressor.decode(data["item"])
        arr = np.frombuffer(decoded_buf, dtype=np.dtype(data["dtype"]))
        arr = arr.reshape(data["shape"])
        return arr