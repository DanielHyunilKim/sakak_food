from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, extend_schema_view

from nutrition.models import Food
from nutrition.openapi import (
    INTERNAL_ERROR_RESPONSE,
    NOT_FOUND_RESPONSE,
    SEARCH_PARAMETERS,
    VALIDATION_ERROR_RESPONSE,
)
from nutrition.serializers import FoodSerializer


class FoodPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


@extend_schema_view(
    list=extend_schema(
        summary="식품 목록 검색",
        description=(
            "식품명, 조사년도, 지역/제조사, 식품코드로 검색합니다. "
            "여러 조건은 AND로 결합되며 결과는 페이지네이션됩니다."
        ),
        parameters=SEARCH_PARAMETERS,
        responses={
            200: FoodSerializer(many=True),
            400: VALIDATION_ERROR_RESPONSE,
            500: INTERNAL_ERROR_RESPONSE,
        },
    ),
    create=extend_schema(
        summary="식품 생성",
        responses={
            201: FoodSerializer,
            400: VALIDATION_ERROR_RESPONSE,
            500: INTERNAL_ERROR_RESPONSE,
        },
    ),
    retrieve=extend_schema(
        summary="식품 상세 조회",
        responses={
            200: FoodSerializer,
            404: NOT_FOUND_RESPONSE,
            500: INTERNAL_ERROR_RESPONSE,
        },
    ),
    update=extend_schema(
        summary="식품 전체 수정",
        responses={
            200: FoodSerializer,
            400: VALIDATION_ERROR_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            500: INTERNAL_ERROR_RESPONSE,
        },
    ),
    partial_update=extend_schema(
        summary="식품 일부 수정",
        responses={
            200: FoodSerializer,
            400: VALIDATION_ERROR_RESPONSE,
            404: NOT_FOUND_RESPONSE,
            500: INTERNAL_ERROR_RESPONSE,
        },
    ),
    destroy=extend_schema(
        summary="식품 삭제",
        responses={
            204: None,
            404: NOT_FOUND_RESPONSE,
            500: INTERNAL_ERROR_RESPONSE,
        },
    ),
)
class FoodViewSet(viewsets.ModelViewSet):
    """CRUD API for food items with case-insensitive filtering."""

    queryset = Food.objects.all().order_by("food_name", "id")
    serializer_class = FoodSerializer
    pagination_class = FoodPagination

    text_filters = {
        "food_name": "food_name",
        "maker_name": "maker_name",
        "food_code": "food_cd",
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        match_type = self._normalized_query_value("match") or "partial"

        if match_type not in {"partial", "exact"}:
            raise ValidationError(
                {"match": "Must be either 'partial' or 'exact'."}
            )

        lookup = "icontains" if match_type == "partial" else "iexact"
        for query_parameter, model_field in self.text_filters.items():
            value = self._normalized_query_value(query_parameter)
            if value:
                queryset = queryset.filter(
                    **{f"{model_field}__{lookup}": value}
                )

        research_year = self._normalized_query_value("research_year")
        if research_year:
            try:
                parsed_year = int(research_year)
            except ValueError as error:
                raise ValidationError(
                    {"research_year": "Must be a whole number."}
                ) from error

            if parsed_year < 0:
                raise ValidationError(
                    {"research_year": "Must be zero or greater."}
                )
            queryset = queryset.filter(research_year=parsed_year)

        return queryset

    def _normalized_query_value(self, parameter):
        value = self.request.query_params.get(parameter, "")
        return " ".join(value.split())
