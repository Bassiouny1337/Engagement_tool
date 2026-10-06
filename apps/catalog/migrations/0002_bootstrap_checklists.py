"""Bootstrap the checklist catalog from the bundled constants (idempotent)."""
from django.db import migrations


def load_checklists(apps, schema_editor):
    ChecklistItem = apps.get_model("catalog", "ChecklistItem")
    from apps.domains.constants import CHECKLISTS

    to_create = []
    for domain_key, categories in CHECKLISTS.items():
        order = 0
        for category, titles in categories.items():
            for title in titles:
                order += 1
                exists = ChecklistItem.objects.filter(
                    domain_key=domain_key, category=category, title=title
                ).exists()
                if exists:
                    continue
                to_create.append(ChecklistItem(
                    domain_key=domain_key, category=category,
                    title=title, order=order, is_active=True,
                ))
    ChecklistItem.objects.bulk_create(to_create)


def unload(apps, schema_editor):
    # Non-destructive reverse: leave curated data in place.
    pass


class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]
    operations = [migrations.RunPython(load_checklists, unload)]
