"""
Master Agent - Orchestrates the entire DLD to Cursor AI Prompt generation pipeline
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

from .context_validation_agent import ContextValidationAgent
from .prompt_generator_agent import PromptGeneratorAgent
from .code_quality_agent import CodeQualityAgent
from .llm_integration import LLMIntegration
from .prompt_output_agent import PromptOutputAgent
from .feedback_loop import FeedbackLoop
from knowledge_base.knowledge_manager import KnowledgeManager
from utils.config import Config
from utils.logger import AgentLogger, PerformanceLogger, setup_logger

class MasterAgent:
    """
    Master Agent that orchestrates the entire multi-agent pipeline
    for converting DLD to optimized Cursor AI prompts
    """
    
    def __init__(self, config: Config, knowledge_manager: KnowledgeManager):
        self.config = config
        self.knowledge_manager = knowledge_manager
        self.logger = AgentLogger("MasterAgent")
        self.perf_logger = PerformanceLogger(setup_logger("performance"))
        
        # Initialize all sub-agents
        self.context_validation_agent: Optional[ContextValidationAgent] = None
        self.prompt_generator_agent: Optional[PromptGeneratorAgent] = None
        self.code_quality_agent: Optional[CodeQualityAgent] = None
        self.llm_integration: Optional[LLMIntegration] = None
        self.prompt_output_agent: Optional[PromptOutputAgent] = None
        self.feedback_loop: Optional[FeedbackLoop] = None
        
        # Pipeline state
        self.pipeline_state: Dict[str, Any] = {}
        self.execution_metrics: Dict[str, Any] = {}
    
    async def initialize(self) -> None:
        """Initialize all sub-agents and prepare the system"""
        self.logger.info("Initializing Master Agent and sub-agents")
        
        try:
            # Initialize agents in dependency order
            self.context_validation_agent = ContextValidationAgent(
                self.config, self.knowledge_manager
            )
            await self.context_validation_agent.initialize()
            
            self.prompt_generator_agent = PromptGeneratorAgent(
                self.config, self.knowledge_manager
            )
            await self.prompt_generator_agent.initialize()
            
            self.code_quality_agent = CodeQualityAgent(
                self.config, self.knowledge_manager
            )
            await self.code_quality_agent.initialize()
            
            self.llm_integration = LLMIntegration(
                self.config, self.knowledge_manager
            )
            await self.llm_integration.initialize()
            
            self.prompt_output_agent = PromptOutputAgent(
                self.config, self.knowledge_manager
            )
            await self.prompt_output_agent.initialize()
            
            self.feedback_loop = FeedbackLoop(
                self.config, self.knowledge_manager
            )
            await self.feedback_loop.initialize()
            
            self.logger.info("All agents initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {str(e)}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown all agents gracefully"""
        self.logger.info("Shutting down Master Agent and sub-agents")
        
        agents = [
            self.feedback_loop,
            self.prompt_output_agent,
            self.llm_integration,
            self.code_quality_agent,
            self.prompt_generator_agent,
            self.context_validation_agent
        ]
        
        for agent in agents:
            if agent:
                try:
                    await agent.shutdown()
                except Exception as e:
                    self.logger.error(f"Error shutting down agent {type(agent).__name__}: {str(e)}")
    
    async def process_dld(
        self,
        dld_content: str,
        project_path: Optional[str] = None,
        output_format: str = "cursor_ai",
        quality_threshold: float = 0.8,
        include_feedback: bool = True
    ) -> Dict[str, Any]:
        """
        Main pipeline method to process DLD and generate Cursor AI prompts
        
        Args:
            dld_content: The DLD document content
            project_path: Optional path to existing project code
            output_format: Output format (cursor_ai, generic, etc.)
            quality_threshold: Minimum quality threshold
            include_feedback: Whether to include feedback loop
        
        Returns:
            Dictionary containing the result and metrics
        """
        start_time = time.time()
        self.logger.info("Starting DLD processing pipeline")
        
        # Initialize pipeline state
        self.pipeline_state = {
            "dld_content": dld_content,
            "project_path": project_path,
            "output_format": output_format,
            "quality_threshold": quality_threshold,
            "include_feedback": include_feedback,
            "start_time": start_time
        }
        
        try:
            # Stage 1: Context Validation
            self.logger.push_context("Context Validation")
            validation_result = await self._execute_context_validation()
            self.pipeline_state["validation_result"] = validation_result
            self.logger.pop_context()
            
            if not validation_result["success"]:
                return self._create_error_response(
                    "Context validation failed",
                    validation_result
                )
            
            # Stage 2: Prompt Generation (6-step pipeline)
            self.logger.push_context("Prompt Generation")
            generation_result = await self._execute_prompt_generation()
            self.pipeline_state["generation_result"] = generation_result
            self.logger.pop_context()
            
            if not generation_result["success"]:
                return self._create_error_response(
                    "Prompt generation failed",
                    generation_result
                )
            
            # Stage 3: Code Quality Assurance
            self.logger.push_context("Quality Assurance")
            quality_result = await self._execute_quality_assurance()
            self.pipeline_state["quality_result"] = quality_result
            self.logger.pop_context()
            
            if quality_result["quality_score"] < quality_threshold:
                return self._create_error_response(
                    f"Quality threshold not met: {quality_result['quality_score']} < {quality_threshold}",
                    quality_result
                )
            
            # Stage 4: LLM Integration
            self.logger.push_context("LLM Integration")
            llm_result = await self._execute_llm_integration()
            self.pipeline_state["llm_result"] = llm_result
            self.logger.pop_context()
            
            # Stage 5: Prompt Output Processing
            self.logger.push_context("Output Processing")
            output_result = await self._execute_output_processing()
            self.pipeline_state["output_result"] = output_result
            self.logger.pop_context()
            
            # Stage 6: Feedback Loop (if enabled)
            feedback_result = None
            if include_feedback:
                self.logger.push_context("Feedback Loop")
                feedback_result = await self._execute_feedback_loop()
                self.pipeline_state["feedback_result"] = feedback_result
                self.logger.pop_context()
            
            # Compile final result
            total_time = time.time() - start_time
            self.execution_metrics["total_time"] = total_time
            
            result = {
                "success": True,
                "prompt": output_result["final_prompt"],
                "quality_score": quality_result["quality_score"],
                "validation_results": validation_result,
                "generation_metrics": generation_result["metrics"],
                "execution_time": total_time,
                "pipeline_state": self.pipeline_state
            }
            
            if feedback_result:
                result["feedback_metrics"] = feedback_result
            
            self.perf_logger.log_agent_performance(
                "MasterAgent",
                "process_dld",
                total_time,
                True,
                self.execution_metrics
            )
            
            self.logger.info(f"Pipeline completed successfully in {total_time:.2f}s")
            return result
            
        except Exception as e:
            total_time = time.time() - start_time
            self.logger.error(f"Pipeline failed after {total_time:.2f}s: {str(e)}")
            
            self.perf_logger.log_agent_performance(
                "MasterAgent",
                "process_dld",
                total_time,
                False,
                {"error": str(e)}
            )
            
            return self._create_error_response(str(e), {})
    
    async def _execute_context_validation(self) -> Dict[str, Any]:
        """Execute context validation stage"""
        self.logger.info("Executing context validation")
        
        return await self.context_validation_agent.validate_dld(
            dld_content=self.pipeline_state["dld_content"],
            project_path=self.pipeline_state["project_path"]
        )
    
    async def _execute_prompt_generation(self) -> Dict[str, Any]:
        """Execute the 6-step prompt generation pipeline"""
        self.logger.info("Executing prompt generation pipeline")
        
        return await self.prompt_generator_agent.generate_prompt(
            validated_dld=self.pipeline_state["validation_result"]["validated_dld"],
            project_path=self.pipeline_state["project_path"],
            output_format=self.pipeline_state["output_format"]
        )
    
    async def _execute_quality_assurance(self) -> Dict[str, Any]:
        """Execute quality assurance validation"""
        self.logger.info("Executing quality assurance")
        
        return await self.code_quality_agent.validate_prompt(
            generated_prompt=self.pipeline_state["generation_result"]["generated_prompt"],
            dld_context=self.pipeline_state["validation_result"]["validated_dld"],
            quality_threshold=self.pipeline_state["quality_threshold"]
        )
    
    async def _execute_llm_integration(self) -> Dict[str, Any]:
        """Execute LLM integration for final prompt optimization"""
        self.logger.info("Executing LLM integration")
        
        return await self.llm_integration.optimize_prompt(
            base_prompt=self.pipeline_state["generation_result"]["generated_prompt"],
            quality_feedback=self.pipeline_state["quality_result"],
            target_model="gpt-5"
        )
    
    async def _execute_output_processing(self) -> Dict[str, Any]:
        """Execute output processing and formatting"""
        self.logger.info("Executing output processing")
        
        return await self.prompt_output_agent.process_output(
            optimized_prompt=self.pipeline_state["llm_result"]["optimized_prompt"],
            output_format=self.pipeline_state["output_format"],
            validation_results=self.pipeline_state["quality_result"]
        )
    
    async def _execute_feedback_loop(self) -> Dict[str, Any]:
        """Execute feedback loop for performance monitoring"""
        self.logger.info("Executing feedback loop")
        
        return await self.feedback_loop.analyze_performance(
            pipeline_state=self.pipeline_state,
            execution_metrics=self.execution_metrics
        )
    
    def _create_error_response(self, error_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "success": False,
            "error_message": error_message,
            "quality_score": 0.0,
            "validation_results": context,
            "execution_time": time.time() - self.pipeline_state.get("start_time", time.time())
        }
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        return {
            "pipeline_state": self.pipeline_state,
            "execution_metrics": self.execution_metrics,
            "agents_status": {
                "context_validation": self.context_validation_agent is not None,
                "prompt_generator": self.prompt_generator_agent is not None,
                "code_quality": self.code_quality_agent is not None,
                "llm_integration": self.llm_integration is not None,
                "prompt_output": self.prompt_output_agent is not None,
                "feedback_loop": self.feedback_loop is not None
            }
        }
