def test_openapi_schema_documents_food_search(api_client):
    response = api_client.get(
        "/api/schema/",
        HTTP_ACCEPT="application/vnd.oai.openapi+json",
    )

    assert response.status_code == 200
    schema = response.data
    assert schema["info"]["title"] == "Food Nutrition API"
    assert schema["info"]["version"] == "1.0.0"

    list_operation = schema["paths"]["/api/foods/"]["get"]
    parameter_names = {
        parameter["name"] for parameter in list_operation["parameters"]
    }
    assert {
        "food_name",
        "research_year",
        "maker_name",
        "food_code",
        "match",
        "page",
        "page_size",
    }.issubset(parameter_names)
    assert {"200", "400", "500"}.issubset(list_operation["responses"])


def test_swagger_and_redoc_pages_are_available(api_client):
    swagger_response = api_client.get("/api/docs/")
    redoc_response = api_client.get("/api/redoc/")

    assert swagger_response.status_code == 200
    assert redoc_response.status_code == 200
