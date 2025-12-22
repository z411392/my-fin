"""Custom Error Base Class"""


class DomainError(Exception):
    """Domain error base class

    Base class for all business logic errors
    """

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
