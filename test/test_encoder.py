import datetime
from decimal import Decimal
import enum
import uuid

import pytest
from pytz import UTC

from kw.json import default_encoder


class Custom:
    pass


class HTML:
    def __html__(self):
        return 'foo'


class SomeEnum(enum.Enum):
    red = 1
    green = 2


UUID = uuid.uuid4()


@pytest.mark.parametrize('value, expected', (
        ({1}, [1]),
        (Decimal('1'), '1'),
        (UUID, str(UUID)),
        (datetime.datetime(2018, 1, 1), '2018-01-01T00:00:00'),
        (datetime.datetime(2018, 1, 1, tzinfo=UTC), '2018-01-01T00:00:00+00:00'),
        (datetime.date(2018, 1, 1), '2018-01-01'),
        (HTML(), 'foo'),
        (SomeEnum.red, 'red'),
        ({'foo': 1}.items(), {'foo': 1}),
))
def test_daisy_encoder(value, expected):
    assert default_encoder(value) == expected


def test_unknown_raises():
    class Foo(object):
        bar = True

    with pytest.raises(TypeError):
        default_encoder(Foo())
