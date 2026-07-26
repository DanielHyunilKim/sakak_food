import logging

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler


logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        logger.error(
            "Unhandled API exception",
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return Response(
            {
                "error": {
                    "status": 500,
                    "code": "internal_server_error",
                    "details": {
                        "detail": ["An unexpected error occurred."],
                    },
                }
            },
            status=500,
        )

    response.data = {
        "error": {
            "status": response.status_code,
            "code": _error_code(exc, response.data),
            "details": _normalize_details(response.data),
        }
    }
    return response


def _error_code(exc, data):
    if isinstance(exc, ValidationError):
        return "validation_error"

    if isinstance(data, dict):
        detail = data.get("detail")
        detail_code = getattr(detail, "code", None)
        if detail_code:
            return detail_code

    return getattr(exc, "default_code", "api_error")


def _normalize_details(data):
    if isinstance(data, dict):
        return {key: _normalize_value(value) for key, value in data.items()}
    return {"non_field_errors": _normalize_value(data)}


def _normalize_value(value):
    if isinstance(value, dict):
        return {
            key: _normalize_value(nested_value)
            for key, nested_value in value.items()
        }
    if isinstance(value, list):
        return value
    return [value]
