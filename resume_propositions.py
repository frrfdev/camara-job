from dotenv import load_dotenv

from database_service import DatabaseService
from proposition_agent import PropositionAgent

load_dotenv(override=True)

async def start_resume_process():
	database_service = DatabaseService()
	proposition_agent = PropositionAgent()
  
	propositions = await proposition_agent.get_last_propositions()
	print(f"Found {len(propositions)} propositions")

	for proposition in propositions:
		print(f"Storing proposition {proposition['id']} in queue")
		await database_service.store_proposition_in_queue(proposition['id'])
		print(f"Proposition {proposition['id']} stored in queue")
  
	print("All propositions stored in queue")
