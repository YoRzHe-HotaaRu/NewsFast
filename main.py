from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import logging
from scraper import scrape_url
from summarizer import extractive_summarize, extract_keywords
from ai_summarizer import ai_summarize, generate_ai_title

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NewsFast - Article Summarizer", description="AI-powered article summarization tool")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

class URLRequest(BaseModel):
    url: str

class SummarizationResponse(BaseModel):
    article: Dict[str, Any]
    extractive_summary: Dict[str, Any]
    keywords: Dict[str, Any]
    ai_summary: Dict[str, Any]
    success: bool
    error: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/summarize", response_model=SummarizationResponse)
async def summarize_article(request: URLRequest):
    """
    Summarize an article from a given URL
    """
    try:
        logger.info(f"Starting summarization for URL: {request.url}")

        # Step 1: Scrape the article
        article_data = scrape_url(request.url)

        # Step 2: Generate extractive summary
        extractive_result = extractive_summarize(article_data['text'], num_sentences=5)

        # Step 3: Extract keywords
        keywords_result = extract_keywords(article_data['text'], num_keywords=10)

        # Step 4: Generate AI summary (abstractive)
        ai_result = ai_summarize(article_data['text'], max_length=150)

        # Step 5: Generate AI title if original title is not good
        if len(article_data['title'].strip()) < 10:
            article_data['title'] = generate_ai_title(article_data['text'])

        # Prepare response
        response_data = SummarizationResponse(
            article=article_data,
            extractive_summary=extractive_result,
            keywords=keywords_result,
            ai_summary=ai_result,
            success=True
        )

        logger.info("Summarization completed successfully")
        return response_data

    except Exception as e:
        logger.error(f"Error in summarization: {str(e)}")

        # Provide more helpful error messages based on error type
        error_message = str(e)
        if "403" in error_message or "forbidden" in error_message.lower():
            error_message = "This content is behind a paywall or requires authentication. Try a different article or news source."
        elif "404" in error_message:
            error_message = "Article not found. Please check the URL and try again."
        elif "Could not extract valid article content" in error_message:
            error_message = "Unable to extract article content. This site may have anti-scraping protection or an unusual format."
        else:
            error_message = "An error occurred while processing the article. Please try again or use a different URL."

        # Return error response
        return SummarizationResponse(
            article={'title': 'Error', 'text': '', 'url': request.url},
            extractive_summary={'summary': 'Error occurred during processing'},
            keywords={'keywords': []},
            ai_summary={'summary': 'Error occurred during AI summarization'},
            success=False,
            error=error_message
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "NewsFast is running"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="127.0.0.1", port=port)