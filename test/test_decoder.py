from decimal import Decimal

import pytest

from kw.json import loads
from kw.json.exceptions import KiwiJsonError

try:
    from simplejson import loads as simplejson_loads
except ImportError:
    simplejson_loads = None


@pytest.mark.skipif(
    simplejson_loads is None, reason="Decimal encoding with simplejson only"
)
@pytest.mark.parametrize(
    "value, expected",
    [
        ('"1"', "1"),
        ("1", Decimal("1")),
        ("-1", Decimal("-1")),
        ("1.0", Decimal("1.0")),
        ("0.123456789123456789", Decimal("0.123456789123456789")),
        ('{"num": 0.123456789123456789}', {"num": Decimal("0.123456789123456789")}),
    ],
    # ids=["str", "int", "neg_int", "float", "long_float", "object"]
)
def test_simplejson_encoder_with_decimal(value, expected):
    assert loads(value, use_decimal=True) == expected


@pytest.mark.skipif(simplejson_loads, reason="Standard json module only")
def test_json_with_use_decimal_argument():
    with pytest.raises(KiwiJsonError, match=r".*Decimal.*"):
        loads("{}", use_decimal=True)
