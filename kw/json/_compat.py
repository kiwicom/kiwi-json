try:
    import enum
except ImportError:
    # Python 2.7
    try:
        import enum34 as enum
    except ImportError:
        enum = None
