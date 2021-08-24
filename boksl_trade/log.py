import logging
from logging import handlers
import config

logger = logging.getLogger(__name__)
logger.setLevel(config.value["logger"]["level"])
formatter = logging.Formatter(config.value["logger"]["format"])

fileLogHandler = handlers.TimedRotatingFileHandler(
    filename=config.value["logger"]["file"],
    when='midnight',
    interval=1,
    backupCount=10,
    encoding='utf-8',
)
fileLogHandler.formatter = formatter
fileLogHandler.level = config.value["logger"]["level"]
fileLogHandler.suffix = "%Y%m%d"
logger.addHandler(fileLogHandler)

streamhandler = logging.StreamHandler()
streamhandler.setFormatter(formatter)
logger.addHandler(streamhandler)
