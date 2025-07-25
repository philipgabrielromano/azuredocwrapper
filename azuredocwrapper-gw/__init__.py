import logging
import os
import azure.functions as func
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import time

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing document extraction request')
    
    try:
        # Get file from request
        file_data = req.get_body()
        
        # Initialize client
        client = DocumentAnalysisClient(
            endpoint=os.environ["DOCUMENT_INTELLIGENCE_ENDPOINT"],
            credential=AzureKeyCredential(os.environ["DOCUMENT_INTELLIGENCE_KEY"])  # Use Key Vault in production!
        )
        
        # Analyze document - using prebuilt-read for general text
        poller = client.begin_analyze_document(
            "prebuilt-read", 
            file_data
        )
        
        # Wait for completion (with timeout)
        result = poller.result()
        
        # Extract all text
        content = ""
        for page in result.pages:
            for line in page.lines:
                content += line.content + "\n"
        
        # For CSVs/tables, also extract tables
        if result.tables:
            content += "\n\n--- Tables ---\n"
            for table in result.tables:
                for cell in table.cells:
                    content += f"{cell.content}\t"
                    if cell.column_index == table.column_count - 1:
                        content += "\n"
        
        return func.HttpResponse(
            content,
            status_code=200,
            mimetype="text/plain"
        )
        
    except Exception as e:
        logging.error(f"Error processing document: {str(e)}")
        return func.HttpResponse(
            f"Error: {str(e)}",
            status_code=500
        )
