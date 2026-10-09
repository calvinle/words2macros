from words2macros.killswitch import lambda_handler


class FakeLambda:
    def __init__(self):
        self.calls = []

    def put_function_concurrency(self, **kwargs):
        self.calls.append(kwargs)


def alarm_event(state: str) -> dict:
    return {"alarmData": {"alarmName": "words2macros-cost-spike", "state": {"value": state}}}


def test_alarm_stops_target_function(monkeypatch):
    monkeypatch.setenv("TARGET_FUNCTION", "analyze-fn")
    client = FakeLambda()

    result = lambda_handler(alarm_event("ALARM"), None, client)

    assert result == {"stopped": True}
    assert client.calls == [{"FunctionName": "analyze-fn", "ReservedConcurrentExecutions": 0}]


def test_recovery_does_nothing(monkeypatch):
    monkeypatch.setenv("TARGET_FUNCTION", "analyze-fn")
    client = FakeLambda()

    result = lambda_handler(alarm_event("OK"), None, client)

    assert result == {"stopped": False}
    assert client.calls == []
