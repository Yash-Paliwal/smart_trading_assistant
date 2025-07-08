raise Exception("TEST: settings.py loaded")
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
print("=== DJANGO SETTINGS LOADED FROM:", __file__)
print("=== CHANNEL_LAYERS CONFIG:", CHANNEL_LAYERS) 