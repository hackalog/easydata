from contextlib import contextmanager
from tempfile import mkdtemp
from pathlib import Path
import pytest
import shutil

from ..data.utils import iter_directory


@contextmanager
def dir_temp() -> Path:
    path = Path(mkdtemp())
    try:
        yield path
    finally:
        shutil.rmtree(path)


def test_iter_directory_empty():
    with dir_temp() as d:
        assert list(iter_directory(d)) == []


def test_iter_directory_flat():
    with dir_temp() as d:
        (d / "qwer").touch()
        (d / "asdf").touch()
        (d / "ghgh").touch()
        (d / "1234").touch()
        assert list(iter_directory(d)) == [d / i for i in ["1234", "asdf", "ghgh", "qwer"]]


def test_iter_directory_deep():
    with dir_temp() as d:
        (d / "a" / "b" / "a" / "A").mkdir(parents=True)
        (d / "a" / "hoho").touch()
        (d / "1").touch()
        (d / "a" / "b" / "a" / "A" / "v").touch()
        (d / "a" / "b" / "3").touch()
        (d / "a" / "b" / "z").touch()
        assert list(iter_directory(d)) == [
            d / i
            for i in ["1", "a", "a/b", "a/b/3", "a/b/a", "a/b/a/A", "a/b/a/A/v", "a/b/z", "a/hoho"]
        ]
