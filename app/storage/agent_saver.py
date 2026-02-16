
from typing import Optional
from langchain.checkpointing import BaseCheckpointSaver
from langchain.checkpointing.sqlite import PostgresCheckpointSaver

from app.config import settings


class AgentSaverManager:
    def __init__(self):
        self._saver: Optional[BaseCheckpointSaver] = None

    def get_postgres_saver(self) -&gt; PostgresCheckpointSaver:
        if self._saver is None:
            self._saver = PostgresCheckpointSaver(
                connection_string=settings.database_url
            )
        return self._saver


agent_saver_manager = AgentSaverManager()

