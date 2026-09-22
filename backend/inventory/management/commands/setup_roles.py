from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
class Command(BaseCommand):
    help='Crea roles sin modificar usuarios ni contraseñas.'
    def handle(self,*args,**options):
        for name in ['Administración','Mantenimiento','Consulta']:Group.objects.get_or_create(name=name)
        self.stdout.write('Roles listos.')
