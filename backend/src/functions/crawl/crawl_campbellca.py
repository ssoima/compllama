import asyncio

from bs4 import BeautifulSoup
from restack_ai.function import function, log
import requests
import pdfplumber
import json

@function.defn(name="crawl_campbellca")
async def crawl_campbellca():
    try:
        url = 'https://www.campbellca.gov/DocumentCenter/View/6775/Smoke-Alarms-and-Carbon-Monoxide-Alarms--Plan-Submittal'
        # Send a GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses

        # Define metadata
        metadata = {
            "title": "Smoke and Carbon Monoxide Alarms",
            "chapter": "1",
            "section": "1",
            "state": "CA",
            "city": "Campbell",
            "subtitle": "Adoption.",
            "url": url
        }

        # Check if the content is a PDF
        if "application/pdf" in response.headers.get("Content-Type", ""):
            with open("document.pdf", "wb") as f:
                f.write(response.content)
            
            # Use pdfplumber to extract text from the PDF
            content = ""
            with pdfplumber.open("document.pdf") as pdf:
                for page in pdf.pages:
                    content += page.extract_text() + "\n"

            # Structure the output as a JSON object
            output = {
                "metadata": metadata,
                "content": content
            }

            log.info("crawl_campbellca", extra={"output": output})
            return json.dumps(output)  # Convert the dictionary to a JSON string

        else:
            # If it's not a PDF, use BeautifulSoup as a fallback
            soup = BeautifulSoup(response.content, 'html.parser')
            content = soup.get_text()

            # Structure the output as a JSON object
            output = {
                "metadata": metadata,
                "content": content
            }

            log.info("crawl_campbellca", extra={"output": output})
            return output

    except requests.exceptions.RequestException as e:
        log.error("crawl_campbellca function failed", error=e)
        raise e
    except Exception as e:
        log.error("An error occurred while processing the PDF", error=e)
        raise e
