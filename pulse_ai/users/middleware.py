class RequestLoggingMiddleware:
    """No-op pass-through middleware.

    This previously printed every request's full path, method, headers and
    body to stdout, which leaked credentials (Authorization/JWT headers,
    login passwords) and patient/session data into the logs. That behaviour
    has been removed. The class is retained as a safe no-op so that any
    deployment still referencing this path keeps working; it is no longer
    enabled in the default MIDDLEWARE stack.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)
