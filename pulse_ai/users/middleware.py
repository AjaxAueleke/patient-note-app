import logging

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print("DEBUG REQUEST LOGGING")
        print("################################################")

        # Print request method and path
        print(f'Request Path: {request.get_full_path()}')
        print(f'Request Method: {request.method}')

        # Print headers
        headers = {k: v for k, v in request.headers.items()}
        print('Headers:')
        for header, value in headers.items():
            print(f'{header}: {value}')

        # Optionally print other parts of the request
        # Be cautious about printing sensitive information like cookies or auth tokens
        if hasattr(request, 'body'):
            try:
                print(f'Body: {request.body.decode("utf-8")}')
            except UnicodeDecodeError:
                print('Body: [Could not decode body, it may be binary data]')

        print("################################################")
        response = self.get_response(request)
        return response
