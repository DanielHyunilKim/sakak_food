from decimal import Decimal

from pathlib import Path

import pandas as pd

from nutrition.models import Food


MAX_BULK_CREATE_BATCH_SIZE = 1000


EXCEL_COLUMN_MAPPING = {
    "SAMPLE_ID": "id",
    "식품코드": "food_cd",
    "식품대분류": "group_name_major",
    "식품상세분류": "group_name_minor",
    "식품명": "food_name",
    "연도": "research_year",
    "지역 / 제조사": "maker_name",
    "성분표출처": "ref_name",
    "1회제공량": "serving_size",
    "내용량_단위": "serving_size_unit",
    "에너지(㎉)": "calorie",
    "탄수화물(g)": "carbohydrate",
    "단백질(g)": "protein",
    "지방(g)": "fat",
    "총당류(g)": "sugars",
    "나트륨(㎎)": "sodium",
    "콜레스테롤(㎎)": "cholesterol",
    "총 포화 지방산(g)": "saturated_fatty_acids",
    "트랜스 지방산(g)": "trans_fat",
}


def load_food_excel(excel_file: Path) -> pd.DataFrame:
    food_df = pd.read_excel(
        excel_file,
        usecols=list(EXCEL_COLUMN_MAPPING),
    )
    return (
        food_df.rename(columns=EXCEL_COLUMN_MAPPING)
        [list(EXCEL_COLUMN_MAPPING.values())]
    )


def bulk_create_food_objs(food_df: pd.DataFrame, batch_size: int = MAX_BULK_CREATE_BATCH_SIZE) -> int:
    food_objs = [
        Food(**food_data)
        for food_data in food_df.to_dict(orient="records")
    ]
    created_food_objs = Food.objects.bulk_create(
        food_objs,
        batch_size=batch_size,
    )
    return len(created_food_objs)
