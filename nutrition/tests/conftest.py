import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def food_payload():
    return {
        "id": "D000006-94-AVG",
        "food_cd": "D000006",
        "group_name_major": "구이류",
        "group_name_minor": "육류구이",
        "food_name": "꿩불고기",
        "research_year": 2019,
        "maker_name": "충주",
        "ref_name": "외식영양성분자료집 통합본(2012-2017년)",
        "serving_size": "500",
        "serving_size_unit": "g",
        "calorie": "368.80",
        "carbohydrate": "39.70",
        "protein": "33.50",
        "fat": "8.50",
        "sugars": "16.90",
        "sodium": "1264.31",
        "cholesterol": "106.18",
        "saturated_fatty_acids": "1.90",
        "trans_fat": "0.10",
    }
