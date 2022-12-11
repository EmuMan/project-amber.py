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
            number_start = number_end = format_specifier.index('F') + 1
            while format_specifier[number_end] in '0123456789': number_end += 1
            final_format += format_specifier[number_start:number_end]
        if 'P' in format_specifier:
            final_format += '%'
        
        string = string.replace('{' + substr + '}', f'{{{final_format}}}'.format(value))
        
        end_of_last = next_closed + 1
        