from decimal import Decimal

import pandas as pd

from nutrition.data_normalizer import (
    NUTRIENT_COLUMNS,
    TEXT_COLUMNS,
    normalize_food_df,
)


def make_food_row(**overrides):
    row = {
        "id": "sample-1",
        "food_cd": "food-1",
        "research_year": "2023",
        **dict.fromkeys(TEXT_COLUMNS, "value"),
        **dict.fromkeys(NUTRIENT_COLUMNS, "1.25"),
    }
    row.update(overrides)
    return row


def test_normalizes_missing_and_invalid_nutrients_to_decimal_zero():
    food_df = pd.DataFrame(
        [
            make_food_row(
                calorie="-",
                carbohydrate="  -  ",
                protein="",
                fat="   ",
                sugars=None,
                sodium=pd.NA,
                cholesterol=float("nan"),
                saturated_fatty_acids="not-a-number",
                trans_fat="2.75",
            )
        ]
    )

    normalized_df = normalize_food_df(food_df)
    normalized_row = normalized_df.iloc[0]

    for column in NUTRIENT_COLUMNS[:-1]:
        assert normalized_row[column] == Decimal("0")
        assert isinstance(normalized_row[column], Decimal)
    assert normalized_row["trans_fat"] == Decimal("2.75")
    assert isinstance(normalized_row["trans_fat"], Decimal)


def test_normalizes_missing_optional_text_and_required_field_types():
    food_df = pd.DataFrame(
        [
            make_food_row(
                id="  sample-1  ",
                food_cd="  food-1  ",
                research_year="2023",
                group_name_major="-",
                group_name_minor="  -  ",
                food_name="",
                maker_name="   ",
                ref_name=None,
                serving_size=pd.NA,
                serving_size_unit=float("nan"),
            )
        ]
    )

    normalized_df = normalize_food_df(food_df)
    normalized_row = normalized_df.iloc[0]

    assert all(normalized_row[column] == "" for column in TEXT_COLUMNS)
    assert normalized_row["id"] == "sample-1"
    assert normalized_row["food_cd"] == "food-1"
    assert normalized_row["research_year"] == 2023


def test_drops_rows_with_missing_or_invalid_required_values():
    food_df = pd.DataFrame(
        [
            make_food_row(id="valid"),
            make_food_row(id="-"),
            make_food_row(food_cd=None),
            make_food_row(research_year="not-a-year"),
        ]
    )

    normalized_df = normalize_food_df(food_df)

    assert normalized_df["id"].tolist() == ["valid"]
