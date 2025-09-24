"""
LLM Integration - Handles communication with language models for prompt optimization
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from openai import AsyncOpenAI

from knowledge_base.knowledge_manager import KnowledgeManager
from utils.config import Config
from utils.logger import AgentLogger

@dataclass
class OptimizationRequest:
    """Request for prompt optimization"""
    base_prompt: str
    target_model: str
    optimization_goals: List[str]
    quality_feedback: Dict[str, Any]
    context: Dict[str, Any]

@dataclass
class OptimizationResult:
    """Result of prompt optimization"""
    optimized_prompt: str
    improvement_score: float
    changes_made: List[str]
    reasoning: str
    metadata: Dict[str, Any]

class LLMIntegration:
    """
    Agent responsible for LLM integration and prompt optimization
    
    Functions:
    - GPT-5 prompt generation and optimization
    - Multi-model compatibility
    - Quality-driven refinement
    """
    
    def __init__(self, config: Config, knowledge_manager: KnowledgeManager):
        self.config = config
        self.knowledge_manager = knowledge_manager
        self.logger = AgentLogger("LLMIntegration")
        
        # Initialize OpenAI client
        self.openai_client = None
        
        # Optimization templates
        self.optimization_templates = {
            "cursor_ai_optimization": """
You are an expert in optimizing prompts for AI code generation tools like Cursor AI.

Analyze the following prompt and optimize it for better code generation results:

{base_prompt}

Quality Feedback:
{quality_feedback}

Optimization Goals:
{optimization_goals}

Please provide:
1. An optimized version of the prompt
2. Explanation of improvements made
3. Expected benefits of the changes

Focus on:
- Clarity and specificity
- Technical accuracy
- Actionable instructions
- Code generation effectiveness
""",
            "5g_domain_enhancement": """
As a 5G wireless communication expert, enhance this prompt with domain-specific knowledge:

{base_prompt}

Ensure the prompt includes:
- Accurate 5G terminology and concepts
- Relevant protocol specifications
- Performance considerations
- Implementation best practices
- Industry standards compliance

