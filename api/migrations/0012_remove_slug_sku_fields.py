from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_gallery'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='slug',
        ),
        migrations.RemoveField(
            model_name='product',
            name='slug',
        ),
        migrations.RemoveField(
            model_name='product',
            name='sku',
        ),
    ]
