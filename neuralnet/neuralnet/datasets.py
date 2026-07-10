"""MNIST loader: downloads the official IDX-format files (stdlib urllib
only, no requests/numpy) and parses them by hand with `struct` + `gzip`.
"""

import gzip
import struct
import urllib.request
from pathlib import Path

MNIST_BASE_URL = "https://storage.googleapis.com/cvdf-datasets/mnist/"
MNIST_FILES = {
    "train_images": "train-images-idx3-ubyte.gz",
    "train_labels": "train-labels-idx1-ubyte.gz",
    "test_images": "t10k-images-idx3-ubyte.gz",
    "test_labels": "t10k-labels-idx1-ubyte.gz",
}

IMAGE_MAGIC = 2051
LABEL_MAGIC = 2049


def _download(filename: str, cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    dest = cache_dir / filename
    if not dest.exists():
        urllib.request.urlretrieve(MNIST_BASE_URL + filename, dest)
    return dest


def read_idx_images(path: Path) -> list[list[float]]:
    """Parses the IDX3 image format: 4-byte magic, 4-byte count, 4-byte
    rows, 4-byte cols (all big-endian), then count*rows*cols raw bytes.
    Pixels are normalised to [0, 1].
    """
    with gzip.open(path, "rb") as f:
        magic, count, rows, cols = struct.unpack(">IIII", f.read(16))
        if magic != IMAGE_MAGIC:
            raise ValueError(f"Unexpected magic number {magic} in {path}, expected {IMAGE_MAGIC}")
        raw = f.read(count * rows * cols)

    stride = rows * cols
    return [[b / 255.0 for b in raw[i * stride : (i + 1) * stride]] for i in range(count)]


def read_idx_labels(path: Path) -> list[int]:
    """Parses the IDX1 label format: 4-byte magic, 4-byte count, then
    count raw label bytes (0-9)."""
    with gzip.open(path, "rb") as f:
        magic, count = struct.unpack(">II", f.read(8))
        if magic != LABEL_MAGIC:
            raise ValueError(f"Unexpected magic number {magic} in {path}, expected {LABEL_MAGIC}")
        raw = f.read(count)
    return list(raw)


def load_mnist(
    cache_dir: str = "~/.neuralnet_data/mnist",
    train_limit: int | None = None,
    test_limit: int | None = None,
) -> tuple[list[list[float]], list[int], list[list[float]], list[int]]:
    """Returns (train_images, train_labels, test_images, test_labels).
    Downloads once into cache_dir, reuses the cache on subsequent calls.
    """
    cache_path = Path(cache_dir).expanduser()

    train_images = read_idx_images(_download(MNIST_FILES["train_images"], cache_path))
    train_labels = read_idx_labels(_download(MNIST_FILES["train_labels"], cache_path))
    test_images = read_idx_images(_download(MNIST_FILES["test_images"], cache_path))
    test_labels = read_idx_labels(_download(MNIST_FILES["test_labels"], cache_path))

    if train_limit is not None:
        train_images = train_images[:train_limit]
        train_labels = train_labels[:train_limit]
    if test_limit is not None:
        test_images = test_images[:test_limit]
        test_labels = test_labels[:test_limit]

    return train_images, train_labels, test_images, test_labels
