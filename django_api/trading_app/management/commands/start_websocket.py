# trading_app/management/commands/start_websocket.py

from django.core.management.base import BaseCommand
import asyncio
import logging
from trading_app.upstox_websocket import start_websocket_client, stop_websocket_client
from trading_app.mock_websocket import start_mock_websocket_client, stop_mock_websocket_client

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Start the WebSocket client for real-time trading'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mock',
            action='store_true',
            help='Use mock data instead of real Upstox WebSocket',
        )

    def handle(self, *args, **options):
        if options['mock']:
            self.stdout.write(
                self.style.SUCCESS('Starting Mock WebSocket client...')
            )
            try:
                # Start the mock WebSocket client
                asyncio.run(start_mock_websocket_client())
                
            except KeyboardInterrupt:
                self.stdout.write(
                    self.style.WARNING('Stopping Mock WebSocket client...')
                )
                stop_mock_websocket_client()
                self.stdout.write(
                    self.style.SUCCESS('Mock WebSocket client stopped.')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error running Mock WebSocket client: {e}')
                )
                logger.error(f'Mock WebSocket client error: {e}')
        else:
            self.stdout.write(
                self.style.SUCCESS('Starting Upstox WebSocket client...')
            )
            try:
                # Start the real WebSocket client
                asyncio.run(start_websocket_client())
                
            except KeyboardInterrupt:
                self.stdout.write(
                    self.style.WARNING('Stopping WebSocket client...')
                )
                stop_websocket_client()
                self.stdout.write(
                    self.style.SUCCESS('WebSocket client stopped.')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error running WebSocket client: {e}')
                )
                logger.error(f'WebSocket client error: {e}') 