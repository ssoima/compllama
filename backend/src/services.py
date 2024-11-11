import asyncio
from src.client import client
from src.functions.llm.chat import llm_chat
from src.functions.hn.search import hn_search
from src.functions.llm.parse_municode_entry import parse_municode_entry
from src.workflows.campbellca_parser import campbellca_parser
from src.workflows.municode_parser import municode_parser
from src.workflows.workflow import hn_workflow
from src.functions.crawl.crawl_campbellca import crawl_campbellca
from src.functions.crawl.store_campbellca_to_db import store_campbellca_to_db
from restack_ai.restack import ServiceOptions

async def main():
    await asyncio.gather(
        client.start_service(
            workflows=[hn_workflow, municode_parser, campbellca_parser],
            functions=[hn_search, parse_municode_entry, crawl_campbellca, store_campbellca_to_db],
        ),
        client.start_service(
            functions=[llm_chat],
            task_queue="llm_chat",
            options=ServiceOptions(
                rate_limit=1,
                max_concurrent_function_runs=1
            )
        )
    )

def run_services():
    asyncio.run(main())

if __name__ == "__main__":
    run_services()
