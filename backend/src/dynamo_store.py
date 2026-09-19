import json
from uuid import uuid4

import config


def new_notice_id():
    return f"NOT-{uuid4().hex[:12].upper()}"


def save_notice(table_client, notice_id, raw_text, simplified, audio_key, language):
    item = {
        "NoticeID": {"S": notice_id},
        "RawText": {"S": raw_text},
        "SimplifiedJSON": {"S": json.dumps(simplified, ensure_ascii=False)},
        "Language": {"S": language},
        "CreatedAt": {"S": _iso_now()},
    }
    if audio_key is not None:
        item["AudioKey"] = {"S": audio_key}
    table_client.put_item(
        TableName=config.notices_table(),
        Item=item,
    )
    return {key: value["S"] for key, value in item.items()}


def get_notice(table_client, notice_id):
    response = table_client.get_item(
        TableName=config.notices_table(),
        Key={"NoticeID": {"S": notice_id}},
    )
    item = response.get("Item")
    if not item:
        return None
    return {
        "NoticeID": item["NoticeID"]["S"],
        "RawText": item["RawText"]["S"],
        "SimplifiedJSON": item["SimplifiedJSON"]["S"],
        "AudioKey": item.get("AudioKey", {}).get("S"),
        "Language": item["Language"]["S"],
        "CreatedAt": item["CreatedAt"]["S"],
    }


def _iso_now():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()