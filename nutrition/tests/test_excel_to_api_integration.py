from pathlib import Path

import pytest
from rest_framework import status

from nutrition.data_loader import bulk_create_food_objs, load_food_excel
from nutrition.data_normalizer import normalize_food_df
from nutrition.models import Food


pytestmark = pytest.mark.django_db


def test_excel_row_is_imported_and_searchable_through_api(api_client):
    excel_file = (
        Path(__file__).parent.parent
        / "static"
        / "통합_식품영양성분DB_음식_20230715.xlsx"
    )

    loaded_df = load_food_excel(excel_file)
    source_df = loaded_df.loc[loaded_df["food_cd"] == "D000006"]
    normalized_df = normalize_food_df(source_df)

    processed_count = bulk_create_food_objs(normalized_df)

    assert processed_count == 1
    assert Food.objects.filter(food_cd="D000006").exists()

    response = api_client.get(
        "/api/foods/",
        {
            "food_name": "꿩불고기",
            "research_year": "2019",
            "maker_name": "충주",
            "food_code": "d000006",
            "match": "exact",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0] == {
        "id": "D000006-94-AVG",
        "food_cd": "D000006",
        "group_name": "구이류 - 육류구이",
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
