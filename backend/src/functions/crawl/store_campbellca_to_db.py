from restack_ai.function import function, log
import requests
from pydantic import BaseModel, Field
from typing import Any



class StoreCampbellToDbInputParams(BaseModel):
    metadata: Any = Field(default=None, description="Metadata of the entry")
    content: str = Field(default=None, description="Content of the entry")

@function.defn(name="store_campbellca_to_db")
async def store_campbellca_to_db():
    try:
        return True

    except requests.exceptions.RequestException as e:
        log.error("crawl_campbellca function failed", error=e)
        raise e
    except Exception as e:
        log.error("An error occurred while processing the PDF", error=e)
        raise e
