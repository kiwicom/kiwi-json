try:
    import enum  # pylint: disable=W0611
except ImportError:
    # Python 2.7
    try:
        import enum34 as enum  # pylint: disable=W0611
    except ImportError:
        enum = None

try:
    from simplejson.encoder import JSONEncoder as BaseJSONEncoder  # pylint: disable=W0611
    from simplejson import dumps as json_dumps
except ImportError:
    from json.encoder import JSONEncoder as BaseJSONEncoder  # pylint: disable=W0611
    from json import dumps as json_dumps
