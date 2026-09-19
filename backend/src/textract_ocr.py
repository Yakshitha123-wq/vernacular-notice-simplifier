import config


def extract_text(client, image_bytes=None, bucket=None, key=None):
    if bucket and key:
        return _extract_from_s3(client, bucket, key)
    return _extract_from_bytes(client, image_bytes)


def _extract_from_bytes(client, image_bytes):
    response = client.detect_document_text(Document={"Bytes": image_bytes})
    return _join_blocks(response)


def _extract_from_s3(client, bucket, key):
    response = client.detect_document_text(
        Document={"S3Object": {"Bucket": bucket, "Name": key}}
    )
    return _join_blocks(response)


def _join_blocks(response):
    blocks = response.get("Blocks", [])
    lines = [
        block["Text"]
        for block in blocks
        if block.get("BlockType") == "LINE"
    ]
    return "\n".join(lines)


def estimates_page_count(text):
    words = len(text.split())
    return max(1, (words + 449) // 450)