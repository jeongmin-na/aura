"""
Code Quality Assurance Agent - Validates prompt quality and technical accuracy
"""

import asyncio
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from knowledge_base.knowledge_manager import KnowledgeManager
from utils.config import Config
from utils.logger import AgentLogger

class QualityMetric(Enum):
    """Quality metrics for prompt assessment"""
    COMPLETENESS = "completeness"
    TECHNICAL_ACCURACY = "technical_accuracy"
    CURSOR_AI_COMPATIBILITY = "cursor_ai_compatibility"
    CLARITY = "clarity"
    SPECIFICITY = "specificity"
    ACTIONABILITY = "actionability"

@dataclass
class QualityAssessment:
    """Quality assessment result"""
    metric: QualityMetric
    score: float
    details: str
    suggestions: List[str]

@dataclass
class ValidationResult:
    """Overall validation result"""
    overall_score: float
    assessments: List[QualityAssessment]
    is_valid: bool
    critical_issues: List[str]
    improvement_suggestions: List[str]

class CodeQualityAgent:
    """
    Agent responsible for prompt quality verification and technical accuracy validation
    
    Functions:
    1. Prompt Completeness Verification
    2. Technical Accuracy Confirmation
    3. Cursor AI Compatibility Verification
    """
    
    def __init__(self, config: Config, knowledge_manager: KnowledgeManager):
        self.config = config
        self.knowledge_manager = knowledge_manager
        self.logger = AgentLogger("CodeQualityAgent")
        
        # Quality thresholds from config
        self.quality_thresholds = config.quality_thresholds
        
        # 5G domain validation patterns
        self.domain_patterns = {
            "5g_keywords": [
                "gNodeB", "5G NR", "5GC", "AMF", "SMF", "UPF", "NGAP", "NAS",
                "RRC", "PDCP", "RLC", "MAC", "PHY", "beamforming", "MIMO",
                "carrier aggregation", "network slicing", "latency", "URLLC"
            ],
            "protocol_patterns": [
                r"\b(?:N[1-9]\d?|Xn|F1|E1|NG|S1|X2)\b",  # Interface names
                r"\b(?:NGAP|NAS|RRC|PDCP|RLC|GTP|SCTP)\b",  # Protocol names
                r"\b(?:FR1|FR2|sub-?6|mmWave)\b",           # Frequency ranges
                r"\b(?:NSA|SA|EN-DC)\b"                     # Architecture modes
            ],
            "technical_units": [
                r"\d+\.?\d*\s*(?:MHz|GHz|kHz)",             # Frequency
                r"\d+\.?\d*\s*(?:Mbps|Gbps|kbps)",          # Bandwidth
                r"\d+\.?\d*\s*(?:ms|μs|ns)",                # Latency
                r"\d+\.?\d*\s*(?:dB|dBm|dBi)",              # Power/gain
                r"\d+\.?\d*\s*(?:%|percent)"                # Percentages
            ]
        }
        
        # Cursor AI compatibility patterns
        self.cursor_ai_patterns = {
            "good_practices": [
                r"implement\s+\w+",                         # Clear implementation tasks
                r"create\s+(?:function|class|module)",      # Specific creation requests
                r"following\s+(?:pattern|convention)",      # Pattern adherence
                r"with\s+(?:error handling|logging)",       # Best practices
                r"test\s+(?:coverage|cases)"                # Testing requirements
            ],
            "problematic_patterns": [
                r"just\s+(?:write|create|make)",            # Vague instructions
                r"somehow\s+(?:implement|handle)",          # Unclear requirements
                r"(?:quick|simple|easy)\s+(?:fix|solution)", # Oversimplified requests
                r"without\s+(?:any|much)\s+(?:documentation|comments)" # Poor practices
            ],
            "required_elements": [
                "context",       # System/domain context
                "requirements",  # Clear requirements
                "constraints",   # Technical constraints
                "examples"       # Usage examples (optional but recommended)
            ]
        }
        
        # Technical accuracy validators
        self.technical_validators = {}
    
    async def initialize(self) -> None:
        """Initialize the code quality agent"""
        self.logger.info("Initializing Code Quality Assurance Agent")
        
        # Load validation rules from knowledge base
        await self._load_validation_rules()
        
        # Initialize technical validators
        await self._initialize_technical_validators()
        
        self.logger.info("Code Quality Assurance Agent initialized successfully")
    
    async def shutdown(self) -> None:
        """Shutdown the agent gracefully"""
        self.logger.info("Shutting down Code Quality Assurance Agent")
    
    async def validate_prompt(
        self,
        generated_prompt: str,
        dld_context: Dict[str, Any],
        quality_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """
        Main validation method for generated prompts
        
        Args:
            generated_prompt: The generated prompt to validate
            dld_context: Context from the original DLD
            quality_threshold: Minimum quality threshold
            
        Returns:
            Validation results and quality metrics
        """
        self.logger.info("Starting prompt quality validation")
        
        try:
            # Step 1: Prompt Completeness Verification
            self.logger.push_context("Completeness Verification")
            completeness_assessment = await self._verify_prompt_completeness(
                generated_prompt, dld_context
            )
            self.logger.pop_context()
            
            # Step 2: Technical Accuracy Confirmation
            self.logger.push_context("Technical Accuracy")
            accuracy_assessment = await self._confirm_technical_accuracy(
                generated_prompt, dld_context
            )
            self.logger.pop_context()
            
            # Step 3: Cursor AI Compatibility Verification
            self.logger.push_context("Cursor AI Compatibility")
            compatibility_assessment = await self._verify_cursor_ai_compatibility(
                generated_prompt
            )
            self.logger.pop_context()
            
            # Additional quality checks
            clarity_assessment = await self._assess_clarity(generated_prompt)
            specificity_assessment = await self._assess_specificity(generated_prompt)
            actionability_assessment = await self._assess_actionability(generated_prompt)
            
            # Compile all assessments
            all_assessments = [
                completeness_assessment,
                accuracy_assessment,
                compatibility_assessment,
                clarity_assessment,
                specificity_assessment,
                actionability_assessment
            ]
            
            # Calculate overall quality score
            overall_score = self._calculate_overall_score(all_assessments)
            
            # Determine validation result
            validation_result = ValidationResult(
                overall_score=overall_score,
                assessments=all_assessments,
                is_valid=overall_score >= quality_threshold,
                critical_issues=self._identify_critical_issues(all_assessments),
                improvement_suggestions=self._generate_improvement_suggestions(all_assessments)
            )
            
            self.logger.info(
                f"Prompt validation completed - "
                f"Score: {overall_score:.2f}, "
                f"Valid: {validation_result.is_valid}"
            )
            
            return {
                "success": True,
                "quality_score": overall_score,
                "validation_result": validation_result,
                "detailed_scores": {
                    assessment.metric.value: assessment.score 
                    for assessment in all_assessments
                },
                "recommendations": validation_result.improvement_suggestions
            }
            
        except Exception as e:
            self.logger.error(f"Prompt validation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "quality_score": 0.0,
                "validation_result": None
            }
    
    async def _verify_prompt_completeness(
        self, 
        prompt: str, 
        dld_context: Dict[str, Any]
    ) -> QualityAssessment:
        """Verify that the prompt is complete and comprehensive"""
        self.logger.info("Verifying prompt completeness")
        
        score = 0.0
        details = []
        suggestions = []
        
        # Check for essential sections
        required_sections = ["context", "requirements", "constraints", "task"]
        found_sections = []
        
        for section in required_sections:
            if self._has_section(prompt, section):
                found_sections.append(section)
                score += 0.2
        
        details.append(f"Found sections: {', '.join(found_sections)}")
        
        # Check coverage of DLD requirements
        dld_sections = dld_context.get("sections", [])
        covered_requirements = 0
        total_requirements = len(dld_sections)
        
        if total_requirements > 0:
            for section in dld_sections:
                section_title = section.get("title", "").lower()
                section_content = section.get("content", "").lower()
                
                # Check if prompt addresses this section
                if self._prompt_addresses_section(prompt, section_title, section_content):
                    covered_requirements += 1
            
            coverage_ratio = covered_requirements / total_requirements
            score += coverage_ratio * 0.4  # 40% weight for requirement coverage
            
            details.append(f"Requirement coverage: {covered_requirements}/{total_requirements} ({coverage_ratio:.2%})")
        
        # Check for 5G domain specificity
        domain_coverage = self._assess_domain_coverage(prompt)
        score += domain_coverage * 0.2  # 20% weight for domain coverage
        
        details.append(f"5G domain coverage: {domain_coverage:.2%}")
        
        # Generate suggestions
        missing_sections = set(required_sections) - set(found_sections)
        if missing_sections:
            suggestions.append(f"Add missing sections: {', '.join(missing_sections)}")
        
        if coverage_ratio < 0.8:
            suggestions.append("Increase coverage of DLD requirements")
        
        if domain_coverage < 0.6:
            suggestions.append("Include more 5G-specific technical details")
        
        return QualityAssessment(
            metric=QualityMetric.COMPLETENESS,
            score=min(score, 1.0),
            details="; ".join(details),
            suggestions=suggestions
        )
    
    async def _confirm_technical_accuracy(
        self, 
        prompt: str, 
        dld_context: Dict[str, Any]
    ) -> QualityAssessment:
        """Confirm technical accuracy of the prompt"""
        self.logger.info("Confirming technical accuracy")
        
        score = 0.8  # Start with high base score
        details = []
        suggestions = []
        issues_found = []
        
        # Check for correct 5G terminology
        terminology_score = await self._validate_5g_terminology(prompt)
        score = score * terminology_score
        details.append(f"5G terminology accuracy: {terminology_score:.2%}")
        
        # Check for technical consistency
        consistency_issues = await self._check_technical_consistency(prompt, dld_context)
        if consistency_issues:
            score *= 0.8  # Reduce score for consistency issues
            issues_found.extend(consistency_issues)
            details.append(f"Consistency issues found: {len(consistency_issues)}")
        
        # Validate technical specifications
        spec_validation = await self._validate_technical_specifications(prompt)
        score *= spec_validation["accuracy_score"]
        details.append(f"Technical specification accuracy: {spec_validation['accuracy_score']:.2%}")
        
        if spec_validation["issues"]:
            issues_found.extend(spec_validation["issues"])
        
        # Check for realistic performance requirements
        perf_validation = await self._validate_performance_requirements(prompt)
        score *= perf_validation["realism_score"]
        details.append(f"Performance requirement realism: {perf_validation['realism_score']:.2%}")
        
        # Generate suggestions
        if terminology_score < 0.9:
            suggestions.append("Review and correct 5G technical terminology")
        
        if consistency_issues:
            suggestions.append("Resolve technical consistency issues")
        
        if issues_found:
            suggestions.append("Address technical specification issues")
        
        return QualityAssessment(
            metric=QualityMetric.TECHNICAL_ACCURACY,
            score=score,
            details="; ".join(details),
            suggestions=suggestions
        )
    
    async def _verify_cursor_ai_compatibility(self, prompt: str) -> QualityAssessment:
        """Verify compatibility with Cursor AI"""
        self.logger.info("Verifying Cursor AI compatibility")
        
        score = 0.0
        details = []
        suggestions = []
        
        # Check for good practices
        good_practices_found = 0
        for pattern in self.cursor_ai_patterns["good_practices"]:
            if re.search(pattern, prompt, re.IGNORECASE):
                good_practices_found += 1
        
        practice_score = min(good_practices_found / len(self.cursor_ai_patterns["good_practices"]), 1.0)
        score += practice_score * 0.4
        details.append(f"Good practices found: {good_practices_found}")
        
        # Check for problematic patterns
        problematic_patterns_found = 0
        for pattern in self.cursor_ai_patterns["problematic_patterns"]:
            if re.search(pattern, prompt, re.IGNORECASE):
                problematic_patterns_found += 1
        
        if problematic_patterns_found > 0:
            score *= 0.7  # Penalty for problematic patterns
            details.append(f"Problematic patterns found: {problematic_patterns_found}")
            suggestions.append("Remove vague or problematic instruction patterns")
        
        # Check prompt structure
        structure_score = self._assess_prompt_structure(prompt)
        score += structure_score * 0.3
        details.append(f"Structure score: {structure_score:.2%}")
        
        # Check for clear actionable instructions
        actionable_score = self._assess_actionable_instructions(prompt)
        score += actionable_score * 0.3
        details.append(f"Actionable instructions: {actionable_score:.2%}")
        
        # Generate suggestions
        if practice_score < 0.7:
            suggestions.append("Include more Cursor AI best practices")
        
        if structure_score < 0.8:
            suggestions.append("Improve prompt structure and organization")
        
        if actionable_score < 0.8:
            suggestions.append("Make instructions more specific and actionable")
        
        return QualityAssessment(
            metric=QualityMetric.CURSOR_AI_COMPATIBILITY,
            score=score,
            details="; ".join(details),
            suggestions=suggestions
        )
    
    async def _assess_clarity(self, prompt: str) -> QualityAssessment:
        """Assess clarity of the prompt"""
        score = 0.8  # Base score
        details = []
        suggestions = []
        
        # Check sentence length (avoid overly long sentences)
        sentences = re.split(r'[.!?]+', prompt)
        long_sentences = [s for s in sentences if len(s.split()) > 30]
        
        if long_sentences:
            score *= 0.9
            details.append(f"Long sentences found: {len(long_sentences)}")
            suggestions.append("Break down long sentences for better clarity")
        
        # Check for clear headings and structure
        headings = re.findall(r'^#+\s+(.+)$', prompt, re.MULTILINE)
        if len(headings) >= 3:
            score += 0.1
            details.append(f"Clear headings found: {len(headings)}")
        else:
            suggestions.append("Add more clear section headings")
        
        # Check for jargon explanation
        jargon_count = len(re.findall(r'\b[A-Z]{2,}\b', prompt))  # Acronyms
        if jargon_count > 10:
            score *= 0.95
            details.append(f"Technical acronyms: {jargon_count}")
            suggestions.append("Consider explaining technical acronyms")
        
        return QualityAssessment(
            metric=QualityMetric.CLARITY,
            score=score,
            details="; ".join(details),
            suggestions=suggestions
        )
    
    async def _assess_specificity(self, prompt: str) -> QualityAssessment:
        """Assess specificity of the prompt"""
        score = 0.0
        details = []
        suggestions = []
        
        # Check for specific technical details
        technical_details = 0
        for pattern_list in self.domain_patterns.values():
            for pattern in pattern_list:
                if isinstance(pattern, str):
                    technical_details += len(re.findall(pattern, prompt, re.IGNORECASE))
                else:
                    technical_details += len(re.findall(pattern, prompt))
        
        specificity_score = min(technical_details / 20, 1.0)  # Normalize to 20 expected details
        score += specificity_score * 0.5
        details.append(f"Technical details found: {technical_details}")
        
        # Check for specific implementation guidance
        implementation_keywords = ["function", "class", "method", "variable", "parameter", "return"]
        impl_guidance = sum(1 for keyword in implementation_keywords if keyword in prompt.lower())
        
        guidance_score = min(impl_guidance / len(implementation_keywords), 1.0)
        score += guidance_score * 0.3
        details.append(f"Implementation guidance: {impl_guidance}")
        
        # Check for examples
        examples_found = len(re.findall(r'example|for instance|such as', prompt, re.IGNORECASE))
        example_score = min(examples_found / 3, 1.0)
        score += example_score * 0.2
        details.append(f"Examples provided: {examples_found}")
        
        # Generate suggestions
        if specificity_score < 0.6:
            suggestions.append("Include more specific technical details")
        
        if guidance_score < 0.5:
            suggestions.append("Provide more specific implementation guidance")
        
        if example_score < 0.3:
            suggestions.append("Add concrete examples to illustrate requirements")
        
        return QualityAssessment(
            metric=QualityMetric.SPECIFICITY,
            score=score,
            details="; ".join(details),
            suggestions=suggestions
        )
    
    async def _assess_actionability(self, prompt: str) -> QualityAssessment:
        """Assess how actionable the prompt is"""
        score = 0.0
        details = []
        suggestions = []
        
        # Check for action verbs
        action_verbs = [
            "implement", "create", "develop", "build", "design", "write",
            "generate", "construct", "establish", "define", "configure"
        ]
        
        actions_found = sum(1 for verb in action_verbs if verb in prompt.lower())
        action_score = min(actions_found / 5, 1.0)
        score += action_score * 0.4
        details.append(f"Action verbs found: {actions_found}")
        
        # Check for clear deliverables
        deliverable_patterns = [
            r'(?:create|implement|build)\s+(?:a|an)\s+\w+',
            r'(?:function|class|module|component)\s+(?:that|which)',
            r'(?:should|must|will)\s+(?:return|provide|handle)'
        ]
        
        deliverables = sum(1 for pattern in deliverable_patterns 
                         if re.search(pattern, prompt, re.IGNORECASE))
        deliverable_score = min(deliverables / 3, 1.0)
        score += deliverable_score * 0.3
        details.append(f"Clear deliverables: {deliverables}")
        
        # Check for step-by-step instructions
        steps = len(re.findall(r'(?:^|\n)\s*\d+\.', prompt))
        step_score = min(steps / 5, 1.0)
        score += step_score * 0.3
        details.append(f"Numbered steps: {steps}")
        
        # Generate suggestions
        if action_score < 0.6:
            suggestions.append("Include more specific action verbs")
        
        if deliverable_score < 0.5:
            suggestions.append("Define clearer deliverables and outcomes")
        
        if step_score < 0.4:
            suggestions.append("Break down complex tasks into numbered steps")
        
        return QualityAssessment(
            metric=QualityMetric.ACTIONABILITY,
            score=score,
            details="; ".join(details),
            suggestions=suggestions
        )
    
    # Helper methods
    
    def _has_section(self, prompt: str, section_name: str) -> bool:
        """Check if prompt has a specific section"""
        patterns = [
            f'#{1,6}\\s*{section_name}',  # Markdown headers
            f'\\b{section_name}\\b.*:',   # Colon-separated sections
            f'^{section_name.upper()}',   # All-caps headers
        ]
        
        for pattern in patterns:
            if re.search(pattern, prompt, re.IGNORECASE | re.MULTILINE):
                return True
        
        return False
    
    def _prompt_addresses_section(self, prompt: str, section_title: str, section_content: str) -> bool:
        """Check if prompt addresses a specific DLD section"""
        # Simple keyword matching approach
        keywords = section_title.split() + section_content.split()[:10]  # First 10 words
        keywords = [word.lower() for word in keywords if len(word) > 3]
        
        prompt_lower = prompt.lower()
        matches = sum(1 for keyword in keywords if keyword in prompt_lower)
        
        return matches >= max(2, len(keywords) * 0.3)  # At least 30% keyword overlap
    
    def _assess_domain_coverage(self, prompt: str) -> float:
        """Assess 5G domain coverage in the prompt"""
        total_score = 0.0
        weights = {"5g_keywords": 0.4, "protocol_patterns": 0.3, "technical_units": 0.3}
        
        for category, patterns in self.domain_patterns.items():
            found_count = 0
            
            for pattern in patterns:
                if isinstance(pattern, str):
                    found_count += len(re.findall(pattern, prompt, re.IGNORECASE))
                else:
                    found_count += len(re.findall(pattern, prompt))
            
            # Normalize score for this category
            expected_count = len(patterns) * 2  # Expect each pattern to appear ~2 times
            category_score = min(found_count / expected_count, 1.0)
            total_score += category_score * weights[category]
        
        return total_score
    
    async def _validate_5g_terminology(self, prompt: str) -> float:
        """Validate 5G terminology usage"""
        correct_usage = 0.0
        total_terms = 0
        
        # Check for correct acronym usage
        acronyms_found = re.findall(r'\b[A-Z]{2,}\b', prompt)
        valid_5g_acronyms = set(self.domain_patterns["5g_keywords"])
        
        for acronym in acronyms_found:
            total_terms += 1
            if acronym in valid_5g_acronyms or acronym.lower() in [term.lower() for term in valid_5g_acronyms]:
                correct_usage += 1
        
        if total_terms == 0:
            return 0.5  # Neutral score if no terms found
        
        return correct_usage / total_terms
    
    async def _check_technical_consistency(self, prompt: str, dld_context: Dict[str, Any]) -> List[str]:
        """Check for technical inconsistencies"""
        issues = []
        
        # Check for conflicting frequency bands
        frequency_mentions = re.findall(r'\b(?:FR1|FR2|sub-?6|mmWave)\b', prompt, re.IGNORECASE)
        if "FR1" in frequency_mentions and "mmWave" in frequency_mentions:
            issues.append("Conflicting frequency band mentions (FR1 and mmWave)")
        
        # Check for unrealistic performance claims
        latency_values = re.findall(r'(\d+\.?\d*)\s*(?:ms|millisecond)', prompt, re.IGNORECASE)
        for value in latency_values:
            if float(value) < 0.1:  # Sub-millisecond claims might be unrealistic
                issues.append(f"Potentially unrealistic latency claim: {value}ms")
        
        return issues
    
    async def _validate_technical_specifications(self, prompt: str) -> Dict[str, Any]:
        """Validate technical specifications in the prompt"""
        accuracy_score = 1.0
        issues = []
        
        # Check bandwidth specifications
        bandwidth_values = re.findall(r'(\d+\.?\d*)\s*(?:Mbps|Gbps)', prompt, re.IGNORECASE)
        for value_str in bandwidth_values:
            value = float(value_str)
            if "Gbps" in prompt and value > 100:  # Very high bandwidth claims
                accuracy_score *= 0.9
                issues.append(f"Very high bandwidth claim: {value}Gbps")
        
        # Check frequency specifications
        freq_values = re.findall(r'(\d+\.?\d*)\s*(?:MHz|GHz)', prompt, re.IGNORECASE)
        for value_str in freq_values:
            value = float(value_str)
            if "GHz" in prompt and value > 100:  # Very high frequency
                accuracy_score *= 0.9
                issues.append(f"Very high frequency claim: {value}GHz")
        
        return {
            "accuracy_score": accuracy_score,
            "issues": issues
        }
    
    async def _validate_performance_requirements(self, prompt: str) -> Dict[str, Any]:
        """Validate performance requirements for realism"""
        realism_score = 1.0
        
        # Check latency requirements
        latency_requirements = re.findall(r'(?:latency|delay).*?(\d+\.?\d*)\s*(?:ms|μs)', prompt, re.IGNORECASE)
        for latency in latency_requirements:
            if float(latency) < 0.1:  # Very low latency
                realism_score *= 0.8
        
        # Check reliability requirements
        reliability_requirements = re.findall(r'reliability.*?(\d+\.?\d*)\s*%', prompt, re.IGNORECASE)
        for reliability in reliability_requirements:
            if float(reliability) > 99.999:  # Very high reliability
                realism_score *= 0.9
        
        return {
            "realism_score": realism_score
        }
    
    def _assess_prompt_structure(self, prompt: str) -> float:
        """Assess the structural quality of the prompt"""
        score = 0.0
        
        # Check for clear sections
        sections = len(re.findall(r'^#+\s+', prompt, re.MULTILINE))
        if sections >= 3:
            score += 0.3
        
        # Check for lists and bullet points
        lists = len(re.findall(r'^\s*[-*]\s+', prompt, re.MULTILINE))
        if lists >= 3:
            score += 0.2
        
        # Check for code blocks or examples
        code_blocks = len(re.findall(r'```|`[^`]+`', prompt))
        if code_blocks >= 1:
            score += 0.2
        
        # Check for logical flow (consecutive numbered items)
        numbered_items = len(re.findall(r'^\s*\d+\.', prompt, re.MULTILINE))
        if numbered_items >= 3:
            score += 0.3
        
        return min(score, 1.0)
    
    def _assess_actionable_instructions(self, prompt: str) -> float:
        """Assess how actionable the instructions are"""
        score = 0.0
        
        # Look for imperative verbs
        imperative_verbs = ["create", "implement", "build", "design", "develop", "write", "generate"]
        verb_count = sum(1 for verb in imperative_verbs if verb in prompt.lower())
        score += min(verb_count / 5, 0.4)
        
        # Look for specific deliverables
        deliverable_patterns = [
            r'(?:function|class|module)\s+(?:named|called)\s+\w+',
            r'(?:return|output)\s+(?:a|an)\s+\w+',
            r'(?:should|must|will)\s+(?:implement|provide|handle)'
        ]
        
        deliverables = sum(1 for pattern in deliverable_patterns 
                         if re.search(pattern, prompt, re.IGNORECASE))
        score += min(deliverables / 3, 0.3)
        
        # Look for constraints and guidelines
        constraint_indicators = ["following", "adhering to", "according to", "based on"]
        constraints = sum(1 for indicator in constraint_indicators 
                        if indicator in prompt.lower())
        score += min(constraints / 2, 0.3)
        
        return score
    
    def _calculate_overall_score(self, assessments: List[QualityAssessment]) -> float:
        """Calculate overall quality score from individual assessments"""
        if not assessments:
            return 0.0
        
        # Weighted scoring
        weights = {
            QualityMetric.COMPLETENESS: 0.25,
            QualityMetric.TECHNICAL_ACCURACY: 0.25,
            QualityMetric.CURSOR_AI_COMPATIBILITY: 0.20,
            QualityMetric.CLARITY: 0.10,
            QualityMetric.SPECIFICITY: 0.10,
            QualityMetric.ACTIONABILITY: 0.10
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for assessment in assessments:
            weight = weights.get(assessment.metric, 0.1)
            total_score += assessment.score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _identify_critical_issues(self, assessments: List[QualityAssessment]) -> List[str]:
        """Identify critical issues that must be addressed"""
        critical_issues = []
        
        for assessment in assessments:
            if assessment.score < 0.5:  # Critical threshold
                critical_issues.append(
                    f"Critical issue in {assessment.metric.value}: {assessment.details}"
                )
        
        return critical_issues
    
    def _generate_improvement_suggestions(self, assessments: List[QualityAssessment]) -> List[str]:
        """Generate improvement suggestions from all assessments"""
        all_suggestions = []
        
        for assessment in assessments:
            all_suggestions.extend(assessment.suggestions)
        
        # Remove duplicates while preserving order
        unique_suggestions = []
        seen = set()
        for suggestion in all_suggestions:
            if suggestion not in seen:
                unique_suggestions.append(suggestion)
                seen.add(suggestion)
        
        return unique_suggestions
    
    async def _load_validation_rules(self) -> None:
        """Load validation rules from knowledge base"""
        self.logger.info("Loading validation rules from knowledge base")
        # Implementation would load from knowledge_manager
    
    async def _initialize_technical_validators(self) -> None:
        """Initialize technical validators"""
        self.logger.info("Initializing technical validators")
        # Implementation would set up domain-specific validators
