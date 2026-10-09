"""Cost kill switch: stops the analyze function when a CloudWatch alarm fires.

Setting a function's reserved concurrency to 0 makes Lambda reject every new
invocation, so no more Bedrock calls are made. Re-enable with:
    aws lambda delete-function-concurrency --function-name <analyze function>
"""

import json
import logging
import os
from typing import Any

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: dict[str, Any], context: Any, client: Any = None) -> dict[str, Any]:
    state = event.get("alarmData", {}).get("state", {}).get("value")
    if state != "ALARM":
        # Alarms can also notify on recovery; only act when entering ALARM.
        logger.info(json.dumps({"action": "none", "alarm_state": state}))
        return {"stopped": False}

    target = os.environ["TARGET_FUNCTION"]
    client = client or boto3.client("lambda")
    client.put_function_concurrency(FunctionName=target, ReservedConcurrentExecutions=0)
    logger.warning(
        json.dumps(
            {
                "action": "stopped",
                "function": target,
                "alarm": event.get("alarmData", {}).get("alarmName"),
            }
        )
    )
    return {"stopped": True}
