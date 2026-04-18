from dataclasses import dataclass
from datetime import datetime


@dataclass
class Note:
    id: str
    user_id: str
    title: str
    content: str
    storage_key: str
    source: str
    created_at: datetime
