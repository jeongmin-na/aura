"""
DLD to Cursor AI Prompt Generation System
Multi-Agent Architecture for 5G Base Station Design Document Processing
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel

from agents.master_agent import MasterAgent
from agents.context_validation_agent import ContextValidationAgent
from agents.prompt_generator_agent import PromptGeneratorAgent
from agents.code_quality_agent import CodeQualityAgent
from agents.llm_integration import LLMIntegration
from agents.prompt_output_agent import PromptOutputAgent
from agents.feedback_loop import FeedbackLoop
from knowledge_base.knowledge_manager import KnowledgeManager
from utils.config import Config
from utils.logger import setup_logger

# Initialize logging
logger = setup_logger("main")

# FastAPI app
app = FastAPI(
    title="DLD to Cursor AI Prompt Generator",
    description="Multi-Agent System for Converting 5G Design Documents to Optimized Cursor AI Prompts",
    version="1.0.0"
)

class DLDProcessRequest(BaseModel):
    """Request model for DLD processing"""
    dld_content: str
    project_path: Optional[str] = None
    output_format: str = "cursor_ai"
    quality_threshold: float = 0.8
    include_feedback: bool = True

class PromptResponse(BaseModel):
    """Response model for generated prompts"""
    success: bool
    prompt: Optional[str] = None
    quality_score: float
    validation_results: Dict[str, Any]
    feedback_metrics: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

# Global system components
master_agent: Optional[MasterAgent] = None
knowledge_manager: Optional[KnowledgeManager] = None

@app.on_event("startup")
async def startup_event():
    """Initialize system components on startup"""
    global master_agent, knowledge_manager
    
    try:
        # Load configuration
        config = Config()
        
        # Initialize knowledge manager
        knowledge_manager = KnowledgeManager(config)
        await knowledge_manager.initialize()
        
        # Initialize master agent with all sub-agents
        master_agent = MasterAgent(config, knowledge_manager)
        await master_agent.initialize()
        
        logger.info("DLD to Cursor AI Prompt Generation System initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize system: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if master_agent:
        await master_agent.shutdown()
    if knowledge_manager:
        await knowledge_manager.shutdown()
    logger.info("System shutdown completed")

@app.post("/process-dld", response_model=PromptResponse)
async def process_dld(request: DLDProcessRequest):
    """
    Main endpoint for processing DLD and generating Cursor AI prompts
    """
    try:
        if not master_agent:
            raise HTTPException(status_code=500, detail="System not initialized")
        
        # Process DLD through the multi-agent pipeline
        result = await master_agent.process_dld(
            dld_content=request.dld_content,
            project_path=request.project_path,
            output_format=request.output_format,
            quality_threshold=request.quality_threshold,
            include_feedback=request.include_feedback
        )
        
        return PromptResponse(
            success=result["success"],
            prompt=result.get("prompt"),
            quality_score=result["quality_score"],
            validation_results=result["validation_results"],
            feedback_metrics=result.get("feedback_metrics"),
            error_message=result.get("error_message")
        )
        
    except Exception as e:
        logger.error(f"Error processing DLD: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-dld", response_model=PromptResponse)
async def upload_dld(
    file: UploadFile = File(...),
    project_path: Optional[str] = None,
    output_format: str = "cursor_ai",
    quality_threshold: float = 0.8
):
    """
    Upload DLD file and process it
    """
    try:
        # Read file content
        content = await file.read()
        dld_content = content.decode('utf-8')
        
        # Process using the main endpoint logic
        request = DLDProcessRequest(
            dld_content=dld_content,
            project_path=project_path,
            output_format=output_format,
            quality_threshold=quality_threshold
        )
        
        return await process_dld(request)
        
    except Exception as e:
        logger.error(f"Error uploading and processing DLD: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "system_initialized": master_agent is not None,
        "knowledge_base_ready": knowledge_manager is not None and await knowledge_manager.is_ready()
    }

@app.get("/knowledge-stats")
async def get_knowledge_stats():
    """Get knowledge base statistics"""
    if not knowledge_manager:
        raise HTTPException(status_code=500, detail="Knowledge manager not initialized")
    
    return await knowledge_manager.get_statistics()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
