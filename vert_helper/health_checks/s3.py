from __future__ import annotations

from .types import HealthCheckResult


def check_s3(context: dict) -> HealthCheckResult:
    bucket_name = context.get("bucket_name")
    if not bucket_name:
        return HealthCheckResult(
            status="UNKNOWN",
            message="bucket_name nao informado",
        )

    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError:
        return HealthCheckResult(
            status="FAILED",
            message="Dependencia boto3 nao instalada",
        )

    try:
        client = boto3.client(
            "s3",
            aws_access_key_id=context.get("aws_access_key_id"),
            aws_secret_access_key=context.get("aws_secret_access_key"),
            region_name=context.get("region_name"),
        )
        client.head_bucket(Bucket=bucket_name)
        return HealthCheckResult(status="OK")
    except (BotoCoreError, ClientError) as exc:
        return HealthCheckResult(status="FAILED", message=str(exc))
