from logging.config import dictConfig
from pathlib import Path

log_file = Path.home() / '.pymoodle.log'

dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'default': {
        'formatter': 'default',
        'level': 'DEBUG',
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': str(log_file),
        'maxBytes': 20000000
    }},
    'loggers': {
        'pymoodle_jku': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False
        },
        '__main__': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False
        },
        '': {
            'handlers': ['default'],
            'level': 'ERROR',
            'propagate': True
        },
    }
})
