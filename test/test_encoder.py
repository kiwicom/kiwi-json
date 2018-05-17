import datetime
from decimal import Decimal
import enum

import pytest

from kw.json import default_encoder


def test_unknown_raises():
    class Foo(object):
        bar = True

    with pytest.raises(TypeError):
        default_encoder(Foo())


def test_date():
    dt = datetime.date(2018, 1, 2)

    assert default_encoder(dt) == '2018-01-02'


def test_datetime():
    dt = datetime.datetime(2018, 1, 2, 3, 4, 5)

    assert default_encoder(dt) == '2018-01-02T03:04:05'


def test_decimal():
    dec = Decimal(100 * 1.19)

    assert default_encoder(dec) == '119'


def test_enum():
    class Cats(enum.Enum):
        foo = 1
        bar = 2

    cat = Cats.foo
    assert default_encoder(cat) == 'foo'
