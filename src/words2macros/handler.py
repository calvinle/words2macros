import json
import logging
import os
from typing import Any

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    logger.info("Received event: %s", json.dumps(event))

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"message": "ok"}),
    }
