import json

from looniemind.db import Database
from looniemind.models import ForecastService, ModelService
from looniemind.services import FinanceService

if __name__ == "__main__":
    database = Database()
    database.initialize()
    service = FinanceService(database, ModelService(database), ForecastService(database))
    print(json.dumps(service.seed_demo(), ensure_ascii=False, indent=2))