Provide an enhanced version that maintains technical accuracy while being practical for code generation.
"""
        }
        
        # Model configurations
        self.model_configs = {
            "gpt-4": {
                "max_tokens": 4000,
                "temperature": 0.7,
                "top_p": 0.9
            },
            "gpt-3.5-turbo": {
                "max_tokens": 3000,
                "temperature": 0.8,
                "top_p": 0.9
            }
        }
    
    async def initialize(self) -> None:
        """Initialize the LLM integration"""
        self.logger.info("Initializing LLM Integration")
        
        # Initialize OpenAI client
        api_key = self.config.llm.api_key
        if api_key:
            self.openai_client = AsyncOpenAI(api_key=api_key)
        else:
            self.logger.warning("No OpenAI API key provided")
        
        self.logger.info("LLM Integration initialized successfully")
    
    async def shutdown(self) -> None:
        """Shutdown the LLM integration"""
        self.logger.info("Shutting down LLM Integration")
        if self.openai_client:
            await self.openai_client.close()
    
    async def optimize_prompt(
        self,
        base_prompt: str,
        quality_feedback: Dict[str, Any],
        target_model: str = "gpt-4",
        optimization_goals: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Main method for optimizing prompts using LLM
        
        Args:
            base_prompt: The prompt to optimize
            quality_feedback: Feedback from quality assessment
            target_model: Target LLM model
            optimization_goals: Specific optimization goals
            
        Returns:
            Optimization results and metadata
        """
        self.logger.info(f"Starting prompt optimization for {target_model}")
        
        if not self.openai_client:
            return {
                "success": False,
                "error": "OpenAI client not initialized",
                "optimized_prompt": base_prompt
            }
        
        try:
            # Prepare optimization request
            optimization_goals = optimization_goals or self._extract_optimization_goals(quality_feedback)
            
            request = OptimizationRequest(
                base_prompt=base_prompt,
                target_model=target_model,
                optimization_goals=optimization_goals,
                quality_feedback=quality_feedback,
                context={}
            )
            
            # Perform optimization
            result = await self._perform_optimization(request)
            
            # Validate optimization result
            validation_result = await self._validate_optimization(base_prompt, result)
            
            self.logger.info(f"Prompt optimization completed with score: {result.improvement_score:.2f}")
            
            return {
                "success": True,
                "optimized_prompt": result.optimized_prompt,
                "improvement_score": result.improvement_score,
                "changes_made": result.changes_made,
                "reasoning": result.reasoning,
                "validation_result": validation_result,
                "metadata": result.metadata
            }
            
        except Exception as e:
            self.logger.error(f"Prompt optimization failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "optimized_prompt": base_prompt
            }
    
    async def _perform_optimization(self, request: OptimizationRequest) -> OptimizationResult:
        """Perform the actual optimization using LLM"""
        self.logger.info("Performing prompt optimization")
        
        # Choose optimization strategy based on quality feedback
        strategy = self._choose_optimization_strategy(request.quality_feedback)
        
        # Generate optimization prompt
        optimization_prompt = self._generate_optimization_prompt(request, strategy)
        
        # Call LLM for optimization
        response = await self._call_llm(optimization_prompt, request.target_model)
        
        # Parse and structure the response
        result = self._parse_optimization_response(response, request)
        
        return result
    
    def _extract_optimization_goals(self, quality_feedback: Dict[str, Any]) -> List[str]:
        """Extract optimization goals from quality feedback"""
        goals = []
        
        validation_result = quality_feedback.get("validation_result")
        if not validation_result:
            return ["general_improvement"]
        
        # Analyze quality scores to determine goals
        detailed_scores = quality_feedback.get("detailed_scores", {})
        
        for metric, score in detailed_scores.items():
            if score < 0.7:
                if metric == "completeness":
                    goals.append("improve_completeness")
                elif metric == "technical_accuracy":
                    goals.append("enhance_technical_accuracy")
                elif metric == "cursor_ai_compatibility":
                    goals.append("optimize_for_cursor_ai")
                elif metric == "clarity":
                    goals.append("improve_clarity")
                elif metric == "specificity":
                    goals.append("increase_specificity")
                elif metric == "actionability":
                    goals.append("enhance_actionability")
        
        if not goals:
            goals = ["general_optimization"]
        
        return goals
    
    def _choose_optimization_strategy(self, quality_feedback: Dict[str, Any]) -> str:
        """Choose optimization strategy based on feedback"""
        detailed_scores = quality_feedback.get("detailed_scores", {})
        
        # Prioritize the lowest scoring aspect
        if detailed_scores:
            lowest_metric = min(detailed_scores.items(), key=lambda x: x[1])
            metric_name = lowest_metric[0]
            
            if metric_name in ["technical_accuracy", "completeness"]:
                return "5g_domain_enhancement"
            elif metric_name in ["cursor_ai_compatibility", "actionability"]:
                return "cursor_ai_optimization"
        
        return "cursor_ai_optimization"  # Default strategy
    
    def _generate_optimization_prompt(self, request: OptimizationRequest, strategy: str) -> str:
        """Generate the optimization prompt for the LLM"""
        template = self.optimization_templates.get(strategy, self.optimization_templates["cursor_ai_optimization"])
        
        return template.format(
            base_prompt=request.base_prompt,
            quality_feedback=json.dumps(request.quality_feedback, indent=2),
            optimization_goals="\n".join(f"- {goal}" for goal in request.optimization_goals)
        )
    
    async def _call_llm(self, prompt: str, model: str) -> str:
        """Call the LLM with the optimization prompt"""
        model_config = self.model_configs.get(model, self.model_configs["gpt-4"])
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert prompt engineer specializing in optimizing prompts for AI code generation tools, particularly in the 5G telecommunications domain."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=model_config["max_tokens"],
                temperature=model_config["temperature"],
                top_p=model_config["top_p"]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"LLM call failed: {str(e)}")
            raise
    
    def _parse_optimization_response(self, response: str, request: OptimizationRequest) -> OptimizationResult:
        """Parse the LLM response into structured result"""
        # Simple parsing - in practice, you'd want more sophisticated parsing
        lines = response.split('\n')
        
        optimized_prompt = ""
        reasoning = ""
        changes_made = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if "optimized" in line.lower() and ("prompt" in line.lower() or "version" in line.lower()):
                current_section = "prompt"
                continue
            elif "explanation" in line.lower() or "reasoning" in line.lower():
                current_section = "reasoning"
                continue
            elif "improvements" in line.lower() or "changes" in line.lower():
                current_section = "changes"
                continue
            
            if current_section == "prompt" and line:
                optimized_prompt += line + "\n"
            elif current_section == "reasoning" and line:
                reasoning += line + " "
            elif current_section == "changes" and line.startswith("-"):
                changes_made.append(line[1:].strip())
        
        # If no structured sections found, use the entire response as optimized prompt
        if not optimized_prompt:
            optimized_prompt = response
        
        # Calculate improvement score (simplified)
        improvement_score = self._calculate_improvement_score(request.base_prompt, optimized_prompt)
        
        return OptimizationResult(
            optimized_prompt=optimized_prompt.strip(),
            improvement_score=improvement_score,
            changes_made=changes_made,
            reasoning=reasoning.strip(),
            metadata={
                "target_model": request.target_model,
                "optimization_goals": request.optimization_goals,
                "response_length": len(response)
            }
        )
    
    def _calculate_improvement_score(self, original: str, optimized: str) -> float:
        """Calculate a simple improvement score"""
        # Simple heuristics for improvement score
        score = 0.5  # Base score
        
        # Length improvement (optimized should be more detailed)
        length_ratio = len(optimized) / len(original) if len(original) > 0 else 1
        if 1.1 <= length_ratio <= 2.0:  # 10% to 100% increase is good
            score += 0.2
        elif length_ratio > 2.0:  # Too much increase might be verbose
            score += 0.1
        
        # Structure improvement (more sections)
        original_sections = len([line for line in original.split('\n') if line.strip().startswith('#')])
        optimized_sections = len([line for line in optimized.split('\n') if line.strip().startswith('#')])
        
        if optimized_sections > original_sections:
            score += 0.2
        
        # Technical terms (5G domain)
        domain_terms = ["5G", "NR", "gNodeB", "AMF", "SMF", "UPF", "NGAP", "RRC"]
        original_terms = sum(1 for term in domain_terms if term in original)
        optimized_terms = sum(1 for term in domain_terms if term in optimized)
        
        if optimized_terms > original_terms:
            score += 0.1
        
        return min(score, 1.0)
    
    async def _validate_optimization(self, original: str, result: OptimizationResult) -> Dict[str, Any]:
        """Validate the optimization result"""
        validation = {
            "is_valid": True,
            "issues": [],
            "improvements": []
        }
        
        # Check if optimization is significantly different
        if len(result.optimized_prompt) < len(original) * 0.8:
            validation["issues"].append("Optimized prompt is significantly shorter")
        
        # Check if key sections are preserved
        key_sections = ["context", "requirements", "constraints"]
        for section in key_sections:
            if section.lower() in original.lower() and section.lower() not in result.optimized_prompt.lower():
                validation["issues"].append(f"Key section '{section}' may have been removed")
        
        # Check for improvements
        if "##" in result.optimized_prompt and "##" not in original:
            validation["improvements"].append("Added structured sections")
        
        if len(result.changes_made) > 0:
            validation["improvements"].append(f"Made {len(result.changes_made)} specific improvements")
        
        if validation["issues"]:
            validation["is_valid"] = len(validation["issues"]) <= 1  # Allow minor issues
        
        return validation
    
    async def generate_examples(self, prompt: str, num_examples: int = 3) -> List[str]:
        """Generate example implementations based on the prompt"""
        if not self.openai_client:
            return []
        
        try:
            example_prompt = f"""
Based on this prompt, generate {num_examples} brief code examples that demonstrate the expected implementation:

{prompt}

Provide concise, practical examples that show different aspects of the implementation.
"""
            
            response = await self._call_llm(example_prompt, "gpt-3.5-turbo")
            
            # Simple parsing of examples
            examples = []
            lines = response.split('\n')
            current_example = ""
            
            for line in lines:
                if line.strip().startswith("```") and current_example:
                    examples.append(current_example.strip())
                    current_example = ""
                elif line.strip().startswith("```"):
                    current_example = ""
                elif current_example is not None:
                    current_example += line + "\n"
            
            if current_example:
                examples.append(current_example.strip())
            
            return examples[:num_examples]
            
        except Exception as e:
            self.logger.error(f"Example generation failed: {str(e)}")
            return []
    
    async def test_prompt_effectiveness(self, prompt: str) -> Dict[str, Any]:
        """Test the effectiveness of a prompt by generating sample code"""
        if not self.openai_client:
            return {"success": False, "error": "LLM not available"}
        
        try:
            test_response = await self._call_llm(prompt, "gpt-3.5-turbo")
            
            # Analyze the response quality
            analysis = {
                "response_length": len(test_response),
                "has_code": "```" in test_response or "def " in test_response or "class " in test_response,
                "has_comments": "#" in test_response or "//" in test_response,
                "has_docstring": '"""' in test_response or "'''" in test_response,
                "effectiveness_score": 0.0
            }
            
            # Calculate effectiveness score
            score = 0.0
            if analysis["has_code"]:
                score += 0.4
            if analysis["has_comments"]:
                score += 0.2
            if analysis["has_docstring"]:
                score += 0.2
            if analysis["response_length"] > 100:
                score += 0.2
            
            analysis["effectiveness_score"] = score
            
            return {
                "success": True,
                "test_response": test_response,
                "analysis": analysis
            }
            
        except Exception as e:
            self.logger.error(f"Prompt effectiveness testing failed: {str(e)}")
            return {"success": False, "error": str(e)}
