try:
    import enum  # pylint: disable=W0611
except ImportError:
    enum = None

try:
    from simplejson.encoder import (  # pylint: disable=W0611
        JSONEncoder as BaseJSONEncoder,
    )
    from simplejson import dumps as json_dumps  # pylint: disable=W0611
    from simplejson import dump as json_dump  # pylint: disable=W0611
    from simplejson import loads as json_loads  # pylint: disable=W0611
    from simplejson import load as json_load  # pylint: disable=W0611

    simplejson_available = True
except ImportError:
    from json.encoder import JSONEncoder as BaseJSONEncoder  # pylint: disable=W0611
    from json import dumps as json_dumps  # pylint: disable=W0611
    from json import dump as json_dump  # pylint: disable=W0611
    from json import loads as json_loads  # pylint: disable=W0611
    from json import load as json_load  # pylint: disable=W0611

    simplejson_available = False
from .exceptions import KiwiJsonError

from dataclasses import dataclass


@dataclass
class DataclassItem:
    attrib: int


def prevent_unexpected_argument_error(func):
    __use_decimal_error_message = (
        "You can't serialise Decimal as JSON number safely with the standard 'json' module. "
        "Make sure you have 'simplejson' or similar installed."
    )

    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except TypeError as err:
            if str(err).endswith(
                "__init__() got an unexpected keyword argument 'use_decimal'"
            ):
                raise KiwiJsonError(  # pylint: disable=W0707
                    __use_decimal_error_message
                )
            raise
        return result

    return wrapper


_dumps = prevent_unexpected_argument_error(json_dumps)
_dump = prevent_unexpected_argument_error(json_dump)
_loads = prevent_unexpected_argument_error(json_loads)
_load = prevent_unexpected_argument_error(json_load)
