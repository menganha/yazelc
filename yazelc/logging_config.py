""" Various reusable log configurations """

_BASE_CONFIG = {
    "version":                  1,
    "disable_existing_loggers": False,
    "handlers":   {
        "console": {
            "class":     "logging.StreamHandler",
            "formatter": "default",
            "stream":    "ext://sys.stderr"
        },
        "file":    {
            "class":     "logging.FileHandler",
            "formatter": "default",
            "filename":  "game.log",
            "mode":      "w"
        }
    },
    "formatters": {
        "default": {
            "format":  "%(asctime)s.%(msecs)03d [%(levelname)s] @%(name)s: %(message)s",
            "datefmt": "%I:%M:%S"
        }
    }
}

DEBUG_CONFIG = {
    "root": {
        "handlers": ["console"],
        "level":    "DEBUG"
    },
    **_BASE_CONFIG
}

INFO_CONFIG = {
    "root": {
        "handlers": ["console"],
        "level":    "INFO"
    },
    **_BASE_CONFIG
}

ERROR_CONFIG = {
    "root": {
        "handlers": ["console"],
        "level":    "ERROR"
    },
    **_BASE_CONFIG
}
