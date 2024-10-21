from proposition_agent import PropositionAgent
from image_extractor import ImageExtractor
from pdf_converter import PDFConverter
from database_service import DatabaseService
from datetime import datetime, timezone
import asyncio

async def process_proposition(proposition_id):	
	database_service = DatabaseService()
	proposition_resume = await database_service.get_resume_by_proposition_number(proposition_id)

	if proposition_resume: 
		print("Proposition resume already exists")
		return
	
	proposition_agent = PropositionAgent()
	print('Getting proposition details')
	proposition_details = await proposition_agent.get_proposition_details(proposition_id)	
	print('Downloading proposition')
	proposition_pdf = await proposition_agent.download_proposition(proposition_details['urlInteiroTeor'])

	pdf_converter = PDFConverter()
	print('Converting PDF to images')
	images = pdf_converter.pdf_to_images(proposition_pdf)

	full_text = ""
	for index, image in enumerate(images):
		image_extractor = ImageExtractor()
		print(f'Extracting text from image {index}')
		text = image_extractor.extract_text_from_image(image)
		full_text += text

	print(f'Full text: {full_text}')

	print('Generating resume')
	resume = await proposition_agent.resume_proposition(proposition_id, full_text)
	print(f'Resume: {resume}')
 
	if resume and isinstance(resume, list):
		print(f'Parsing resume for proposition {proposition_id}')
            
		cleaned_resume = []
		for item in resume:
			if isinstance(item, dict) and 'title' in item and 'description' in item:
				cleaned_resume.append({
					'title': item['title'].strip(),
					'description': item['description'].strip()
				})
			else:
				print(f"Skipping invalid item in resume: {item}")
            
		db_service = DatabaseService()
            
		print(f'Storing resume for proposition {proposition_id}')

		resume_id = await db_service.store_resume({
			"resume": cleaned_resume,
			"url": proposition_details['uri'],
			"proposition_number": proposition_id,
			"created_at": datetime.now(timezone.utc)
		})
		if resume_id:
			print(f"Resume stored successfully with ID: {resume_id}")
		else:
			print("Failed to store resume")
            
		db_service.close_connection()
	else:
		print(f"Invalid resume format for proposition {proposition_id}")
		print(f"Resume content: {resume}")
	

if __name__ == "__main__":
	asyncio.run(main())
 


