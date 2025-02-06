""" Various reusable log configurations """

DBG_CONFIG = {
    "version":                  1,
    "disable_existing_loggers": False,
    "root":                     {
        "handlers": ["console"],
        "level":    "DEBUG"
    },
    "handlers":                 {
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
    "formatters":               {
        "default": {
            "format":  "%(asctime)s.%(msecs)03d [%(levelname)s] @%(name)s: %(message)s",
            "datefmt": "%I:%M:%S"
        }
    }
}
