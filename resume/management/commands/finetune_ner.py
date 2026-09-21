from django.core.management.base import BaseCommand
from resume.training.finetune import train_spacy

class Command(BaseCommand):
    help = "Melatih (fine-tune) model spaCy NER untuk resume/CV"

    def add_arguments(self, parser):
        parser.add_argument(
            '--iterations',
            type=int,
            default=30,
            help='Jumlah iterasi/epoch (default 30)'
        )

    def handle(self, *args, **options):
        iterations = options['iterations']
        self.stdout.write(self.style.WARNING(f"Memulai fine-tuning NER ({iterations} iterasi)..."))
        
        try:
            train_spacy(iterations=iterations)
            self.stdout.write(self.style.SUCCESS("Berhasil melatih model!"))
            self.stdout.write(self.style.SUCCESS("Model tersimpan di 'resume/models/resume_ner/'"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Terjadi kesalahan: {e}"))
