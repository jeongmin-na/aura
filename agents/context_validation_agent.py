"""
Context Validation Agent - DLD verification and preprocessing
"""

import re
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import pandas as pd
from dataclasses import dataclass

from knowledge_base.knowledge_manager import KnowledgeManager
from utils.config import Config
from utils.logger import AgentLogger

@dataclass
class DLDSection:
    """Represents a section of the DLD document"""
    title: str
    content: str
    section_type: str  # requirements, architecture, interface, etc.
    confidence: float
    extracted_entities: List[str]

@dataclass
class ValidationResult:
    """Results of DLD validation"""
    is_valid: bool
    completeness_score: float
    consistency_score: float
    missing_sections: List[str]
    inconsistencies: List[str]
    extracted_sections: List[DLDSection]
    metadata: Dict[str, Any]

class ContextValidationAgent:
    """
    Agent responsible for DLD verification and preprocessing
    
    Functions:
    1. DLD Structure Analysis
    2. Missing Information Detection  
    3. Consistency Verification
    """
    
    def __init__(self, config: Config, knowledge_manager: KnowledgeManager):
        self.config = config
        self.knowledge_manager = knowledge_manager
        self.logger = AgentLogger("ContextValidationAgent")
        
        # Essential DLD sections for 5G base station design
        self.required_sections = {
            "system_overview": {
                "keywords": ["system", "overview", "architecture", "topology"],
                "weight": 0.2
            },
            "requirements": {
                "keywords": ["requirements", "specifications", "constraints"],
                "weight": 0.25
            },
            "interfaces": {
                "keywords": ["interface", "protocol", "api", "connectivity"],
                "weight": 0.2
            },
            "performance": {
                "keywords": ["performance", "kpi", "latency", "throughput", "capacity"],
                "weight": 0.15
            },
            "security": {
                "keywords": ["security", "authentication", "encryption", "access"],
                "weight": 0.1
            },
            "implementation": {
                "keywords": ["implementation", "deployment", "configuration"],
                "weight": 0.1
            }
        }
        
        # 5G specific entities to extract
        self.domain_entities = {
            "network_functions": ["AMF", "SMF", "UPF", "PCF", "AUSF", "UDM", "NRF", "NSSF"],
            "interfaces": ["N1", "N2", "N3", "N4", "N6", "N8", "N11", "N15", "N22", "Xn", "F1"],
            "protocols": ["NAS", "NGAP", "PFCP", "HTTP/2", "SBI", "SCTP", "GTP"],
            "frequency_bands": ["FR1", "FR2", "sub6", "mmWave", "n1", "n3", "n7", "n28", "n78"],
            "technologies": ["5G NR", "LTE", "NSA", "SA", "MIMO", "beamforming", "carrier aggregation"]
        }
    
    async def initialize(self) -> None:
        """Initialize the context validation agent"""
        self.logger.info("Initializing Context Validation Agent")
        
        # Load domain-specific validation rules
        await self._load_validation_rules()
        
        # Initialize NLP components if needed
        await self._initialize_nlp_components()
        
        self.logger.info("Context Validation Agent initialized successfully")
    
    async def shutdown(self) -> None:
        """Shutdown the agent gracefully"""
        self.logger.info("Shutting down Context Validation Agent")
    
    async def validate_dld(
        self, 
        dld_content: str, 
        project_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main validation method for DLD documents
        
        Args:
            dld_content: Raw DLD document content
            project_path: Optional path to existing project
            
        Returns:
            Validation results and processed DLD
        """
        self.logger.info("Starting DLD validation process")
        
        try:
            # Step 1: DLD Structure Analysis
            self.logger.push_context("Structure Analysis")
            structure_result = await self._analyze_dld_structure(dld_content)
            self.logger.pop_context()
            
            # Step 2: Missing Information Detection
            self.logger.push_context("Missing Information Detection")
            missing_info = await self._detect_missing_information(structure_result)
            self.logger.pop_context()
            
            # Step 3: Consistency Verification
            self.logger.push_context("Consistency Verification")
            consistency_result = await self._verify_consistency(structure_result)
            self.logger.pop_context()
            
            # Step 4: Project Context Analysis (if project path provided)
            project_context = {}
            if project_path:
                self.logger.push_context("Project Context Analysis")
                project_context = await self._analyze_project_context(project_path)
                self.logger.pop_context()
            
            # Compile validation results
            validation_result = ValidationResult(
                is_valid=self._calculate_overall_validity(structure_result, missing_info, consistency_result),
                completeness_score=self._calculate_completeness_score(structure_result, missing_info),
                consistency_score=consistency_result["consistency_score"],
                missing_sections=missing_info["missing_sections"],
                inconsistencies=consistency_result["inconsistencies"],
                extracted_sections=structure_result["sections"],
                metadata={
                    "total_sections": len(structure_result["sections"]),
                    "document_length": len(dld_content),
                    "domain_entities_found": structure_result["domain_entities"],
                    "project_context": project_context
                }
            )
            
            # Create processed DLD
            processed_dld = await self._create_processed_dld(dld_content, validation_result)
            
            self.logger.info(
                f"DLD validation completed - "
                f"Valid: {validation_result.is_valid}, "
                f"Completeness: {validation_result.completeness_score:.2f}, "
                f"Consistency: {validation_result.consistency_score:.2f}"
            )
            
            return {
                "success": validation_result.is_valid,
                "validation_result": validation_result,
                "validated_dld": processed_dld,
                "recommendations": await self._generate_recommendations(validation_result)
            }
            
        except Exception as e:
            self.logger.error(f"DLD validation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "validation_result": None,
                "validated_dld": None
            }
    
    async def _analyze_dld_structure(self, dld_content: str) -> Dict[str, Any]:
        """Analyze the structure of the DLD document"""
        self.logger.info("Analyzing DLD structure")
        
        # Extract sections using various methods
        sections = []
        
        # Method 1: Header-based section extraction
        header_sections = self._extract_sections_by_headers(dld_content)
        sections.extend(header_sections)
        
        # Method 2: Keyword-based section identification
        keyword_sections = self._extract_sections_by_keywords(dld_content)
        sections.extend(keyword_sections)
        
        # Method 3: Content-based section analysis
        content_sections = await self._extract_sections_by_content(dld_content)
        sections.extend(content_sections)
        
        # Merge and deduplicate sections
        merged_sections = self._merge_sections(sections)
        
        # Extract domain entities
        domain_entities = self._extract_domain_entities(dld_content)
        
        return {
            "sections": merged_sections,
            "domain_entities": domain_entities,
            "document_stats": {
                "total_length": len(dld_content),
                "sections_found": len(merged_sections),
                "entities_found": len(domain_entities)
            }
        }
    
    def _extract_sections_by_headers(self, content: str) -> List[DLDSection]:
        """Extract sections based on markdown/document headers"""
        sections = []
        
        # Common header patterns
        header_patterns = [
            r'^#+\s+(.+)$',  # Markdown headers
            r'^(\d+\.?\s+.+)$',  # Numbered sections
            r'^([A-Z][A-Z\s]+)$',  # All caps headers
            r'^(.+)\n[=-]+$'  # Underlined headers
        ]
        
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Check if line matches any header pattern
            is_header = False
            header_text = None
            
            for pattern in header_patterns:
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    header_text = match.group(1).strip()
                    is_header = True
                    break
            
            if is_header and header_text:
                # Save previous section
                if current_section and current_content:
                    sections.append(DLDSection(
                        title=current_section,
                        content='\n'.join(current_content),
                        section_type=self._classify_section_type(current_section, '\n'.join(current_content)),
                        confidence=0.8,
                        extracted_entities=self._extract_entities_from_text('\n'.join(current_content))
                    ))
                
                # Start new section
                current_section = header_text
                current_content = []
            else:
                if current_section:
                    current_content.append(line)
        
        # Don't forget the last section
        if current_section and current_content:
            sections.append(DLDSection(
                title=current_section,
                content='\n'.join(current_content),
                section_type=self._classify_section_type(current_section, '\n'.join(current_content)),
                confidence=0.8,
                extracted_entities=self._extract_entities_from_text('\n'.join(current_content))
            ))
        
        return sections
    
    def _extract_sections_by_keywords(self, content: str) -> List[DLDSection]:
        """Extract sections based on keyword patterns"""
        sections = []
        
        for section_name, section_info in self.required_sections.items():
            keywords = section_info["keywords"]
            
            # Find content related to these keywords
            keyword_pattern = r'(?i).*(?:' + '|'.join(keywords) + r').*'
            lines = content.split('\n')
            
            related_lines = []
            context_window = 3  # Lines before and after keyword match
            
            for i, line in enumerate(lines):
                if re.search(keyword_pattern, line):
                    # Include context
                    start_idx = max(0, i - context_window)
                    end_idx = min(len(lines), i + context_window + 1)
                    related_lines.extend(lines[start_idx:end_idx])
            
            if related_lines:
                content_text = '\n'.join(related_lines)
                sections.append(DLDSection(
                    title=f"Extracted {section_name.replace('_', ' ').title()}",
                    content=content_text,
                    section_type=section_name,
                    confidence=0.6,
                    extracted_entities=self._extract_entities_from_text(content_text)
                ))
        
        return sections
    
    async def _extract_sections_by_content(self, content: str) -> List[DLDSection]:
        """Extract sections using content analysis and NLP"""
        sections = []
        
        # Split content into logical chunks
        chunks = self._split_content_into_chunks(content)
        
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 50:  # Skip very short chunks
                continue
            
            # Classify chunk type
            section_type = self._classify_section_type("", chunk)
            
            # Extract title from chunk
            title = self._extract_chunk_title(chunk) or f"Section {i+1}"
            
            sections.append(DLDSection(
                title=title,
                content=chunk,
                section_type=section_type,
                confidence=0.4,
                extracted_entities=self._extract_entities_from_text(chunk)
            ))
        
        return sections
    
    def _classify_section_type(self, title: str, content: str) -> str:
        """Classify the type of a section based on title and content"""
        text_to_analyze = (title + " " + content).lower()
        
        section_scores = {}
        
        for section_name, section_info in self.required_sections.items():
            score = 0
            for keyword in section_info["keywords"]:
                score += text_to_analyze.count(keyword.lower())
            section_scores[section_name] = score
        
        # Return the section type with highest score
        if section_scores:
            best_section = max(section_scores.items(), key=lambda x: x[1])
            if best_section[1] > 0:
                return best_section[0]
        
        return "general"
    
    def _extract_domain_entities(self, content: str) -> Dict[str, List[str]]:
        """Extract 5G domain-specific entities from content"""
        found_entities = {}
        content_lower = content.lower()
        
        for entity_type, entities in self.domain_entities.items():
            found = []
            for entity in entities:
                # Case-insensitive search with word boundaries
                pattern = r'\b' + re.escape(entity.lower()) + r'\b'
                if re.search(pattern, content_lower):
                    found.append(entity)
            
            if found:
                found_entities[entity_type] = found
        
        return found_entities
    
    def _extract_entities_from_text(self, text: str) -> List[str]:
        """Extract general entities from text"""
        entities = []
        
        # Simple entity extraction patterns
        patterns = [
            r'\b[A-Z][A-Z0-9]{2,}\b',  # Acronyms
            r'\b\d+\.?\d*\s*(?:MHz|GHz|Mbps|Gbps|ms|dB|dBm)\b',  # Technical values
            r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b'  # CamelCase terms
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            entities.extend(matches)
        
        return list(set(entities))  # Remove duplicates
    
    async def _detect_missing_information(self, structure_result: Dict[str, Any]) -> Dict[str, Any]:
        """Detect missing information in the DLD"""
        self.logger.info("Detecting missing information")
        
        found_sections = {section.section_type for section in structure_result["sections"]}
        required_sections = set(self.required_sections.keys())
        
        missing_sections = list(required_sections - found_sections)
        
        # Calculate missing information score
        missing_weight = sum(
            self.required_sections[section]["weight"] 
            for section in missing_sections
        )
        
        return {
            "missing_sections": missing_sections,
            "missing_weight": missing_weight,
            "coverage_score": 1.0 - missing_weight
        }
    
    async def _verify_consistency(self, structure_result: Dict[str, Any]) -> Dict[str, Any]:
        """Verify consistency within the DLD"""
        self.logger.info("Verifying consistency")
        
        inconsistencies = []
        sections = structure_result["sections"]
        
        # Check for conflicting information
        # This is a simplified implementation - in practice, you'd use more sophisticated NLP
        
        # Example: Check for conflicting frequency band mentions
        frequency_mentions = {}
        for section in sections:
            content_lower = section.content.lower()
            for band in self.domain_entities["frequency_bands"]:
                if band.lower() in content_lower:
                    frequency_mentions[band] = frequency_mentions.get(band, 0) + 1
        
        # Check for contradictory statements (simplified)
        contradiction_patterns = [
            (r'(?i)not supported', r'(?i)supported'),
            (r'(?i)mandatory', r'(?i)optional'),
            (r'(?i)synchronous', r'(?i)asynchronous')
        ]
        
        for section in sections:
            for pattern1, pattern2 in contradiction_patterns:
                if re.search(pattern1, section.content) and re.search(pattern2, section.content):
                    inconsistencies.append(f"Potential contradiction in section '{section.title}'")
        
        consistency_score = max(0.0, 1.0 - (len(inconsistencies) * 0.1))
        
        return {
            "inconsistencies": inconsistencies,
            "consistency_score": consistency_score,
            "frequency_analysis": frequency_mentions
        }
    
    async def _analyze_project_context(self, project_path: str) -> Dict[str, Any]:
        """Analyze existing project context if provided"""
        self.logger.info(f"Analyzing project context at {project_path}")
        
        project_dir = Path(project_path)
        if not project_dir.exists():
            return {"error": "Project path does not exist"}
        
        context = {
            "project_structure": [],
            "code_files": [],
            "config_files": [],
            "documentation": []
        }
        
        try:
            # Scan project structure
            for item in project_dir.rglob("*"):
                if item.is_file():
                    rel_path = str(item.relative_to(project_dir))
                    
                    if item.suffix in ['.py', '.js', '.ts', '.cpp', '.c', '.java']:
                        context["code_files"].append(rel_path)
                    elif item.suffix in ['.yaml', '.yml', '.json', '.ini', '.conf']:
                        context["config_files"].append(rel_path)
                    elif item.suffix in ['.md', '.txt', '.rst']:
                        context["documentation"].append(rel_path)
                    
                    context["project_structure"].append(rel_path)
        
        except Exception as e:
            context["error"] = str(e)
        
        return context
    
    def _merge_sections(self, sections: List[DLDSection]) -> List[DLDSection]:
        """Merge and deduplicate similar sections"""
        # Simple implementation - group by section type and merge similar content
        merged = {}
        
        for section in sections:
            key = section.section_type
            if key in merged:
                # Merge content if sections are similar
                existing = merged[key]
                if self._calculate_content_similarity(existing.content, section.content) > 0.7:
                    # Merge the sections
                    merged[key] = DLDSection(
                        title=existing.title if len(existing.title) > len(section.title) else section.title,
                        content=existing.content + "\n\n" + section.content,
                        section_type=key,
                        confidence=max(existing.confidence, section.confidence),
                        extracted_entities=list(set(existing.extracted_entities + section.extracted_entities))
                    )
                else:
                    # Keep as separate section with modified title
                    new_title = f"{section.title} (Alternative)"
                    merged[f"{key}_alt"] = section._replace(title=new_title)
            else:
                merged[key] = section
        
        return list(merged.values())
    
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two content strings"""
        # Simple word-based similarity
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _split_content_into_chunks(self, content: str, chunk_size: int = 1000) -> List[str]:
        """Split content into logical chunks"""
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) < chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _extract_chunk_title(self, chunk: str) -> Optional[str]:
        """Extract a title from a content chunk"""
        lines = chunk.split('\n')
        
        # Look for the first substantial line as title
        for line in lines:
            line = line.strip()
            if len(line) > 10 and len(line) < 100:
                # Remove common prefixes/suffixes
                cleaned = re.sub(r'^\d+\.?\s*', '', line)  # Remove numbering
                cleaned = re.sub(r'^[#*-]+\s*', '', cleaned)  # Remove markdown
                if len(cleaned) > 5:
                    return cleaned
        
        return None
    
    def _calculate_overall_validity(
        self, 
        structure_result: Dict[str, Any], 
        missing_info: Dict[str, Any], 
        consistency_result: Dict[str, Any]
    ) -> bool:
        """Calculate overall validity of the DLD"""
        # DLD is valid if:
        # 1. At least 70% of required sections are present
        # 2. Consistency score is above 0.7
        # 3. At least some domain entities are found
        
        coverage_score = missing_info["coverage_score"]
        consistency_score = consistency_result["consistency_score"]
        has_domain_entities = len(structure_result["domain_entities"]) > 0
        
        return (
            coverage_score >= 0.7 and
            consistency_score >= 0.7 and
            has_domain_entities
        )
    
    def _calculate_completeness_score(
        self, 
        structure_result: Dict[str, Any], 
        missing_info: Dict[str, Any]
    ) -> float:
        """Calculate completeness score"""
        # Base score from coverage
        base_score = missing_info["coverage_score"]
        
        # Bonus for domain entities
        entity_bonus = min(0.1, len(structure_result["domain_entities"]) * 0.02)
        
        # Bonus for number of sections
        section_bonus = min(0.1, len(structure_result["sections"]) * 0.01)
        
        return min(1.0, base_score + entity_bonus + section_bonus)
    
    async def _create_processed_dld(self, original_content: str, validation_result: ValidationResult) -> Dict[str, Any]:
        """Create processed and enhanced DLD"""
        return {
            "original_content": original_content,
            "sections": [
                {
                    "title": section.title,
                    "content": section.content,
                    "type": section.section_type,
                    "confidence": section.confidence,
                    "entities": section.extracted_entities
                }
                for section in validation_result.extracted_sections
            ],
            "metadata": validation_result.metadata,
            "validation_summary": {
                "completeness_score": validation_result.completeness_score,
                "consistency_score": validation_result.consistency_score,
                "missing_sections": validation_result.missing_sections,
                "inconsistencies": validation_result.inconsistencies
            }
        }
    
    async def _generate_recommendations(self, validation_result: ValidationResult) -> List[str]:
        """Generate recommendations for improving the DLD"""
        recommendations = []
        
        if validation_result.missing_sections:
            recommendations.append(
                f"Add missing sections: {', '.join(validation_result.missing_sections)}"
            )
        
        if validation_result.completeness_score < 0.8:
            recommendations.append(
                "Consider adding more detailed technical specifications"
            )
        
        if validation_result.consistency_score < 0.8:
            recommendations.append(
                "Review and resolve potential inconsistencies in the document"
            )
        
        if len(validation_result.extracted_sections) < 5:
            recommendations.append(
                "Consider structuring the document with clearer section headers"
            )
        
        return recommendations
    
    async def _load_validation_rules(self) -> None:
        """Load domain-specific validation rules"""
        # This would load rules from the knowledge base
        self.logger.info("Loading validation rules from knowledge base")
    
    async def _initialize_nlp_components(self) -> None:
        """Initialize NLP components for text analysis"""
        # This would initialize any NLP libraries if needed
        self.logger.info("Initializing NLP components")
