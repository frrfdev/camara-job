import requests
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get the variables from the environment
OLLAMA_URL = os.getenv('OLLAMA_URL')
TOKEN = os.getenv('TOKEN')

def upload_file(token, file):
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    files = {'file': file}
    try:   	
        response = requests.post(OLLAMA_URL, json={
            "model": "llama3.2:latest",
            "prompt": "Leia o arquivo e retorne um resumo conciso e completo que até uma criança de 10 anos consegue entender."
        }, headers=headers, files=files)

        # Print the status code and response text
        print(f"Response Status Code: {response.status_code}")
        print("Response Text:", response.text)

        # Attempt to return the JSON response
        response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
        return response.json()  # Attempt to decode JSON
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print("Response Text:", response.text)  # Print the response text for debugging
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
    except ValueError as json_err:
        print(f"JSON decode error: {json_err}")
        print("Response Text:", response.text)  # Print the response text for debugging
    return None  # Return None if there was an error

def download_file(url):
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    if response.status_code == 200:
        return response.content
    else:
        print(f"Failed to download file. Status code: {response.status_code}")
        print(response.text)
        return None

# Example usage
url = "https://www.camara.leg.br/proposicoesWeb/prop_mostrarintegra?codteor=365033"
file_content = download_file(url)

if file_content:  # Check if file_content is not None
    response = upload_file(TOKEN, file_content)
    if response:  # Check if response is not None
        print(response)
else:
    print("No file content to upload.")
