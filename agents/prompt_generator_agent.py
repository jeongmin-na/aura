"""
Prompt Generator Agent - 6-step pipeline for generating optimized Cursor AI prompts
"""

import asyncio
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import networkx as nx

from knowledge_base.knowledge_manager import KnowledgeManager
from utils.config import Config
from utils.logger import AgentLogger

@dataclass
class CodeMapping:
    """Represents mapping between DLD and existing code"""
    dld_section: str
    code_file: str
    function_name: str
    confidence: float
    mapping_type: str  # direct, indirect, missing

@dataclass
class PromptComponent:
    """Components of the generated prompt"""
    component_type: str  # context, instruction, example, constraint
    content: str
    priority: int
    source: str  # which step generated this

class PromptGeneratorAgent:
    """
    Agent responsible for the 6-step prompt generation pipeline:
    
    0. Project Code Structure Analysis
    1. DLD Parsing and Conversion
    2. System Prompt Loading
    3. Cursor AI Rules Integration
    4. Code Mapping Analysis
    5. Coding Style Extraction
    6. Context Enhancement
    """
    
    def __init__(self, config: Config, knowledge_manager: KnowledgeManager):
        self.config = config
        self.knowledge_manager = knowledge_manager
        self.logger = AgentLogger("PromptGeneratorAgent")
        
        # Pipeline state
        self.pipeline_state: Dict[str, Any] = {}
        self.prompt_components: List[PromptComponent] = []
        
        # Code analysis patterns
        self.code_patterns = {
            "function_definitions": r'(?:def|function|async\s+def)\s+(\w+)',
            "class_definitions": r'class\s+(\w+)',
            "import_statements": r'(?:import|from)\s+([^\s]+)',
            "api_endpoints": r'@app\.(?:get|post|put|delete)\(["\']([^"\']+)["\']',
            "database_models": r'class\s+(\w+).*(?:Model|Entity)',
            "test_functions": r'(?:def|it|describe)\s+(test_\w+|.*test.*)'
        }
        
        # 5G domain prompt templates
        self.domain_templates = {
            "5g_context": """
You are an expert 5G wireless communication engineer with deep knowledge of:
- 5G NR (New Radio) protocols and procedures
- 5G Core Network (5GC) architecture and network functions
- Radio Access Network (RAN) design and optimization
- Network slicing and service orchestration
- Protocol stack implementation (PHY, MAC, RLC, PDCP, RRC, NAS)
- Performance optimization and troubleshooting

When generating code, consider:
- Real-time performance requirements
- Hardware constraints and optimization
- Protocol compliance and interoperability
- Security and authentication mechanisms
- Scalability and network efficiency
""",
            "base_station_context": """
For 5G base station (gNodeB) development, focus on:
- Radio frequency management and beamforming
- Cell management and handover procedures
- Resource scheduling and allocation
- Interference mitigation techniques
- Power control and energy efficiency
- Multi-antenna (MIMO) processing
- Carrier aggregation implementation
""",
            "cursor_ai_integration": """
Generate code that is:
- Well-documented with clear inline comments
- Modular and testable with proper separation of concerns
- Following established coding patterns in the project
- Optimized for the specific domain requirements
- Including appropriate error handling and logging
- Compatible with existing codebase architecture
"""
        }
    
    async def initialize(self) -> None:
        """Initialize the prompt generator agent"""
        self.logger.info("Initializing Prompt Generator Agent")
        
        # Load prompt templates and patterns
        await self._load_prompt_templates()
        
        # Initialize code analysis tools
        await self._initialize_code_analyzers()
        
        self.logger.info("Prompt Generator Agent initialized successfully")
    
    async def shutdown(self) -> None:
        """Shutdown the agent gracefully"""
        self.logger.info("Shutting down Prompt Generator Agent")
    
    async def generate_prompt(
        self,
        validated_dld: Dict[str, Any],
        project_path: Optional[str] = None,
        output_format: str = "cursor_ai"
    ) -> Dict[str, Any]:
        """
        Main method for the 6-step prompt generation pipeline
        
        Args:
            validated_dld: Processed DLD from context validation
            project_path: Optional path to existing project
            output_format: Target format for the prompt
            
        Returns:
            Generated prompt and metadata
        """
        self.logger.info("Starting 6-step prompt generation pipeline")
        
        # Initialize pipeline state
        self.pipeline_state = {
            "validated_dld": validated_dld,
            "project_path": project_path,
            "output_format": output_format
        }
        self.prompt_components = []
        
        try:
            # Step 0: Project Code Structure Analysis
            self.logger.push_context("Step 0: Project Structure Analysis")
            await self._step0_project_structure_analysis()
            self.logger.pop_context()
            
            # Step 1: DLD Parsing and Conversion
            self.logger.push_context("Step 1: DLD Parsing")
            await self._step1_dld_parsing_conversion()
            self.logger.pop_context()
            
            # Step 2: System Prompt Loading
            self.logger.push_context("Step 2: System Prompt Loading")
            await self._step2_system_prompt_loading()
            self.logger.pop_context()
            
            # Step 3: Cursor AI Rules Integration
            self.logger.push_context("Step 3: Cursor AI Rules")
            await self._step3_cursor_ai_rules_integration()
            self.logger.pop_context()
            
            # Step 4: Code Mapping Analysis
            self.logger.push_context("Step 4: Code Mapping")
            await self._step4_code_mapping_analysis()
            self.logger.pop_context()
            
            # Step 5: Coding Style Extraction
            self.logger.push_context("Step 5: Coding Style")
            await self._step5_coding_style_extraction()
            self.logger.pop_context()
            
            # Step 6: Context Enhancement
            self.logger.push_context("Step 6: Context Enhancement")
            await self._step6_context_enhancement()
            self.logger.pop_context()
            
            # Assemble final prompt
            generated_prompt = await self._assemble_final_prompt()
            
            self.logger.info("Prompt generation pipeline completed successfully")
            
            return {
                "success": True,
                "generated_prompt": generated_prompt,
                "pipeline_state": self.pipeline_state,
                "prompt_components": self.prompt_components,
                "metrics": {
                    "total_components": len(self.prompt_components),
                    "prompt_length": len(generated_prompt),
                    "sections_processed": len(validated_dld.get("sections", [])),
                    "code_files_analyzed": len(self.pipeline_state.get("code_files", []))
                }
            }
            
        except Exception as e:
            self.logger.error(f"Prompt generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "pipeline_state": self.pipeline_state
            }
    
    async def _step0_project_structure_analysis(self) -> None:
        """Step 0: Analyze project code structure"""
        self.logger.info("Analyzing project code structure")
        
        project_path = self.pipeline_state.get("project_path")
        if not project_path:
            self.logger.info("No project path provided, skipping structure analysis")
            self.pipeline_state["project_analysis"] = {"files": [], "structure": {}}
            return
        
        project_dir = Path(project_path)
        if not project_dir.exists():
            self.logger.warning(f"Project path does not exist: {project_path}")
            self.pipeline_state["project_analysis"] = {"files": [], "structure": {}}
            return
        
        # Directory scanning
        directory_structure = await self._scan_directory_structure(project_dir)
        
        # File dependency mapping
        dependency_map = await self._analyze_file_dependencies(project_dir)
        
        # Architecture pattern identification
        architecture_patterns = await self._identify_architecture_patterns(project_dir)
        
        self.pipeline_state["project_analysis"] = {
            "directory_structure": directory_structure,
            "dependency_map": dependency_map,
            "architecture_patterns": architecture_patterns,
            "total_files": len(directory_structure.get("code_files", [])),
            "project_type": self._determine_project_type(directory_structure, architecture_patterns)
        }
        
        # Add project context component
        self.prompt_components.append(PromptComponent(
            component_type="context",
            content=self._generate_project_context_text(),
            priority=1,
            source="step0_project_structure"
        ))
    
    async def _step1_dld_parsing_conversion(self) -> None:
        """Step 1: Parse DLD and convert to structured format"""
        self.logger.info("Parsing and converting DLD")
        
        validated_dld = self.pipeline_state["validated_dld"]
        
        # Extract technical specifications
        tech_specs = await self._extract_technical_specifications(validated_dld)
        
        # Classify requirements
        classified_requirements = await self._classify_requirements(validated_dld)
        
        # Convert to markdown
        markdown_content = await self._convert_to_markdown(validated_dld)
        
        # Identify pseudocode sections
        pseudocode_sections = await self._identify_pseudocode(validated_dld)
        
        self.pipeline_state["dld_parsing"] = {
            "tech_specs": tech_specs,
            "classified_requirements": classified_requirements,
            "markdown_content": markdown_content,
            "pseudocode_sections": pseudocode_sections
        }
        
        # Add DLD components to prompt
        self.prompt_components.append(PromptComponent(
            component_type="context",
            content=f"## Technical Specifications\\n{self._format_tech_specs(tech_specs)}",
            priority=2,
            source="step1_dld_parsing"
        ))
        
        self.prompt_components.append(PromptComponent(
            component_type="instruction",
            content=f"## Requirements\\n{self._format_requirements(classified_requirements)}",
            priority=3,
            source="step1_dld_parsing"
        ))
    
    async def _step2_system_prompt_loading(self) -> None:
        """Step 2: Load system prompts with 5G domain knowledge"""
        self.logger.info("Loading system prompts and domain knowledge")
        
        # Load 5G domain knowledge
        domain_knowledge = await self._load_5g_domain_knowledge()
        
        # Load coding guidelines
        coding_guidelines = await self._load_coding_guidelines()
        
        # Load quality standards
        quality_standards = await self._load_quality_standards()
        
        self.pipeline_state["system_prompts"] = {
            "domain_knowledge": domain_knowledge,
            "coding_guidelines": coding_guidelines,
            "quality_standards": quality_standards
        }
        
        # Add system prompt components
        self.prompt_components.append(PromptComponent(
            component_type="context",
            content=self.domain_templates["5g_context"],
            priority=1,
            source="step2_system_prompts"
        ))
        
        self.prompt_components.append(PromptComponent(
            component_type="context",
            content=self.domain_templates["base_station_context"],
            priority=1,
            source="step2_system_prompts"
        ))
    
    async def _step3_cursor_ai_rules_integration(self) -> None:
        """Step 3: Integrate Cursor AI specific rules and conventions"""
        self.logger.info("Integrating Cursor AI rules and team conventions")
        
        # Load team coding conventions
        team_conventions = await self._load_team_conventions()
        
        # Load project-specific rules
        project_rules = await self._load_project_rules()
        
        # Load AI utilization guidelines
        ai_guidelines = await self._load_ai_guidelines()
        
        self.pipeline_state["cursor_ai_rules"] = {
            "team_conventions": team_conventions,
            "project_rules": project_rules,
            "ai_guidelines": ai_guidelines
        }
        
        # Add Cursor AI integration component
        self.prompt_components.append(PromptComponent(
            component_type="constraint",
            content=self.domain_templates["cursor_ai_integration"],
            priority=2,
            source="step3_cursor_ai_rules"
        ))
        
        # Add specific conventions
        if team_conventions:
            self.prompt_components.append(PromptComponent(
                component_type="constraint",
                content=f"## Team Coding Conventions\\n{self._format_conventions(team_conventions)}",
                priority=2,
                source="step3_cursor_ai_rules"
            ))
    
    async def _step4_code_mapping_analysis(self) -> None:
        """Step 4: Analyze mapping between DLD and existing code"""
        self.logger.info("Analyzing DLD to code mapping")
        
        if not self.pipeline_state.get("project_analysis", {}).get("directory_structure"):
            self.logger.info("No project structure available, skipping code mapping")
            self.pipeline_state["code_mapping"] = {"mappings": [], "missing_implementations": []}
            return
        
        validated_dld = self.pipeline_state["validated_dld"]
        project_analysis = self.pipeline_state["project_analysis"]
        
        # DLD-code matching
        dld_code_matches = await self._match_dld_to_code(validated_dld, project_analysis)
        
        # Function name mapping
        function_mappings = await self._analyze_function_mappings(validated_dld, project_analysis)
        
        # Module structure analysis
        module_structure = await self._analyze_module_structure(project_analysis)
        
        self.pipeline_state["code_mapping"] = {
            "dld_code_matches": dld_code_matches,
            "function_mappings": function_mappings,
            "module_structure": module_structure,
            "missing_implementations": self._identify_missing_implementations(dld_code_matches)
        }
        
        # Add code mapping guidance
        if dld_code_matches:
            self.prompt_components.append(PromptComponent(
                component_type="context",
                content=f"## Existing Code Structure\\n{self._format_code_mappings(dld_code_matches)}",
                priority=3,
                source="step4_code_mapping"
            ))
    
    async def _step5_coding_style_extraction(self) -> None:
        """Step 5: Extract coding style from existing codebase"""
        self.logger.info("Extracting coding style patterns")
        
        if not self.pipeline_state.get("project_analysis", {}).get("directory_structure"):
            self.logger.info("No project structure available, using default style")
            self.pipeline_state["coding_style"] = self._get_default_coding_style()
            return
        
        project_analysis = self.pipeline_state["project_analysis"]
        
        # Analyze existing code patterns
        code_patterns = await self._analyze_code_patterns(project_analysis)
        
        # Extract naming conventions
        naming_conventions = await self._extract_naming_conventions(project_analysis)
        
        # Identify architecture style
        architecture_style = await self._identify_architecture_style(project_analysis)
        
        # Analyze test patterns
        test_patterns = await self._analyze_test_patterns(project_analysis)
        
        self.pipeline_state["coding_style"] = {
            "code_patterns": code_patterns,
            "naming_conventions": naming_conventions,
            "architecture_style": architecture_style,
            "test_patterns": test_patterns
        }
        
        # Add coding style guidance
        self.prompt_components.append(PromptComponent(
            component_type="constraint",
            content=f"## Coding Style Guidelines\\n{self._format_coding_style()}",
            priority=2,
            source="step5_coding_style"
        ))
    
    async def _step6_context_enhancement(self) -> None:
        """Step 6: Enhance context with domain-specific knowledge"""
        self.logger.info("Enhancing context with 5G domain knowledge")
        
        # 5G protocol knowledge
        protocol_knowledge = await self._enhance_5g_protocol_context()
        
        # Hardware constraints
        hardware_constraints = await self._identify_hardware_constraints()
        
        # Performance requirements
        performance_requirements = await self._extract_performance_requirements()
        
        self.pipeline_state["context_enhancement"] = {
            "protocol_knowledge": protocol_knowledge,
            "hardware_constraints": hardware_constraints,
            "performance_requirements": performance_requirements
        }
        
        # Add enhanced context
        self.prompt_components.append(PromptComponent(
            component_type="context",
            content=f"## 5G Protocol Context\\n{self._format_protocol_context(protocol_knowledge)}",
            priority=2,
            source="step6_context_enhancement"
        ))
        
        if hardware_constraints:
            self.prompt_components.append(PromptComponent(
                component_type="constraint",
                content=f"## Hardware Constraints\\n{self._format_hardware_constraints(hardware_constraints)}",
                priority=2,
                source="step6_context_enhancement"
            ))
    
    async def _assemble_final_prompt(self) -> str:
        """Assemble the final prompt from all components"""
        self.logger.info("Assembling final prompt")
        
        # Sort components by priority and type
        sorted_components = sorted(
            self.prompt_components,
            key=lambda x: (x.priority, x.component_type)
        )
        
        # Group components by type
        context_components = [c for c in sorted_components if c.component_type == "context"]
        instruction_components = [c for c in sorted_components if c.component_type == "instruction"]
        constraint_components = [c for c in sorted_components if c.component_type == "constraint"]
        example_components = [c for c in sorted_components if c.component_type == "example"]
        
        # Assemble prompt sections
        prompt_parts = []
        
        # System context
        if context_components:
            prompt_parts.append("# System Context")
            for component in context_components:
                prompt_parts.append(component.content)
            prompt_parts.append("")
        
        # Main instructions
        if instruction_components:
            prompt_parts.append("# Instructions")
            for component in instruction_components:
                prompt_parts.append(component.content)
            prompt_parts.append("")
        
        # Constraints and guidelines
        if constraint_components:
            prompt_parts.append("# Guidelines and Constraints")
            for component in constraint_components:
                prompt_parts.append(component.content)
            prompt_parts.append("")
        
        # Examples
        if example_components:
            prompt_parts.append("# Examples")
            for component in example_components:
                prompt_parts.append(component.content)
            prompt_parts.append("")
        
        # Add specific task instruction
        task_instruction = self._generate_task_instruction()
        prompt_parts.append("# Task")
        prompt_parts.append(task_instruction)
        
        return "\\n\\n".join(prompt_parts)
    
    # Helper methods for the pipeline steps
    
    async def _scan_directory_structure(self, project_dir: Path) -> Dict[str, Any]:
        """Scan and analyze directory structure"""
        structure = {
            "code_files": [],
            "config_files": [],
            "test_files": [],
            "documentation": [],
            "directories": []
        }
        
        try:
            for item in project_dir.rglob("*"):
                if item.is_file():
                    rel_path = str(item.relative_to(project_dir))
                    
                    if item.suffix in ['.py', '.js', '.ts', '.cpp', '.c', '.java', '.go', '.rs']:
                        if 'test' in rel_path.lower():
                            structure["test_files"].append(rel_path)
                        else:
                            structure["code_files"].append(rel_path)
                    elif item.suffix in ['.yaml', '.yml', '.json', '.ini', '.conf', '.cfg']:
                        structure["config_files"].append(rel_path)
                    elif item.suffix in ['.md', '.txt', '.rst', '.doc']:
                        structure["documentation"].append(rel_path)
                elif item.is_dir():
                    structure["directories"].append(str(item.relative_to(project_dir)))
        
        except Exception as e:
            self.logger.error(f"Error scanning directory structure: {str(e)}")
        
        return structure
    
    async def _analyze_file_dependencies(self, project_dir: Path) -> Dict[str, List[str]]:
        """Analyze dependencies between files"""
        dependency_map = {}
        
        try:
            for code_file in project_dir.rglob("*.py"):  # Focus on Python for now
                rel_path = str(code_file.relative_to(project_dir))
                dependencies = []
                
                try:
                    with open(code_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Extract import statements
                    import_matches = re.findall(self.code_patterns["import_statements"], content)
                    dependencies.extend(import_matches)
                    
                except Exception:
                    continue
                
                dependency_map[rel_path] = dependencies
        
        except Exception as e:
            self.logger.error(f"Error analyzing file dependencies: {str(e)}")
        
        return dependency_map
    
    async def _identify_architecture_patterns(self, project_dir: Path) -> List[str]:
        """Identify architecture patterns in the project"""
        patterns = []
        
        # Look for common patterns
        if (project_dir / "models").exists():
            patterns.append("MVC")
        if (project_dir / "controllers").exists():
            patterns.append("MVC")
        if (project_dir / "services").exists():
            patterns.append("Service Layer")
        if (project_dir / "repositories").exists():
            patterns.append("Repository Pattern")
        if any(p.name == "docker-compose.yml" for p in project_dir.rglob("*")):
            patterns.append("Microservices")
        if (project_dir / "tests").exists():
            patterns.append("Test-Driven Development")
        
        return patterns
    
    def _determine_project_type(self, directory_structure: Dict[str, Any], architecture_patterns: List[str]) -> str:
        """Determine the type of project"""
        code_files = directory_structure.get("code_files", [])
        
        if any(f.endswith('.py') for f in code_files):
            if any('django' in p or 'flask' in p for p in architecture_patterns):
                return "Python Web Application"
            else:
                return "Python Application"
        elif any(f.endswith(('.js', '.ts')) for f in code_files):
            return "JavaScript/TypeScript Application"
        elif any(f.endswith(('.cpp', '.c')) for f in code_files):
            return "C/C++ Application"
        else:
            return "Unknown"
    
    def _generate_project_context_text(self) -> str:
        """Generate project context description"""
        analysis = self.pipeline_state.get("project_analysis", {})
        
        if not analysis or not analysis.get("directory_structure"):
            return "No existing project structure to analyze."
        
        structure = analysis["directory_structure"]
        patterns = analysis.get("architecture_patterns", [])
        project_type = analysis.get("project_type", "Unknown")
        
        context = f"""## Existing Project Structure

Project Type: {project_type}
Architecture Patterns: {', '.join(patterns) if patterns else 'None identified'}

File Statistics:
- Code Files: {len(structure.get('code_files', []))}
- Test Files: {len(structure.get('test_files', []))}
- Configuration Files: {len(structure.get('config_files', []))}
- Documentation: {len(structure.get('documentation', []))}

Key Directories: {', '.join(structure.get('directories', [])[:10])}
"""
        return context
    
    async def _extract_technical_specifications(self, validated_dld: Dict[str, Any]) -> Dict[str, Any]:
        """Extract technical specifications from DLD"""
        specs = {
            "performance_requirements": [],
            "interface_specifications": [],
            "protocol_requirements": [],
            "hardware_constraints": []
        }
        
        sections = validated_dld.get("sections", [])
        
        for section in sections:
            content = section.get("content", "").lower()
            
            # Extract performance requirements
            perf_patterns = [
                r'(\d+\.?\d*)\s*(ms|millisecond)',  # Latency
                r'(\d+\.?\d*)\s*(mbps|gbps|kbps)',  # Throughput
                r'(\d+\.?\d*)\s*%.*reliability',    # Reliability
                r'(\d+\.?\d*)\s*(mhz|ghz)'          # Frequency
            ]
            
            for pattern in perf_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                specs["performance_requirements"].extend(matches)
            
            # Extract interface specifications
            if section.get("type") == "interfaces":
                specs["interface_specifications"].append(section.get("content", ""))
        
        return specs
    
    async def _classify_requirements(self, validated_dld: Dict[str, Any]) -> Dict[str, List[str]]:
        """Classify requirements by type"""
        classified = {
            "functional": [],
            "non_functional": [],
            "interface": [],
            "performance": [],
            "security": []
        }
        
        sections = validated_dld.get("sections", [])
        
        for section in sections:
            section_type = section.get("type", "general")
            content = section.get("content", "")
            
            if section_type == "requirements":
                # Simple classification based on keywords
                content_lower = content.lower()
                
                if any(word in content_lower for word in ["shall", "must", "implement", "provide"]):
                    classified["functional"].append(content)
                elif any(word in content_lower for word in ["performance", "latency", "throughput"]):
                    classified["performance"].append(content)
                elif any(word in content_lower for word in ["security", "authentication", "encryption"]):
                    classified["security"].append(content)
                elif any(word in content_lower for word in ["interface", "api", "protocol"]):
                    classified["interface"].append(content)
                else:
                    classified["non_functional"].append(content)
        
        return classified
    
    async def _convert_to_markdown(self, validated_dld: Dict[str, Any]) -> str:
        """Convert DLD to markdown format"""
        markdown_parts = []
        
        sections = validated_dld.get("sections", [])
        
        for section in sections:
            title = section.get("title", "Untitled")
            content = section.get("content", "")
            
            markdown_parts.append(f"## {title}")
            markdown_parts.append(content)
            markdown_parts.append("")
        
        return "\\n".join(markdown_parts)
    
    async def _identify_pseudocode(self, validated_dld: Dict[str, Any]) -> List[Dict[str, str]]:
        """Identify pseudocode sections in DLD"""
        pseudocode_sections = []
        
        sections = validated_dld.get("sections", [])
        
        for section in sections:
            content = section.get("content", "")
            
            # Look for pseudocode patterns
            pseudocode_patterns = [
                r'```\\w*\\n([^`]+)\\n```',  # Code blocks
                r'BEGIN\\s+(.+?)\\s+END',     # BEGIN/END blocks
                r'ALGORITHM\\s+(.+?)\\s+END', # Algorithm blocks
                r'PROCEDURE\\s+(.+?)\\s+END'  # Procedure blocks
            ]
            
            for pattern in pseudocode_patterns:
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    pseudocode_sections.append({
                        "section": section.get("title", ""),
                        "code": match.strip(),
                        "type": "pseudocode"
                    })
        
        return pseudocode_sections
    
    def _format_tech_specs(self, tech_specs: Dict[str, Any]) -> str:
        """Format technical specifications for prompt"""
        formatted = []
        
        for category, specs in tech_specs.items():
            if specs:
                formatted.append(f"### {category.replace('_', ' ').title()}")
                for spec in specs[:5]:  # Limit to first 5
                    formatted.append(f"- {spec}")
                formatted.append("")
        
        return "\\n".join(formatted)
    
    def _format_requirements(self, classified_requirements: Dict[str, List[str]]) -> str:
        """Format requirements for prompt"""
        formatted = []
        
        for req_type, requirements in classified_requirements.items():
            if requirements:
                formatted.append(f"### {req_type.replace('_', ' ').title()} Requirements")
                for req in requirements[:3]:  # Limit to first 3
                    # Truncate long requirements
                    truncated = req[:200] + "..." if len(req) > 200 else req
                    formatted.append(f"- {truncated}")
                formatted.append("")
        
        return "\\n".join(formatted)
    
    async def _load_5g_domain_knowledge(self) -> Dict[str, Any]:
        """Load 5G domain knowledge from knowledge base"""
        # This would interface with the knowledge manager
        return {
            "protocols": ["NR", "5GC", "NGAP", "NAS"],
            "network_functions": ["AMF", "SMF", "UPF"],
            "interfaces": ["N1", "N2", "N3", "N4"]
        }
    
    async def _load_coding_guidelines(self) -> Dict[str, Any]:
        """Load coding guidelines"""
        return {
            "style": "PEP8",
            "documentation": "Google style docstrings",
            "testing": "pytest framework"
        }
    
    async def _load_quality_standards(self) -> Dict[str, Any]:
        """Load quality standards"""
        return {
            "code_coverage": "minimum 80%",
            "complexity": "cyclomatic complexity < 10",
            "documentation": "all public functions documented"
        }
    
    async def _load_team_conventions(self) -> Dict[str, Any]:
        """Load team coding conventions"""
        return {
            "naming": "snake_case for functions, PascalCase for classes",
            "imports": "absolute imports preferred",
            "error_handling": "explicit exception handling required"
        }
    
    async def _load_project_rules(self) -> Dict[str, Any]:
        """Load project-specific rules"""
        return {
            "architecture": "clean architecture principles",
            "dependencies": "minimize external dependencies",
            "performance": "real-time constraints apply"
        }
    
    async def _load_ai_guidelines(self) -> Dict[str, Any]:
        """Load AI utilization guidelines"""
        return {
            "code_generation": "generate complete, testable functions",
            "documentation": "include usage examples",
            "optimization": "prioritize readability over cleverness"
        }
    
    def _format_conventions(self, conventions: Dict[str, Any]) -> str:
        """Format team conventions for prompt"""
        formatted = []
        
        for category, rule in conventions.items():
            formatted.append(f"- **{category.replace('_', ' ').title()}**: {rule}")
        
        return "\\n".join(formatted)
    
    async def _match_dld_to_code(self, validated_dld: Dict[str, Any], project_analysis: Dict[str, Any]) -> List[CodeMapping]:
        """Match DLD sections to existing code"""
        mappings = []
        
        sections = validated_dld.get("sections", [])
        code_files = project_analysis.get("directory_structure", {}).get("code_files", [])
        
        for section in sections:
            section_title = section.get("title", "").lower()
            section_content = section.get("content", "").lower()
            
            for code_file in code_files:
                # Simple matching based on filename similarity
                filename = Path(code_file).stem.lower()
                
                # Calculate similarity score
                similarity = self._calculate_text_similarity(
                    section_title + " " + section_content,
                    filename
                )
                
                if similarity > 0.3:  # Threshold for relevance
                    mappings.append(CodeMapping(
                        dld_section=section.get("title", ""),
                        code_file=code_file,
                        function_name="",  # Would be extracted from actual file analysis
                        confidence=similarity,
                        mapping_type="indirect"
                    ))
        
        return mappings
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    async def _analyze_function_mappings(self, validated_dld: Dict[str, Any], project_analysis: Dict[str, Any]) -> Dict[str, List[str]]:
        """Analyze function mappings between DLD and code"""
        return {"mapped_functions": [], "missing_functions": []}
    
    async def _analyze_module_structure(self, project_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze module structure"""
        return {"modules": [], "dependencies": {}}
    
    def _identify_missing_implementations(self, dld_code_matches: List[CodeMapping]) -> List[str]:
        """Identify missing implementations"""
        return ["feature_x", "feature_y"]  # Simplified
    
    def _format_code_mappings(self, mappings: List[CodeMapping]) -> str:
        """Format code mappings for prompt"""
        if not mappings:
            return "No existing code mappings found."
        
        formatted = []
        for mapping in mappings[:5]:  # Limit to first 5
            formatted.append(
                f"- **{mapping.dld_section}** → `{mapping.code_file}` "
                f"(confidence: {mapping.confidence:.2f})"
            )
        
        return "\\n".join(formatted)
    
    async def _analyze_code_patterns(self, project_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code patterns in the project"""
        return {"patterns": ["factory_pattern", "singleton_pattern"]}
    
    async def _extract_naming_conventions(self, project_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract naming conventions from code"""
        return {"functions": "snake_case", "classes": "PascalCase"}
    
    async def _identify_architecture_style(self, project_analysis: Dict[str, Any]) -> str:
        """Identify architecture style"""
        return "layered_architecture"
    
    async def _analyze_test_patterns(self, project_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze test patterns"""
        return {"framework": "pytest", "style": "AAA_pattern"}
    
    def _get_default_coding_style(self) -> Dict[str, Any]:
        """Get default coding style when no project is available"""
        return {
            "code_patterns": {"patterns": ["clean_code"]},
            "naming_conventions": {"functions": "snake_case", "classes": "PascalCase"},
            "architecture_style": "modular",
            "test_patterns": {"framework": "standard", "style": "unit_tests"}
        }
    
    def _format_coding_style(self) -> str:
        """Format coding style guidelines"""
        style = self.pipeline_state.get("coding_style", {})
        
        formatted = []
        
        naming = style.get("naming_conventions", {})
        if naming:
            formatted.append("### Naming Conventions")
            for item, convention in naming.items():
                formatted.append(f"- {item}: {convention}")
            formatted.append("")
        
        arch_style = style.get("architecture_style", "")
        if arch_style:
            formatted.append(f"### Architecture Style")
            formatted.append(f"- {arch_style}")
            formatted.append("")
        
        return "\\n".join(formatted)
    
    async def _enhance_5g_protocol_context(self) -> Dict[str, Any]:
        """Enhance context with 5G protocol knowledge"""
        return {
            "protocols": ["NR", "5GC"],
            "procedures": ["registration", "session_establishment"],
            "states": ["idle", "connected"]
        }
    
    async def _identify_hardware_constraints(self) -> List[str]:
        """Identify hardware constraints from DLD"""
        return ["real_time_processing", "memory_constraints", "power_efficiency"]
    
    async def _extract_performance_requirements(self) -> Dict[str, Any]:
        """Extract performance requirements"""
        return {
            "latency": "< 1ms",
            "throughput": "> 1Gbps",
            "reliability": "99.99%"
        }
    
    def _format_protocol_context(self, protocol_knowledge: Dict[str, Any]) -> str:
        """Format protocol context for prompt"""
        formatted = []
        
        for category, items in protocol_knowledge.items():
            formatted.append(f"### {category.title()}")
            for item in items:
                formatted.append(f"- {item}")
            formatted.append("")
        
        return "\\n".join(formatted)
    
    def _format_hardware_constraints(self, constraints: List[str]) -> str:
        """Format hardware constraints for prompt"""
        formatted = []
        
        for constraint in constraints:
            formatted.append(f"- {constraint.replace('_', ' ').title()}")
        
        return "\\n".join(formatted)
    
    def _generate_task_instruction(self) -> str:
        """Generate the specific task instruction"""
        validated_dld = self.pipeline_state["validated_dld"]
        
        # Extract key requirements for the task
        sections = validated_dld.get("sections", [])
        main_features = []
        
        for section in sections:
            if section.get("type") in ["requirements", "implementation"]:
                # Extract key features from section content
                content = section.get("content", "")
                # Simple feature extraction (would be more sophisticated in practice)
                features = re.findall(r'implement\\s+(\\w+)', content, re.IGNORECASE)
                main_features.extend(features)
        
        if not main_features:
            main_features = ["the specified functionality"]
        
        task = f"""
Based on the provided DLD specifications, implement {', '.join(main_features[:3])}.

Your implementation should:
1. Follow the technical specifications and requirements outlined above
2. Adhere to the coding style and conventions of the existing project
3. Include comprehensive error handling and logging
4. Provide clear documentation and comments
5. Consider the 5G domain constraints and performance requirements
6. Be compatible with the existing codebase architecture

Generate complete, production-ready code that can be directly integrated into the project.
"""
        
        return task.strip()
    
    async def _load_prompt_templates(self) -> None:
        """Load prompt templates from knowledge base"""
        self.logger.info("Loading prompt templates")
    
    async def _initialize_code_analyzers(self) -> None:
        """Initialize code analysis tools"""
        self.logger.info("Initializing code analyzers")
