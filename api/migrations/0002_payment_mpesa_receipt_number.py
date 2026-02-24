# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='mpesa_receipt_number',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
    ]
