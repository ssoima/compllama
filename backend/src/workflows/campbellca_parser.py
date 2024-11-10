from datetime import timedelta
from restack_ai.workflow import workflow, import_functions


with import_functions():
    from src.functions.crawl.crawl_campbellca import crawl_campbellca
    from src.functions.crawl.store_campbell_to_db import store_campbellca_to_db, StoreCampbellToDbInputParams


@workflow.defn(name="campbellca_parser")
class campbellca_parser:
    @workflow.run
    async def run(self):
        campbell_data = await workflow.step(crawl_campbellca, start_to_close_timeout=timedelta(seconds=30))
        stored_data = await workflow.step(store_campbellca_to_db, start_to_close_timeout=timedelta(seconds=30))
        return campbell_data