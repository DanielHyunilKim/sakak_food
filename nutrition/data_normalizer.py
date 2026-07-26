from decimal import Decimal

import pandas as pd


NUTRIENT_COLUMNS = [
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

TEXT_COLUMNS = [
    "group_name_major",
    "group_name_minor",
    "food_name",
    "maker_name",
    "ref_name",
    "serving_size",
    "serving_size_unit",
]

REQUIRED_COLUMNS = [
    "id",
    "food_cd",
    "food_name",
    "research_year",
]


def normalize_food_df(food_df: pd.DataFrame) -> pd.DataFrame:
    normalized_df = food_df.copy()

    # Treat whitespace-only strings and "-" as missing.
    normalized_df = normalized_df.replace(
        {
            r"^\s*$": pd.NA,
            r"^\s*-\s*$": pd.NA,
        },
        regex=True,
    )

    # Invalid or missing nutrients become zero.
    for column in NUTRIENT_COLUMNS:
        normalized_df[column] = (
            pd.to_numeric(normalized_df[column], errors="coerce")
            .fillna(0)
            .map(lambda value: Decimal(str(value)))
        )

    # Convert year to a nullable integer before validating it.
    normalized_df["research_year"] = pd.to_numeric(
        normalized_df["research_year"],
        errors="coerce",
    ).astype("Int64")

    # Rows missing required identity or display fields cannot be imported.
    normalized_df = normalized_df.dropna(subset=REQUIRED_COLUMNS)

    # Missing optional text becomes an empty string.
    normalized_df[TEXT_COLUMNS] = normalized_df[TEXT_COLUMNS].fillna("")

    normalized_df["id"] = normalized_df["id"].astype(str).str.strip()
    normalized_df["food_cd"] = normalized_df["food_cd"].astype(str).str.strip()
    normalized_df["research_year"] = normalized_df["research_year"].astype(int)

    return normalized_df
