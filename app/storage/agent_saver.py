
from typing import Optional
from langgraph.checkpoint.postgres import PostgresSaver

from app.config import settings


class AgentSaverManager:
    def __init__(self):
        self._saver = None

    def get_postgres_saver(self):
        if self._saver is None:
            self._saver = PostgresSaver.from_conn_string(settings.database_url)
        return self._saver


agent_saver_manager = AgentSaverManager()

