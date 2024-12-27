__all__ = ["TooManyRequestsException", "RejectionURLException"]

class TooManyRequestsException(Exception):
    pass

class RejectionURLException(Exception):
    pass

class FastForwardInaccessibleException(Exception):
    pass