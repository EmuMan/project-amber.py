class APIRequestException(Exception):
    
    def __init__(self, error: int, *args: object) -> None:
        self.message = f'error code: {error}'
        super().__init__(*args)
        