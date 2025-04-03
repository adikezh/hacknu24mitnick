class ImpersonationMiddleware:
    """
    Middleware to add an 'is_impersonating' attribute to the request object.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.is_impersonating = "original_user_id" in request.session
        return self.get_response(request)
