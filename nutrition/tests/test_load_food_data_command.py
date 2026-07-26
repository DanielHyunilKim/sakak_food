from unittest.mock import Mock

import pandas as pd
import pytest
from django.core.management import CommandError, call_command

from nutrition.models import Food


pytestmark = pytest.mark.django_db


def test_command_upserts_foods_without_creating_duplicates(
    monkeypatch,
    tmp_path,
    food_payload,
):
    excel_file = tmp_path / "foods.xlsx"
    excel_file.touch()
    loaded_df = pd.DataFrame([food_payload])
    monkeypatch.setattr(
        "nutrition.management.commands.load_food_data.load_food_excel",
        lambda _excel_file: loaded_df,
    )
    logger = Mock()
    monkeypatch.setattr(
        "nutrition.management.commands.load_food_data.logger",
        logger,
    )

    call_command("load_food_data", excel_file)

    assert Food.objects.count() == 1
    logger.info.assert_called_once_with(
        "Food import complete: read=%d, created=%d, updated=%d, "
        "rejected=%d, duplicates_removed=%d.",
        1,
        1,
        0,
        0,
        0,
    )

    loaded_df.loc[0, "food_name"] = "수정된 꿩불고기"
    logger.reset_mock()
    call_command("load_food_data", excel_file)

    assert Food.objects.count() == 1
    assert Food.objects.get(food_cd="D000006").food_name == "수정된 꿩불고기"
    logger.info.assert_called_once_with(
        "Food import complete: read=%d, created=%d, updated=%d, "
        "rejected=%d, duplicates_removed=%d.",
        1,
        0,
        1,
        0,
        0,
    )


def test_command_rejects_a_missing_excel_file(tmp_path):
    with pytest.raises(CommandError, match="Excel file does not exist"):
        call_command("load_food_data", tmp_path / "missing.xlsx")
