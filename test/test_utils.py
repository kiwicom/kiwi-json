import pytest

from kw.json import mask_dict


@pytest.mark.parametrize(
    "value, expected",
    (
        (None, {}),
        ((("test", 1),), {"test": 1}),
        ((("secret", "FOO"),), {"secret": "-- MASKED --"}),
        ((("public_key", "FOO"),), {"public_key": "FOO"}),
    ),
)
def test_mask_dict(value, expected):
    assert mask_dict(value) == expected
