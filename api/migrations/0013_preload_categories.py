from django.db import migrations


def create_default_categories(apps, schema_editor):
    Category = apps.get_model('api', 'Category')
    default_categories = [
        'Tinting',
        'PPF',
        'Wrapping',
        'Detailing',
        'Auto Spares',
    ]
    for name in default_categories:
        Category.objects.get_or_create(name=name)


def reverse_default_categories(apps, schema_editor):
    Category = apps.get_model('api', 'Category')
    Category.objects.filter(name__in=[
        'Tinting', 'PPF', 'Wrapping', 'Detailing', 'Auto Spares',
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_remove_slug_sku_fields'),
    ]

    operations = [
        migrations.RunPython(create_default_categories, reverse_default_categories),
    ]
