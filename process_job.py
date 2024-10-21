import asyncio
from database_service import DatabaseService
from index import process_proposition

async def main():
  try: 	
    database_service = DatabaseService()
    propositions = await database_service.get_all_propositions_from_queue()
    print(f"Found {len(propositions)} propositions in queue")
    
    for proposition in propositions:
      try:
        print(f"Processing proposition {proposition['proposition_number']}")
        await database_service.update_proposition_status(proposition['proposition_number'], 'processing')
        await process_proposition(proposition['proposition_number'])
        await database_service.delete_proposition_from_queue(proposition['proposition_number'])
        print(f"Proposition {proposition['proposition_number']} processed")
      except Exception as e:
        await database_service.update_proposition_status(proposition['proposition_number'], 'failed')
        print(f"Error processing proposition {proposition['proposition_number']}: {e}")
  except Exception as e:
    print(f"Error processing propositions: {e}")
    
if __name__ == "__main__":
  asyncio.run(main())

