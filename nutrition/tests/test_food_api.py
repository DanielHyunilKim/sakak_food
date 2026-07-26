import pytest
from rest_framework import status

from nutrition.models import Food


pytestmark = pytest.mark.django_db


def create_food(food_payload, **overrides):
    payload = food_payload | overrides
    return Food.objects.create(**payload)


def test_food_crud(api_client, food_payload):
    create_response = api_client.post(
        "/api/foods/",
        food_payload,
        format="json",
    )

    assert create_response.status_code == status.HTTP_201_CREATED
    assert Food.objects.filter(pk=food_payload["id"]).exists()

    detail_url = f"/api/foods/{food_payload['id']}/"
    retrieve_response = api_client.get(detail_url)
    assert retrieve_response.status_code == status.HTTP_200_OK
    assert retrieve_response.data["food_name"] == "꿩불고기"
    assert retrieve_response.data["group_name"] == "구이류 - 육류구이"

    update_response = api_client.patch(
        detail_url,
        {"food_name": "  닭갈비  "},
        format="json",
    )
    assert update_response.status_code == status.HTTP_200_OK
    assert update_response.data["food_name"] == "닭갈비"

    delete_response = api_client.delete(detail_url)
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert not Food.objects.filter(pk=food_payload["id"]).exists()


def test_partial_search_trims_spaces(
    api_client,
    food_payload,
):
    create_food(
        food_payload,
        id="D000007-ZZ-AVG",
        food_cd="D000007",
        food_name="닭갈비",
        maker_name="전국(대표)",
    )
    create_food(
        food_payload,
        id="D000008-66-AVG",
        food_cd="D000008",
        food_name="닭갈비",
        maker_name="춘천",
    )
    create_food(
        food_payload,
        id="D000012-95-AVG",
        food_cd="D000012",
        food_name="돼지갈비",
        maker_name="서울특별시 마포구",
    )
    create_food(
        food_payload,
        id="D000009-ZZ-AVG",
        food_cd="D000009",
        food_name="닭꼬치",
        maker_name="전국(대표)",
    )

    response = api_client.get(
        "/api/foods/",
        {"food_name": "  갈비  ", "match": "partial"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 3
    assert {food["id"] for food in response.data["results"]} == {
        "D000007-ZZ-AVG",
        "D000008-66-AVG",
        "D000012-95-AVG",
    }


def test_exact_search_is_case_insensitive(api_client, food_payload):
    create_food(
        food_payload,
        id="D000007-ZZ-AVG",
        food_cd="D000007",
        food_name="닭갈비",
    )
    create_food(
        food_payload,
        id="D000008-66-AVG",
        food_cd="D000008",
        food_name="닭갈비",
    )
    create_food(
        food_payload,
        id="D000009-ZZ-AVG",
        food_cd="D000009",
        food_name="닭꼬치",
    )

    response = api_client.get(
        "/api/foods/",
        {"food_name": "닭갈비", "match": "exact"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert {food["id"] for food in response.data["results"]} == {
        "D000007-ZZ-AVG",
        "D000008-66-AVG",
    }


def test_combines_search_filters(api_client, food_payload):
    create_food(
        food_payload,
        id="D000008-66-AVG",
        food_cd="D000008",
        food_name="닭갈비",
        maker_name="춘천",
        research_year=2019,
    )
    create_food(
        food_payload,
        id="D000007-ZZ-AVG",
        food_cd="D000007",
        food_name="닭갈비",
        maker_name="전국(대표)",
        research_year=2019,
    )
    create_food(
        food_payload,
        id="D000012-95-AVG",
        food_cd="D000012",
        food_name="돼지갈비",
        maker_name="서울특별시 마포구",
        research_year=2019,
    )

    response = api_client.get(
        "/api/foods/",
        {
            "food_code": "d000008",
            "maker_name": "  춘천  ",
            "research_year": "2019",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert [food["id"] for food in response.data["results"]] == [
        "D000008-66-AVG"
    ]


@pytest.mark.parametrize(
    ("query", "error_field"),
    [
        ({"match": "unknown"}, "match"),
        ({"research_year": "twenty"}, "research_year"),
        ({"research_year": "-1"}, "research_year"),
    ],
)
def test_invalid_search_parameters_return_400(
    api_client,
    query,
    error_field,
):
    response = api_client.get("/api/foods/", query)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert error_field in response.data


def test_list_is_paginated(api_client, food_payload):
    foods = [
        Food(
            **(
                food_payload
                | {
                    "id": f"food-{index:02d}",
                    "food_cd": f"TEST{index:03d}",
                }
            )
        )
        for index in range(25)
    ]
    Food.objects.bulk_create(foods)

    response = api_client.get("/api/foods/", {"page": 2, "page_size": 10})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 25
    assert len(response.data["results"]) == 10
    assert response.data["next"] is not None
    assert response.data["previous"] is not None


def test_missing_food_returns_404(api_client):
    response = api_client.get("/api/foods/missing/")

    assert response.status_code == status.HTTP_404_NOT_FOUND
