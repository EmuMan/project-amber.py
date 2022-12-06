from typing import Any, ClassVar
from urllib import parse
from requests import request
import json

from projectamber.exceptions import APIRequestException


class APIRequest:
    
    BASE: ClassVar[str] = 'https://api.ambr.top/v2'
    
    method: str
    path: str
    language: str
    url :str
    
    def __init__(self, method: str, language: str, path: str):
        self.method = method
        self.path = path
        self.language = language
        self.url = f'{self.BASE}/{language}{path}'
    
    def request(self) -> dict:
        response = request(self.method, self.url)
        
        if not response.ok:
            raise APIRequestException(response.status_code)
        
        return json.loads(response.content)['data']
        