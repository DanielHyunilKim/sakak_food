from django.db import models

# Create your models here.
class Food(models.Model):
    id = models.CharField(primary_key=True)
    food_cd = models.CharField()
    group_name_major = models.CharField()
    group_name_minor = models.CharField()
    food_name = models.CharField()
    research_year = models.PositiveIntegerField()
    maker_name = models.CharField()
    ref_name = models.CharField()
    serving_size = models.CharField()
    serving_size_unit = models.CharField()

    calorie = models.DecimalField(max_digits=8, decimal_places=2)
    carbohydrate = models.DecimalField(max_digits=8, decimal_places=2)
    protein = models.DecimalField(max_digits=8, decimal_places=2)
    fat = models.DecimalField(max_digits=8, decimal_places=2)
    sugars = models.DecimalField(max_digits=8, decimal_places=2)
    sodium = models.DecimalField(max_digits=8, decimal_places=2)
    cholesterol = models.DecimalField(max_digits=8, decimal_places=2)
    saturated_fatty_acids = models.DecimalField(max_digits=8, decimal_places=2)
    trans_fat = models.DecimalField(max_digits=8, decimal_places=2)