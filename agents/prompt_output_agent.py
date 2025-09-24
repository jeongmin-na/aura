"""
Prompt Output Agent - Final processing and formatting of optimized prompts
"""

import asyncio
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from knowledge_base.knowledge_manager import KnowledgeManager
from utils.config import Config
from utils.logger import AgentLogger

@dataclass
class OutputFormat:
    """Output format specification"""
    name: str
    extension: str
    template: str
    metadata_required: List[str]

@dataclass
class ProcessedOutput:
    """Processed output result"""
    formatted_prompt: str
    metadata: Dict[str, Any]
    quality_metrics: Dict[str, float]
    export_formats: Dict[str, str]

class PromptOutputAgent:
    """
    Agent responsible for prompt output processing and optimization
    
    Functions:
    1. Prompt Structuring
    2. Cursor AI Format Conversion
    3. Verification and Testing
    """
    
    def __init__(self, config: Config, knowledge_manager: KnowledgeManager):
        self.config = config
        self.knowledge_manager = knowledge_manager
        self.logger = AgentLogger("PromptOutputAgent")
        
        # Output format templates
        self.output_formats = {
            "cursor_ai": OutputFormat(
                name="Cursor AI",
                extension=".md",
                template=self._get_cursor_ai_template(),
                metadata_required=["domain", "complexity", "requirements"]
            ),
            "generic": OutputFormat(
                name="Generic AI",
                extension=".txt",
                template=self._get_generic_template(),
                metadata_required=["title", "description"]
            ),
            "structured_json": OutputFormat(
                name="Structured JSON",
                extension=".json",
                template=self._get_json_template(),
                metadata_required=["schema_version", "prompt_type"]
            )
        }
        
        # Quality enhancement patterns
        self.enhancement_patterns = {
            "cursor_ai_best_practices": [
                {
                    "pattern": r"implement",
                    "enhancement": "implement with proper error handling and logging"
                },
                {
                    "pattern": r"create function",
                    "enhancement": "create a well-documented function with type hints"
                },
                {
                    "pattern": r"write code",
                    "enhancement": "write clean, maintainable code following best practices"
                }
            ],
            "5g_domain_enhancements": [
                {
                    "pattern": r"\b5G\b",
                    "enhancement": "5G (New Radio) with specific focus on 3GPP standards"
                },
                {
                    "pattern": r"\bbase station\b",
                    "enhancement": "gNodeB (5G base station)"
                },
                {
                    "pattern": r"\blatency\b",
                    "enhancement": "latency (target: <1ms for URLLC applications)"
                }
            ]
        }
    
    async def initialize(self) -> None:
        """Initialize the prompt output agent"""
        self.logger.info("Initializing Prompt Output Agent")
        
        # Load output templates
        await self._load_output_templates()
        
        # Initialize formatters
        await self._initialize_formatters()
        
        self.logger.info("Prompt Output Agent initialized successfully")
    
    async def shutdown(self) -> None:
        """Shutdown the agent gracefully"""
        self.logger.info("Shutting down Prompt Output Agent")
    
    async def process_output(
        self,
        optimized_prompt: str,
        output_format: str = "cursor_ai",
        validation_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main method for processing and formatting output
        
        Args:
            optimized_prompt: The optimized prompt to process
            output_format: Target output format
            validation_results: Results from quality validation
            
        Returns:
            Processed output with multiple formats
        """
        self.logger.info(f"Processing output for format: {output_format}")
        
        try:
            # Step 1: Prompt Structuring
            self.logger.push_context("Prompt Structuring")
            structured_prompt = await self._structure_prompt(optimized_prompt, validation_results)
            self.logger.pop_context()
            
            # Step 2: Format-specific Processing
            self.logger.push_context("Format Processing")
            formatted_output = await self._format_for_target(structured_prompt, output_format)
            self.logger.pop_context()
            
            # Step 3: Quality Enhancement
            self.logger.push_context("Quality Enhancement")
            enhanced_output = await self._enhance_output_quality(formatted_output, output_format)
            self.logger.pop_context()
            
            # Step 4: Verification and Testing
            self.logger.push_context("Verification")
            verification_result = await self._verify_output(enhanced_output, output_format)
            self.logger.pop_context()
            
            # Step 5: Generate Multiple Formats
            self.logger.push_context("Multi-format Generation")
            export_formats = await self._generate_export_formats(enhanced_output, validation_results)
            self.logger.pop_context()
            
            # Compile final result
            processed_output = ProcessedOutput(
                formatted_prompt=enhanced_output,
                metadata=self._generate_metadata(optimized_prompt, validation_results),
                quality_metrics=self._calculate_output_quality(enhanced_output),
                export_formats=export_formats
            )
            
            self.logger.info("Output processing completed successfully")
            
            return {
                "success": True,
                "final_prompt": processed_output.formatted_prompt,
                "metadata": processed_output.metadata,
                "quality_metrics": processed_output.quality_metrics,
                "export_formats": processed_output.export_formats,
                "verification_result": verification_result
            }\n            \n        except Exception as e:\n            self.logger.error(f\"Output processing failed: {str(e)}\")\n            return {\n                \"success\": False,\n                \"error\": str(e),\n                \"final_prompt\": optimized_prompt  # Fallback to original\n            }\n    \n    async def _structure_prompt(self, prompt: str, validation_results: Optional[Dict[str, Any]]) -> str:\n        \"\"\"Structure the prompt with clear sections and organization\"\"\"\n        self.logger.info(\"Structuring prompt\")\n        \n        # Parse existing structure\n        sections = self._parse_prompt_sections(prompt)\n        \n        # Reorganize sections according to best practices\n        structured_sections = self._reorganize_sections(sections)\n        \n        # Add missing sections if needed\n        complete_sections = await self._add_missing_sections(structured_sections, validation_results)\n        \n        # Format with proper markdown structure\n        structured_prompt = self._format_sections(complete_sections)\n        \n        return structured_prompt\n    \n    def _parse_prompt_sections(self, prompt: str) -> Dict[str, str]:\n        \"\"\"Parse prompt into identifiable sections\"\"\"\n        sections = {}\n        \n        # Split by markdown headers\n        lines = prompt.split('\\n')\n        current_section = \"introduction\"\n        current_content = []\n        \n        for line in lines:\n            # Check for markdown headers\n            header_match = re.match(r'^(#+)\\s+(.+)$', line.strip())\n            if header_match:\n                # Save previous section\n                if current_content:\n                    sections[current_section] = '\\n'.join(current_content).strip()\n                \n                # Start new section\n                level = len(header_match.group(1))\n                section_title = header_match.group(2).lower().replace(' ', '_')\n                current_section = section_title\n                current_content = []\n            else:\n                current_content.append(line)\n        \n        # Don't forget the last section\n        if current_content:\n            sections[current_section] = '\\n'.join(current_content).strip()\n        \n        return sections\n    \n    def _reorganize_sections(self, sections: Dict[str, str]) -> Dict[str, str]:\n        \"\"\"Reorganize sections according to best practices\"\"\"\n        # Define ideal section order\n        ideal_order = [\n            \"system_context\",\n            \"domain_context\", \n            \"requirements\",\n            \"technical_specifications\",\n            \"constraints\",\n            \"implementation_guidelines\",\n            \"examples\",\n            \"task\",\n            \"deliverables\"\n        ]\n        \n        reorganized = {}\n        \n        # Map existing sections to ideal structure\n        section_mapping = {\n            \"context\": \"system_context\",\n            \"system_context\": \"system_context\",\n            \"5g_context\": \"domain_context\",\n            \"domain_context\": \"domain_context\",\n            \"requirements\": \"requirements\",\n            \"specifications\": \"technical_specifications\",\n            \"technical_specifications\": \"technical_specifications\",\n            \"constraints\": \"constraints\",\n            \"guidelines\": \"implementation_guidelines\",\n            \"implementation_guidelines\": \"implementation_guidelines\",\n            \"examples\": \"examples\",\n            \"task\": \"task\",\n            \"deliverables\": \"deliverables\"\n        }\n        \n        # Reorganize existing sections\n        for section_key, content in sections.items():\n            mapped_key = section_mapping.get(section_key, section_key)\n            if mapped_key in reorganized:\n                reorganized[mapped_key] += \"\\n\\n\" + content\n            else:\n                reorganized[mapped_key] = content\n        \n        # Return in ideal order\n        ordered_sections = {}\n        for section in ideal_order:\n            if section in reorganized:\n                ordered_sections[section] = reorganized[section]\n        \n        # Add any remaining sections\n        for section, content in reorganized.items():\n            if section not in ordered_sections:\n                ordered_sections[section] = content\n        \n        return ordered_sections\n    \n    async def _add_missing_sections(self, sections: Dict[str, str], validation_results: Optional[Dict[str, Any]]) -> Dict[str, str]:\n        \"\"\"Add missing sections based on validation results\"\"\"\n        complete_sections = sections.copy()\n        \n        # Add system context if missing\n        if \"system_context\" not in complete_sections:\n            complete_sections[\"system_context\"] = self._generate_default_system_context()\n        \n        # Add domain context if missing\n        if \"domain_context\" not in complete_sections:\n            complete_sections[\"domain_context\"] = self._generate_default_domain_context()\n        \n        # Add task section if missing\n        if \"task\" not in complete_sections:\n            complete_sections[\"task\"] = self._generate_default_task_section()\n        \n        # Add deliverables if missing\n        if \"deliverables\" not in complete_sections:\n            complete_sections[\"deliverables\"] = self._generate_default_deliverables()\n        \n        return complete_sections\n    \n    def _format_sections(self, sections: Dict[str, str]) -> str:\n        \"\"\"Format sections with proper markdown structure\"\"\"\n        formatted_parts = []\n        \n        section_titles = {\n            \"system_context\": \"# System Context\",\n            \"domain_context\": \"# Domain Context\", \n            \"requirements\": \"# Requirements\",\n            \"technical_specifications\": \"# Technical Specifications\",\n            \"constraints\": \"# Constraints and Guidelines\",\n            \"implementation_guidelines\": \"# Implementation Guidelines\",\n            \"examples\": \"# Examples\",\n            \"task\": \"# Task\",\n            \"deliverables\": \"# Deliverables\"\n        }\n        \n        for section_key, content in sections.items():\n            if content and content.strip():\n                title = section_titles.get(section_key, f\"# {section_key.replace('_', ' ').title()}\")\n                formatted_parts.append(title)\n                formatted_parts.append(content.strip())\n                formatted_parts.append(\"\")  # Empty line between sections\n        \n        return \"\\n\".join(formatted_parts)\n    \n    async def _format_for_target(self, structured_prompt: str, output_format: str) -> str:\n        \"\"\"Format prompt for specific target format\"\"\"\n        self.logger.info(f\"Formatting for target: {output_format}\")\n        \n        format_spec = self.output_formats.get(output_format)\n        if not format_spec:\n            self.logger.warning(f\"Unknown output format: {output_format}, using generic\")\n            format_spec = self.output_formats[\"generic\"]\n        \n        if output_format == \"cursor_ai\":\n            return await self._format_for_cursor_ai(structured_prompt)\n        elif output_format == \"structured_json\":\n            return await self._format_for_json(structured_prompt)\n        else:\n            return structured_prompt  # Generic format\n    \n    async def _format_for_cursor_ai(self, prompt: str) -> str:\n        \"\"\"Format specifically for Cursor AI compatibility\"\"\"\n        # Add Cursor AI specific elements\n        cursor_header = \"\"\"<!-- Cursor AI Optimized Prompt -->\n<!-- Generated by DLD to Cursor AI Prompt Generation System -->\n<!-- Domain: 5G Telecommunications -->\n\n\"\"\"\n        \n        # Add file extension hints if code generation is expected\n        code_hint = \"\"\"\\n\\n---\\n**Note for Cursor AI**: This prompt is optimized for generating production-ready code. Consider the following:\n- Use appropriate file extensions (.py, .cpp, .js, etc.)\n- Include proper imports and dependencies\n- Follow the coding conventions specified above\n- Generate complete, testable functions\n---\\n\"\"\"\n        \n        return cursor_header + prompt + code_hint\n    \n    async def _format_for_json(self, prompt: str) -> str:\n        \"\"\"Format as structured JSON\"\"\"\n        sections = self._parse_prompt_sections(prompt)\n        \n        json_structure = {\n            \"prompt_metadata\": {\n                \"version\": \"1.0\",\n                \"domain\": \"5G_telecommunications\",\n                \"generated_at\": datetime.now().isoformat(),\n                \"format\": \"structured_json\"\n            },\n            \"system_context\": sections.get(\"system_context\", \"\"),\n            \"domain_context\": sections.get(\"domain_context\", \"\"),\n            \"requirements\": sections.get(\"requirements\", \"\"),\n            \"constraints\": sections.get(\"constraints\", \"\"),\n            \"task\": sections.get(\"task\", \"\"),\n            \"examples\": sections.get(\"examples\", \"\"),\n            \"deliverables\": sections.get(\"deliverables\", \"\")\n        }\n        \n        return json.dumps(json_structure, indent=2, ensure_ascii=False)\n    \n    async def _enhance_output_quality(self, formatted_output: str, output_format: str) -> str:\n        \"\"\"Enhance output quality with domain-specific improvements\"\"\"\n        self.logger.info(\"Enhancing output quality\")\n        \n        enhanced = formatted_output\n        \n        # Apply Cursor AI best practices\n        if output_format == \"cursor_ai\":\n            for pattern_info in self.enhancement_patterns[\"cursor_ai_best_practices\"]:\n                pattern = pattern_info[\"pattern\"]\n                enhancement = pattern_info[\"enhancement\"]\n                enhanced = re.sub(pattern, enhancement, enhanced, flags=re.IGNORECASE)\n        \n        # Apply 5G domain enhancements\n        for pattern_info in self.enhancement_patterns[\"5g_domain_enhancements\"]:\n            pattern = pattern_info[\"pattern\"]\n            enhancement = pattern_info[\"enhancement\"]\n            enhanced = re.sub(pattern, enhancement, enhanced)\n        \n        # Add quality indicators\n        enhanced = self._add_quality_indicators(enhanced)\n        \n        return enhanced\n    \n    def _add_quality_indicators(self, prompt: str) -> str:\n        \"\"\"Add quality indicators to the prompt\"\"\"\n        quality_footer = \"\"\"\\n\\n---\\n## Quality Indicators\\n✅ **Technical Accuracy**: 5G domain expertise applied\\n✅ **Cursor AI Compatibility**: Optimized for AI code generation\\n✅ **Completeness**: All essential sections included\\n✅ **Actionability**: Clear, specific instructions provided\\n---\"\"\"\n        \n        return prompt + quality_footer\n    \n    async def _verify_output(self, enhanced_output: str, output_format: str) -> Dict[str, Any]:\n        \"\"\"Verify the final output quality\"\"\"\n        self.logger.info(\"Verifying output\")\n        \n        verification = {\n            \"is_valid\": True,\n            \"issues\": [],\n            \"suggestions\": [],\n            \"quality_score\": 0.0\n        }\n        \n        # Check basic structure\n        if not enhanced_output.strip():\n            verification[\"is_valid\"] = False\n            verification[\"issues\"].append(\"Output is empty\")\n            return verification\n        \n        # Check for required sections (for cursor_ai format)\n        if output_format == \"cursor_ai\":\n            required_sections = [\"context\", \"task\", \"requirements\"]\n            for section in required_sections:\n                if section.lower() not in enhanced_output.lower():\n                    verification[\"issues\"].append(f\"Missing required section: {section}\")\n        \n        # Check for 5G domain content\n        domain_terms = [\"5G\", \"gNodeB\", \"NR\", \"AMF\", \"SMF\", \"UPF\"]\n        domain_coverage = sum(1 for term in domain_terms if term in enhanced_output)\n        \n        if domain_coverage == 0:\n            verification[\"suggestions\"].append(\"Consider adding more 5G domain-specific terminology\")\n        \n        # Check length appropriateness\n        if len(enhanced_output) < 500:\n            verification[\"suggestions\"].append(\"Prompt might be too brief for complex tasks\")\n        elif len(enhanced_output) > 5000:\n            verification[\"suggestions\"].append(\"Prompt might be too verbose\")\n        \n        # Calculate quality score\n        quality_score = 1.0\n        quality_score -= len(verification[\"issues\"]) * 0.2\n        quality_score -= len(verification[\"suggestions\"]) * 0.1\n        quality_score = max(0.0, quality_score)\n        \n        verification[\"quality_score\"] = quality_score\n        \n        if verification[\"issues\"]:\n            verification[\"is_valid\"] = False\n        \n        return verification\n    \n    async def _generate_export_formats(self, enhanced_output: str, validation_results: Optional[Dict[str, Any]]) -> Dict[str, str]:\n        \"\"\"Generate multiple export formats\"\"\"\n        self.logger.info(\"Generating export formats\")\n        \n        export_formats = {}\n        \n        # Cursor AI format (markdown)\n        export_formats[\"cursor_ai_md\"] = await self._format_for_cursor_ai(enhanced_output)\n        \n        # Plain text format\n        export_formats[\"plain_text\"] = self._strip_markdown(enhanced_output)\n        \n        # JSON format\n        export_formats[\"structured_json\"] = await self._format_for_json(enhanced_output)\n        \n        # Template format for reuse\n        export_formats[\"template\"] = self._create_template_format(enhanced_output)\n        \n        return export_formats\n    \n    def _strip_markdown(self, text: str) -> str:\n        \"\"\"Strip markdown formatting for plain text\"\"\"\n        # Remove markdown headers\n        text = re.sub(r'^#+\\s+', '', text, flags=re.MULTILINE)\n        \n        # Remove markdown emphasis\n        text = re.sub(r'\\*\\*(.*?)\\*\\*', r'\\1', text)\n        text = re.sub(r'\\*(.*?)\\*', r'\\1', text)\n        \n        # Remove markdown lists\n        text = re.sub(r'^\\s*[-*]\\s+', '• ', text, flags=re.MULTILINE)\n        \n        # Remove code blocks\n        text = re.sub(r'```[^`]*```', '[CODE BLOCK]', text, flags=re.DOTALL)\n        text = re.sub(r'`([^`]+)`', r'\\1', text)\n        \n        return text\n    \n    def _create_template_format(self, prompt: str) -> str:\n        \"\"\"Create a template format for reuse\"\"\"\n        template = prompt\n        \n        # Replace specific values with placeholders\n        template = re.sub(r'\\b\\d+\\.\\d+\\s*(?:MHz|GHz|Mbps|Gbps|ms)\\b', '{PERFORMANCE_VALUE}', template)\n        template = re.sub(r'\\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\\b', '{CLASS_NAME}', template)\n        \n        # Add template header\n        template_header = \"\"\"<!-- Template: 5G DLD to Cursor AI Prompt -->\n<!-- Usage: Replace {PLACEHOLDERS} with actual values -->\n<!-- Generated: {TIMESTAMP} -->\n\n\"\"\".format(TIMESTAMP=datetime.now().isoformat())\n        \n        return template_header + template\n    \n    def _generate_metadata(self, original_prompt: str, validation_results: Optional[Dict[str, Any]]) -> Dict[str, Any]:\n        \"\"\"Generate metadata for the output\"\"\"\n        metadata = {\n            \"generated_at\": datetime.now().isoformat(),\n            \"system_version\": \"1.0\",\n            \"domain\": \"5G_telecommunications\",\n            \"prompt_length\": len(original_prompt),\n            \"format\": \"cursor_ai_optimized\",\n            \"quality_validated\": validation_results is not None\n        }\n        \n        if validation_results:\n            metadata[\"validation_score\"] = validation_results.get(\"quality_score\", 0.0)\n            metadata[\"validation_passed\"] = validation_results.get(\"success\", False)\n        \n        return metadata\n    \n    def _calculate_output_quality(self, enhanced_output: str) -> Dict[str, float]:\n        \"\"\"Calculate quality metrics for the output\"\"\"\n        metrics = {\n            \"completeness\": 0.0,\n            \"structure\": 0.0,\n            \"domain_coverage\": 0.0,\n            \"actionability\": 0.0\n        }\n        \n        # Completeness (sections present)\n        expected_sections = [\"context\", \"requirements\", \"task\", \"constraints\"]\n        present_sections = sum(1 for section in expected_sections if section.lower() in enhanced_output.lower())\n        metrics[\"completeness\"] = present_sections / len(expected_sections)\n        \n        # Structure (markdown formatting)\n        headers = len(re.findall(r'^#+\\s+', enhanced_output, re.MULTILINE))\n        lists = len(re.findall(r'^\\s*[-*]\\s+', enhanced_output, re.MULTILINE))\n        metrics[\"structure\"] = min((headers + lists) / 10, 1.0)\n        \n        # Domain coverage (5G terms)\n        domain_terms = [\"5G\", \"NR\", \"gNodeB\", \"AMF\", \"SMF\", \"UPF\", \"NGAP\", \"RRC\", \"latency\", \"throughput\"]\n        found_terms = sum(1 for term in domain_terms if term in enhanced_output)\n        metrics[\"domain_coverage\"] = min(found_terms / len(domain_terms), 1.0)\n        \n        # Actionability (action verbs)\n        action_verbs = [\"implement\", \"create\", \"develop\", \"build\", \"design\", \"generate\"]\n        found_verbs = sum(1 for verb in action_verbs if verb in enhanced_output.lower())\n        metrics[\"actionability\"] = min(found_verbs / 3, 1.0)\n        \n        return metrics\n    \n    # Default content generators\n    \n    def _generate_default_system_context(self) -> str:\n        return \"\"\"You are an expert 5G telecommunications engineer with deep knowledge of wireless communication systems, protocol implementation, and network optimization.\"\"\"\n    \n    def _generate_default_domain_context(self) -> str:\n        return \"\"\"**5G Domain Context:**\n- Focus on 3GPP standards compliance\n- Consider real-time performance requirements\n- Implement with scalability and reliability in mind\n- Follow telecommunications industry best practices\"\"\"\n    \n    def _generate_default_task_section(self) -> str:\n        return \"\"\"Implement the specified functionality according to the requirements and technical specifications provided above.\"\"\"\n    \n    def _generate_default_deliverables(self) -> str:\n        return \"\"\"**Expected Deliverables:**\n- Complete, working implementation\n- Comprehensive documentation\n- Unit tests with good coverage\n- Performance benchmarks where applicable\"\"\"\n    \n    # Template getters\n    \n    def _get_cursor_ai_template(self) -> str:\n        return \"\"\"\n# {title}\n\n## System Context\n{system_context}\n\n## Domain Context  \n{domain_context}\n\n## Requirements\n{requirements}\n\n## Technical Specifications\n{technical_specifications}\n\n## Constraints and Guidelines\n{constraints}\n\n## Task\n{task}\n\n## Deliverables\n{deliverables}\n\"\"\"\n    \n    def _get_generic_template(self) -> str:\n        return \"\"\"\n{title}\n\n{description}\n\nRequirements:\n{requirements}\n\nTask:\n{task}\n\"\"\"\n    \n    def _get_json_template(self) -> str:\n        return \"\"\"\n{\n  \"prompt_metadata\": {\n    \"version\": \"1.0\",\n    \"domain\": \"{domain}\",\n    \"prompt_type\": \"{prompt_type}\"\n  },\n  \"content\": {\n    \"system_context\": \"{system_context}\",\n    \"requirements\": \"{requirements}\",\n    \"task\": \"{task}\"\n  }\n}\n\"\"\"\n    \n    async def _load_output_templates(self) -> None:\n        \"\"\"Load output templates from knowledge base\"\"\"\n        self.logger.info(\"Loading output templates\")\n    \n    async def _initialize_formatters(self) -> None:\n        \"\"\"Initialize formatting components\"\"\"\n        self.logger.info(\"Initializing formatters\")
