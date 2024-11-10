from restack_ai.function import function, log, FunctionFailure
import os
from pydantic import BaseModel
from dotenv import load_dotenv

from src.ordinance_db import OrdinanceDBWithTogether

load_dotenv()


class ParseMunicodeEntryInputParams(BaseModel):
    path: str

@function.defn(name="parse_municode_entry")
async def parse_municode_entry(input: ParseMunicodeEntryInputParams):
    try:
        db = OrdinanceDBWithTogether.from_excel(
            excel_path=input.get('path', None),
            api_key=os.getenv('TOGETHER_API_KEY'),
            collection_name="california_city_ordinances"
        )
        return True
    except Exception as e:
        log.error(f"Error interacting with llm: {e}")
        raise FunctionFailure(f"Error interacting with llm: {e}", non_retryable=True)
