from decimal import Decimal

from rest_framework import serializers

from nutrition.models import Food


class FoodSerializer(serializers.ModelSerializer):
    group_name = serializers.SerializerMethodField()

    class Meta:
        model = Food
        fields = [
            "id",
            "food_cd",
            "group_name",
            "group_name_major",
            "group_name_minor",
            "food_name",
            "research_year",
            "maker_name",
            "ref_name",
            "serving_size",
            "serving_size_unit",
            "calorie",
            "carbohydrate",
            "protein",
            "fat",
            "sugars",
            "sodium",
            "cholesterol",
            "saturated_fatty_acids",
            "trans_fat",
        ]
        extra_kwargs = {
            "id": {"trim_whitespace": True},
            "food_cd": {"trim_whitespace": True},
            "group_name_major": {"trim_whitespace": True},
            "group_name_minor": {"trim_whitespace": True},
            "food_name": {"trim_whitespace": True},
            "maker_name": {"trim_whitespace": True},
            "ref_name": {"trim_whitespace": True},
            "serving_size": {"trim_whitespace": True},
            "serving_size_unit": {"trim_whitespace": True},
            "calorie": {"min_value": Decimal("0")},
            "carbohydrate": {"min_value": Decimal("0")},
            "protein": {"min_value": Decimal("0")},
            "fat": {"min_value": Decimal("0")},
            "sugars": {"min_value": Decimal("0")},
            "sodium": {"min_value": Decimal("0")},
            "cholesterol": {"min_value": Decimal("0")},
            "saturated_fatty_acids": {"min_value": Decimal("0")},
            "trans_fat": {"min_value": Decimal("0")},
        }

    def get_group_name(self, obj) -> str:
        return f"{obj.group_name_major} - {obj.group_name_minor}"

    def validate_id(self, value):
        if self.instance is not None and value != self.instance.pk:
            raise serializers.ValidationError("The food ID cannot be changed.")
        return value
