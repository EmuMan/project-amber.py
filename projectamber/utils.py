def _autogen_repr(obj: object):
    params: str = ', '.join(f'{k}={v}' for k, v in obj.__dict__.items())
    return f'{obj.__class__.__name__}({params})'
