import pytest

from kw.json import mask_dict, mask_dict_factory


@pytest.mark.parametrize(
    "value, expected",
    (
        (None, {}),
        ((("test", 1),), {"test": 1}),
        ([("test", 1), ("testo", 2)], {"test": 1, "testo": 2}),
        ({"test": 1}, {"test": 1}),
        ({"secret": "FOO"}, {"secret": "-- MASKED --"}),
        ({"public_key": "FOO"}, {"public_key": "FOO"}),
    ),
)
def test_mask_dict(value, expected):
    assert mask_dict(value) == expected


@pytest.mark.parametrize(
    "blacklist, whitelist, value, expected",
    (
        (frozenset(), frozenset(), {"secret": "42"}, {"secret": "42"}),
        (
            frozenset(["doom"]),
            frozenset(["doomed"]),
            {"doomed": "we_are", "dooming": "nope"},
            {"doomed": "we_are", "dooming": "-- MASKED --"},
        ),
    ),
)
def test_mask_dict_factory(blacklist, whitelist, value, expected):
    my_mask_dict = mask_dict_factory(blacklist=blacklist, whitelist=whitelist)
    assert my_mask_dict(value) == expected
