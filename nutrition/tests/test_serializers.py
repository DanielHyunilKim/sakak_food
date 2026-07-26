from decimal import Decimal

import pytest

from nutrition.models import Food
from nutrition.serializers import FoodSerializer


pytestmark = pytest.mark.django_db


def test_valid_food_is_saved_and_text_is_trimmed(food_payload):
    food_payload["food_name"] = "  꿩불고기  "
    food_payload["maker_name"] = "  충주  "

    serializer = FoodSerializer(data=food_payload)

    assert serializer.is_valid(), serializer.errors
    food = serializer.save()
    assert food.food_name == "꿩불고기"
    assert food.maker_name == "충주"
    assert food.calorie == Decimal("368.80")
    assert Food.objects.filter(pk=food.pk).exists()
    assert serializer.data["group_name"] == "구이류 - 육류구이"


@pytest.mark.parametrize(
    "field",
    [
        "calorie",
        "carbohydrate",
        "protein",
        "fat",
        "sugars",
        "sodium",
        "cholesterol",
        "saturated_fatty_acids",
        "trans_fat",
    ],
)
def test_negative_nutrients_are_rejected(food_payload, field):
    food_payload[field] = "-0.01"

    serializer = FoodSerializer(data=food_payload)

    assert not serializer.is_valid()
    assert field in serializer.errors


def test_required_fields_cannot_be_blank(food_payload):
    food_payload["food_name"] = "   "

    serializer = FoodSerializer(data=food_payload)

    assert not serializer.is_valid()
    assert "food_name" in serializer.errors


def test_food_id_cannot_be_changed(food_payload):
    food = Food.objects.create(**food_payload)
    serializer = FoodSerializer(
        food,
        data={"id": "different-id"},
        partial=True,
    )

    assert not serializer.is_valid()
    assert "id" in serializer.errors
