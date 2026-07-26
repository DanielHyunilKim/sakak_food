from rest_framework import serializers
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
)


class ApiErrorSerializer(serializers.Serializer):
    status = serializers.IntegerField()
    code = serializers.CharField()
    details = serializers.DictField()


class ApiErrorEnvelopeSerializer(serializers.Serializer):
    error = ApiErrorSerializer()


SEARCH_PARAMETERS = [
    OpenApiParameter(
        name="food_name",
        type=str,
        location=OpenApiParameter.QUERY,
        description="식품명. match 방식에 따라 부분 또는 정확 일치합니다.",
        examples=[OpenApiExample("Food name", value="닭갈비")],
    ),
    OpenApiParameter(
        name="research_year",
        type=int,
        location=OpenApiParameter.QUERY,
        description="조사년도. 항상 정확 일치합니다.",
        examples=[OpenApiExample("Research year", value=2019)],
    ),
    OpenApiParameter(
        name="maker_name",
        type=str,
        location=OpenApiParameter.QUERY,
        description="지역/제조사. match 방식에 따라 부분 또는 정확 일치합니다.",
        examples=[OpenApiExample("Maker or region", value="춘천")],
    ),
    OpenApiParameter(
        name="food_code",
        type=str,
        location=OpenApiParameter.QUERY,
        description="식품코드(food_cd). 대소문자를 구분하지 않습니다.",
        examples=[OpenApiExample("Food code", value="D000008")],
    ),
    OpenApiParameter(
        name="match",
        type=str,
        location=OpenApiParameter.QUERY,
        enum=["partial", "exact"],
        default="partial",
        description="텍스트 검색 방식. 기본값은 partial입니다.",
    ),
]


VALIDATION_ERROR_RESPONSE = OpenApiResponse(
    response=ApiErrorEnvelopeSerializer,
    description="요청값 또는 검색 조건이 올바르지 않습니다.",
    examples=[
        OpenApiExample(
            "Validation error",
            value={
                "error": {
                    "status": 400,
                    "code": "validation_error",
                    "details": {
                        "food_cd": ["food with this food cd already exists."]
                    },
                }
            },
        )
    ],
)

NOT_FOUND_RESPONSE = OpenApiResponse(
    response=ApiErrorEnvelopeSerializer,
    description="요청한 식품이 존재하지 않습니다.",
    examples=[
        OpenApiExample(
            "Food not found",
            value={
                "error": {
                    "status": 404,
                    "code": "not_found",
                    "details": {
                        "detail": ["No Food matches the given query."]
                    },
                }
            },
        )
    ],
)

INTERNAL_ERROR_RESPONSE = OpenApiResponse(
    response=ApiErrorEnvelopeSerializer,
    description="예상하지 못한 서버 오류입니다.",
    examples=[
        OpenApiExample(
            "Internal server error",
            value={
                "error": {
                    "status": 500,
                    "code": "internal_server_error",
                    "details": {
                        "detail": ["An unexpected error occurred."]
                    },
                }
            },
        )
    ],
)
