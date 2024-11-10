from datetime import timedelta
from restack_ai.workflow import workflow, import_functions, log


with import_functions():
    from src.functions.llm.parse_municode_entry import parse_municode_entry, ParseMunicodeEntryInputParams



@workflow.defn(name="municode_parser")
class municode_parser:
    @workflow.run
    async def run(self, input: dict):
        path = "../data/CaliforniaCityCACodeofOrdinancesEXPORT20220511.xlsx"
        returned_doc = await workflow.step(parse_municode_entry, ParseMunicodeEntryInputParams(path=path), start_to_close_timeout=timedelta(seconds=30))
        return returned_doc