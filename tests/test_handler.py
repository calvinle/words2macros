import json

from words2macros.handler import lambda_handler


def test_lambda_handler_returns_ok():
    response = lambda_handler({}, None)

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {"message": "ok"}
