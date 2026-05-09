from typing import List, Dict, Any, Optional
import asyncio
import re
import signal
import time
from contextlib import contextmanager
import aiohttp
from fastapi import FastAPI, HTTPException
from app.conf.config import config
from app.utils.log_utils import get_logger
from app.schemas.re_schemas import RegexRequest, RegexResponse
from app.algorithms.regex_agent import RegexAgent
import logging

logger = get_logger(__name__)

# FastAPI application
app = FastAPI(title="LDPAS API", description="Low-Dimensional Philosophical Analysis System")


# Global agent instance
agent_instance = RegexAgent()


@app.post("/generate-regex", response_model=RegexResponse)
async def generate_regex_endpoint(request: RegexRequest):
    """Generate and validate analysis result based on user request."""
    try:
        # Validate input length
        if len(request.sample_input) > config.SAMPLE_INPUT_MAX_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Sample input exceeds maximum length of {config.SAMPLE_INPUT_MAX_LENGTH} characters"
            )
        
        if len(request.user_request) > config.MAX_REGEX_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"User request exceeds maximum length of {config.MAX_REGEX_LENGTH} characters"
            )
        
        # Create agent instance via async context manager
        async with RegexAgent() as local_agent:
            result = await local_agent.generate_regex(
                user_request=request.user_request,
                sample_input=request.sample_input,
                expected_matches=request.expected_matches,
                negative_examples=request.negative_examples,
                additional_examples=request.additional_examples
            )
        
        return RegexResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_regex_endpoint: {e}")
        return RegexResponse(
            success=False,
            attempts=0,
            error=str(e)
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "llm_provider": config.CHAT_MODEL_CONFIG.NAME}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.DEBUG
    )