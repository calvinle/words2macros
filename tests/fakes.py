class FakeBedrock:
    """Returns canned replies in order and records each request."""

    def __init__(self, *replies: str):
        self.replies = list(replies)
        self.requests = []

    def converse(self, **request):
        self.requests.append(request)
        text = self.replies.pop(0)
        return {"output": {"message": {"content": [{"text": text}]}}}
