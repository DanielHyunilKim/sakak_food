import logging
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from nutrition.data_loader import (
    MAX_BULK_CREATE_BATCH_SIZE,
    bulk_create_food_objs,
    load_food_excel,
)
from nutrition.data_normalizer import normalize_food_df
from nutrition.models import Food


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Load, normalize, and upsert food data from an Excel workbook."

    def add_arguments(self, parser):
        parser.add_argument("excel_file", type=Path)
        parser.add_argument(
            "--batch-size",
            type=int,
            default=MAX_BULK_CREATE_BATCH_SIZE,
            help=f"Rows per database batch (default: {MAX_BULK_CREATE_BATCH_SIZE}).",
        )
    def handle(self, *args, **options):
        excel_file = options["excel_file"]
        batch_size = options["batch_size"]

        if not excel_file.is_file():
            raise CommandError(f"Excel file does not exist: {excel_file}")
        if batch_size <= 0:
            raise CommandError("Batch size must be greater than zero.")

        raw_df = load_food_excel(excel_file)
        normalized_df = normalize_food_df(raw_df)
        valid_df = (
            normalized_df.drop_duplicates(subset=["id"], keep="last")
            .drop_duplicates(subset=["food_cd"], keep="last")
        )

        read_count = len(raw_df)
        rejected_count = read_count - len(normalized_df)
        duplicate_count = len(normalized_df) - len(valid_df)
        food_codes = valid_df["food_cd"].tolist()
        existing_codes = set(
            Food.objects.filter(food_cd__in=food_codes).values_list(
                "food_cd",
                flat=True,
            )
        )

        with transaction.atomic():
            processed_count = bulk_create_food_objs(valid_df, batch_size)

        updated_count = len(existing_codes)
        created_count = processed_count - updated_count

        logger.info(
            "Food import complete: read=%d, created=%d, updated=%d, "
            "rejected=%d, duplicates_removed=%d.",
            read_count,
            created_count,
            updated_count,
            rejected_count,
            duplicate_count,
        )
