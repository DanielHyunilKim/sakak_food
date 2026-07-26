from pathlib import Path
from unittest.mock import Mock

import pandas as pd

from nutrition.data_loader import (
    EXCEL_COLUMN_MAPPING,
    UPSERT_UPDATE_FIELDS,
    bulk_create_food_objs,
    load_food_excel,
)
from nutrition.models import Food


def test_loads_bundled_excel_with_expected_columns():
    excel_file = (
        Path(__file__).parent.parent
        / "static"
        / "통합_식품영양성분DB_음식_20230715.xlsx"
    )

    food_df = load_food_excel(excel_file)

    assert not food_df.empty
    assert food_df.columns.tolist() == list(EXCEL_COLUMN_MAPPING.values())


def test_bulk_creates_foods_in_batches(monkeypatch):
    food_df = pd.DataFrame(
        {"id": [f"food-{index}" for index in range(15)]}
    )
    bulk_create = Mock(side_effect=lambda food_objs, **kwargs: food_objs)
    monkeypatch.setattr(Food.objects, "bulk_create", bulk_create)

    created_count = bulk_create_food_objs(food_df, batch_size=10)

    food_objs = bulk_create.call_args.args[0]
    assert created_count == 15
    assert bulk_create.call_args.kwargs["batch_size"] == 10
    assert bulk_create.call_args.kwargs["update_conflicts"] is True
    assert bulk_create.call_args.kwargs["update_fields"] == UPSERT_UPDATE_FIELDS
    assert bulk_create.call_args.kwargs["unique_fields"] == ["food_cd"]
    assert all(isinstance(food, Food) for food in food_objs)
