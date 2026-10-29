"""Add model_type field to PredictionRecord.

Distinguishes records produced by the existing HAM10000 dermoscopic
prediction flow (model_type='dermoscopic', the default for legacy rows)
from records produced by the new SkinDisNet phone-image prediction flow
(model_type='phone').

Both flows share the same table; the field lets the result template
decide which class list (7 HAM10000 vs 6 SkinDisNet) to render.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("predictor", "0003_medical_review_and_patient_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="predictionrecord",
            name="model_type",
            field=models.CharField(
                choices=[
                    ("dermoscopic", "Dermoscopic (HAM10000)"),
                    ("phone", "Phone Image (SkinDisNet)"),
                ],
                db_index=True,
                default="dermoscopic",
                max_length=16,
            ),
        ),
    ]
