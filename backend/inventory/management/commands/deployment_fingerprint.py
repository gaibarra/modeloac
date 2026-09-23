import hashlib
import json
from django.apps import apps
from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder

class Command(BaseCommand):
    help = 'Resumen de integridad de todas las tablas Django, sin exponer sus datos.'
    def handle(self, *args, **options):
        result = {}
        for model in sorted(apps.get_models(include_auto_created=True), key=lambda m: m._meta.label_lower):
            digest = hashlib.sha256()
            count = 0
            fields = [f.attname for f in model._meta.concrete_fields]
            for row in model.objects.order_by(model._meta.pk.name).values(*fields).iterator():
                digest.update(json.dumps(row, cls=DjangoJSONEncoder, sort_keys=True, ensure_ascii=False).encode())
                digest.update(b'\n')
                count += 1
            result[model._meta.label_lower] = {'count': count, 'sha256': digest.hexdigest()}
        self.stdout.write(json.dumps(result, sort_keys=True, indent=2))
