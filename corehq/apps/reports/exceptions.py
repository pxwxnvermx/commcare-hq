

class BadRequestError(Exception):
    """
    For catching client-side errors.
    Views should catch and return HTTP400 or similar
    """
    pass


class InvalidDaterangeException(Exception):
    pass


class TooMuchDataError(Exception):
    pass
