import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from inventory.models import Location,TechnicalModel,Asset,SourceRecord,AuditEvent,HistoricalService
class Command(BaseCommand):
    help='Importación idempotente por claves originales. Nunca sobrescribe registros operativos existentes.'
    def add_arguments(self,parser):
        parser.add_argument('file')
        parser.add_argument('--dry-run',action='store_true')
    @transaction.atomic
    def handle(self,*args,**options):
        data=json.loads(Path(options['file']).read_text())
        stats={}
        for key,model in [('locations',Location),('models',TechnicalModel)]:
            created=0
            for row in data[key]:
                values={k:v for k,v in row.items() if k!='legacy_id'}
                obj,new=model.objects.get_or_create(code=values.pop('code'),defaults=values);created+=int(new)
                if row.get('needs_review'):
                    SourceRecord.objects.get_or_create(key=f"initial:{key}:{row['code']}",defaults={'category':key,'page':12 if key=='models' else 10 if row['legacy_id']<=50 else 14 if row['legacy_id']<=107 else 11,'legacy_id':str(row.get('legacy_id',row['code'])),'raw_text':json.dumps(row,ensure_ascii=False),'proposed':{'resource':key,'id':obj.pk}})
            stats[key]=created
        created=0
        for row in data['assets']:
            if Asset.objects.filter(legacy_id=row['legacy_id']).exists():continue
            if Asset.objects.filter(code=row['code']).exists():raise CommandError(f"Conflicto de código {row['code']}; transacción cancelada.")
            obj=Asset.objects.create(code=row['code'],legacy_id=row['legacy_id'],model=TechnicalModel.objects.filter(code=row['model_code']).first(),location=Location.objects.filter(code=row['location_code']).first(),acquired_on=row['acquired_on'],notes=row['notes'],source_ref=row['source_ref'],needs_review=row['needs_review'])
            created+=1
            if row['needs_review']:
                SourceRecord.objects.get_or_create(key=f"initial:assets:{row['legacy_id']}",defaults={'category':'assets','page':row['page'],'legacy_id':str(row['legacy_id']),'raw_text':json.dumps(row,ensure_ascii=False),'proposed':{'resource':'assets','id':obj.pk}})
        stats['assets']=created
        created=0
        original_asset_ids={row['code']:row['legacy_id'] for row in data['assets']}
        for row in data.get('historical_services',[]):
            values={k:v for k,v in row.items() if k not in ['legacy_id','asset_code']}
            values['asset']=Asset.objects.get(legacy_id=original_asset_ids[row['asset_code']])
            obj,new=HistoricalService.objects.get_or_create(legacy_id=row['legacy_id'],defaults=values);created+=int(new)
            if row['legacy_id']==26:
                SourceRecord.objects.get_or_create(key='initial:history:26-crossed',defaults={'category':'historical','page':1,'legacy_id':'26','raw_text':json.dumps(row,ensure_ascii=False),'proposed':{'resource':'historical','id':obj.pk},'review_note':'Fila aparentemente tachada en el documento. Confirmar si corresponde a un trabajo anulado.'})
            if row['possible_duplicate_of']:
                SourceRecord.objects.get_or_create(key=f"initial:history:{row['legacy_id']}",defaults={'category':'historical','page':1 if row['legacy_id']<=63 else 2,'legacy_id':str(row['legacy_id']),'raw_text':json.dumps(row,ensure_ascii=False),'proposed':{'resource':'historical','id':obj.pk},'review_note':f"Posible repetición de la fila {row['possible_duplicate_of']}. Conservada, no eliminada automáticamente."})
        stats['historical_services']=created
        for row in data.get('historical_requests',[]):
            SourceRecord.objects.get_or_create(key=f"initial:request:{row['no']}",defaults={'category':'requests','page':3,'legacy_id':str(row['no']),'raw_text':json.dumps(row,ensure_ascii=False),'review_note':'La fuente incluye estatus y fecha de atención; comprobar su coherencia antes de crear una orden.'})
        for row in data.get('source_pages',[]):
            SourceRecord.objects.get_or_create(key=f"initial:page:{row['page']}",defaults=row)
        if options['dry_run']:
            transaction.set_rollback(True)
        else:
            AuditEvent.objects.create(action='import',resource='initial-inventory',object_id='v1',detail={'created':stats,'hashes':data['source_files']})
        self.stdout.write(json.dumps({'dry_run':options['dry_run'],'created':stats},ensure_ascii=False))
