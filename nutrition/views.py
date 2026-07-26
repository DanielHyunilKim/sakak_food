from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination

from nutrition.models import Food
from nutrition.serializers import FoodSerializer


class FoodPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


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
