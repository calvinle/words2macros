class UserFacingError(Exception):
    """An error whose message is safe to show users (neutral voice, no internals).

    `code` is a stable identifier the API returns, so clients don't match on text.
    """

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message
