import logging
import time
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from app.models.schemas import CardGenerationRequest, CardGenerationResponse
from app.agents.github_card_agent import github_card_agent
from app.config import settings
from pathlib import Path
import os

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate", response_model=CardGenerationResponse)
async def generate_card(request: CardGenerationRequest):
    """
    Invoke the GitHub Card Agent to generate a personalized developer card.
    """
    start_time = time.time()
    username = request.username.strip()
    
    logger.info(f"Received generation request for user: {username}")
    
    try:
        # Invoke the autonomous ADK agent
        # The agent follows the strict sequence: scrape -> analyze -> schema -> render -> save
        result = await github_card_agent.generate_for_user(username)
        
        if not result or "error" in result:
            error_detail = result.get("error") if result else "Agent failed to produce a result"
            logger.error(f"Agent error for {username}: {error_detail}")
            raise HTTPException(status_code=500, detail=f"Generation failed: {error_detail}")

        # The agent returns the structured card_data and card_url
        card_url = result.get("card_url")
        card_data = result.get("card_data")

        # Fallback extraction if structure is slightly different
        if not card_url:
            card_url = result.get("url")
        
        duration = time.time() - start_time
        logger.info(f"Successfully generated card for {username} in {duration:.2f}s")

        return CardGenerationResponse(
            success=True,
            image_url=card_url,
            message="Your premium developer card has been synthesized.",
            card_data=card_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating card for {username}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred during synthesis.")

@router.get("/card/{username}", response_class=HTMLResponse)
async def get_card(username: str):
    """
    Retrieve an existing card for a specific user.
    """
    # Define path to the stored card
    current_file = Path(__file__).resolve()
    backend_root = current_file.parent.parent.parent
    file_path = backend_root / "app" / "static" / "cards" / f"{username}.html"
    
    if not file_path.exists():
        logger.warning(f"Card not found for user: {username}")
        raise HTTPException(status_code=404, detail="Card not found. Please generate one first.")
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    return HTMLResponse(content=content)
