try:
    from simplejson.encoder import JSONEncoder as BaseJSONEncoder  # pylint: disable=W0611
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


try:
    # To avoid a syntax error when type annotations syntax is not available
    exec(  # pylint: disable=exec-used
        """
from dataclasses import dataclass
@dataclass
class DataclassItem:
    attrib: int
    """,
        globals(),
    )
except ImportError:
    DataclassItem = None
