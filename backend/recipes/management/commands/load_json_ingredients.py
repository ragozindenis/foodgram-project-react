import json
import os

from django.core.management.base import BaseCommand

from recipes.models import Ingredient

path = "data"


class Command(BaseCommand):
    help = "load ingredients to db"

    def handle(self, *args, **options):
        with open(
            os.path.join(path, "ingredients.json"), "r", encoding="utf-8"
        ) as f:
            data = json.load(f)
            for row in data:
                Ingredient.objects.get_or_create(
                    name=row.get("name"),
                    measurement_unit=row.get("measurement_unit"),
                )
