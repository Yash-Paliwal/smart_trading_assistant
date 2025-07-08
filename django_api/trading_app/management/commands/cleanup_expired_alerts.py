from django.core.management.base import BaseCommand
from django.utils import timezone
from trading_app.models import RadarAlert
from datetime import timedelta

class Command(BaseCommand):
    help = 'Clean up expired alerts and manage alert lifecycle'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )
        parser.add_argument(
            '--expire-old',
            action='store_true',
            help='Mark old alerts as expired',
        )
        parser.add_argument(
            '--delete-expired',
            action='store_true',
            help='Delete expired alerts older than 24 hours',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        
        if options['expire_old']:
            # Mark alerts as expired if they have expired_at time
            expired_alerts = RadarAlert.objects.filter(
                status='ACTIVE',
                expires_at__lt=now
            )
            
            if options['dry_run']:
                self.stdout.write(
                    self.style.WARNING(
                        f'Would mark {expired_alerts.count()} alerts as expired'
                    )
                )
                for alert in expired_alerts[:5]:  # Show first 5
                    self.stdout.write(f'  - {alert.instrument_key} (expired at {alert.expires_at})')
            else:
                count = expired_alerts.update(status='EXPIRED')
                self.stdout.write(
                    self.style.SUCCESS(f'Marked {count} alerts as expired')
                )
        
        if options['delete_expired']:
            # Delete expired alerts older than 24 hours
            cutoff_time = now - timedelta(hours=24)
            old_expired_alerts = RadarAlert.objects.filter(
                status='EXPIRED',
                timestamp__lt=cutoff_time
            )
            
            if options['dry_run']:
                self.stdout.write(
                    self.style.WARNING(
                        f'Would delete {old_expired_alerts.count()} old expired alerts'
                    )
                )
            else:
                count = old_expired_alerts.count()
                old_expired_alerts.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Deleted {count} old expired alerts')
                )
        
        if not any([options['expire_old'], options['delete_expired']]):
            # Default: show current alert status
            active_alerts = RadarAlert.objects.filter(status='ACTIVE').count()
            expired_alerts = RadarAlert.objects.filter(status='EXPIRED').count()
            total_alerts = RadarAlert.objects.count()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Alert Status: {active_alerts} active, {expired_alerts} expired, {total_alerts} total'
                )
            )
            
            # Show alerts expiring soon
            soon_expiring = RadarAlert.objects.filter(
                status='ACTIVE',
                expires_at__gt=now,
                expires_at__lt=now + timedelta(minutes=30)
            )
            
            if soon_expiring.exists():
                self.stdout.write(
                    self.style.WARNING(f'{soon_expiring.count()} alerts expiring in next 30 minutes')
                ) 