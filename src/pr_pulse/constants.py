from enum import Enum


class OutputFormat(str, Enum):
    table = "table"
    json = "json"


MAX_COMMENTS = 5
BATCH_SIZE = 8
