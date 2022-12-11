from typing import Callable, Iterable, Any


def _autogen_repr(obj: object):
    params: str = ', '.join(f'{k}={v}' for k, v in obj.__dict__.items())
    return f'{obj.__class__.__name__}({params})'

def _talent_format(string: str, values: list[float]) -> str:
    end_of_last: int = 0
    
    while(string.count('{', end_of_last) > 0):
        next_open = string.index('{', end_of_last)
        next_closed = string.index('}', next_open + 1)
        
        substr = string[next_open + 1:next_closed]
        param, format_specifier = substr.split(':')
        param_index = int(param[5:]) - 1
        
        value = values[param_index]
        final_format = ':'
        
        if 'F' in format_specifier:
            if type(value) == float:
                number_start = number_end = format_specifier.index('F') + 1
                while number_end < len(format_specifier) and \
                    format_specifier[number_end] in '0123456789':
                        number_end += 1
                final_format += f'.{format_specifier[number_start:number_end]}'
        else:
            final_format += '.0'
        if 'P' in format_specifier:
            final_format += '%'
        
        old_len = len(string)
        string = string.replace('{' + substr + '}', f'{{{final_format}}}'.format(value))
        
        # string length has changed, account for difference
        end_of_last = next_closed - (old_len - len(string)) + 1
    
    return string
        
def find_any(iterable: Iterable, predicate: Callable) -> Any | None:
    for value in iterable:
        if predicate(value):
            return value
    return None
