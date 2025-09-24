"""
Configuration management for the DLD to Cursor AI Prompt Generation System
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field

class AgentConfig(BaseModel):
    """Configuration for individual agents"""
    enabled: bool = True
    timeout: int = 300
    max_retries: int = 3
    parameters: Dict[str, Any] = {}

class LLMConfig(BaseModel):
    """LLM configuration"""
    provider: str = "openai"
    model: str = "gpt-4"
    api_key: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 60

class KnowledgeBaseConfig(BaseModel):
    """Knowledge base configuration"""
    enabled: bool = True
    data_path: str = "knowledge_base/data"
    update_interval: int = 3600  # seconds
    cache_size: int = 1000

class Config(BaseModel):
    """Main system configuration"""
    
    # System settings
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    max_concurrent_requests: int = Field(default=10)
    
    # Agent configurations
    context_validation_agent: AgentConfig = Field(default_factory=AgentConfig)
    prompt_generator_agent: AgentConfig = Field(default_factory=AgentConfig)
    code_quality_agent: AgentConfig = Field(default_factory=AgentConfig)
    prompt_output_agent: AgentConfig = Field(default_factory=AgentConfig)
    feedback_loop: AgentConfig = Field(default_factory=AgentConfig)
    
    # LLM configuration
    llm: LLMConfig = Field(default_factory=LLMConfig)
    
    # Knowledge base configuration
    knowledge_base: KnowledgeBaseConfig = Field(default_factory=KnowledgeBaseConfig)
    
    # 5G Domain specific settings
    domain_5g: Dict[str, Any] = Field(default_factory=lambda: {
        "protocols": ["NR", "LTE", "5GC", "RAN", "NG-RAN"],
        "frequency_bands": ["FR1", "FR2", "sub6", "mmWave"],
        "network_functions": ["AMF", "SMF", "UPF", "PCF", "AUSF", "UDM", "NRF"],
        "interfaces": ["N1", "N2", "N3", "N4", "N6", "N8", "N11", "N15", "N22"],
        "performance_kpis": ["latency", "throughput", "reliability", "energy_efficiency"]
    })
    
    # Cursor AI specific settings
    cursor_ai: Dict[str, Any] = Field(default_factory=lambda: {
        "prompt_format": "structured",
        "max_prompt_length": 8000,
        "include_context": True,
        "include_examples": True,
        "optimization_level": "high"
    })
    
    # Quality thresholds
    quality_thresholds: Dict[str, float] = Field(default_factory=lambda: {
        "dld_completeness": 0.8,
        "technical_accuracy": 0.9,
        "prompt_effectiveness": 0.85,
        "code_quality": 0.9
    })
    
    @classmethod
    def load_from_file(cls, config_path: str = "config.yaml") -> "Config":
        """Load configuration from YAML file"""
        config_file = Path(config_path)
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                return cls(**config_data)
        else:
            # Create default config file
            config = cls()
            config.save_to_file(config_path)
            return config
    
    def save_to_file(self, config_path: str = "config.yaml") -> None:
        """Save configuration to YAML file"""
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, allow_unicode=True)
    
    def get_agent_config(self, agent_name: str) -> AgentConfig:
        """Get configuration for specific agent"""
        return getattr(self, agent_name, AgentConfig())
    
    def update_from_env(self) -> None:
        """Update configuration from environment variables"""
        # LLM settings
        if os.getenv("OPENAI_API_KEY"):
            self.llm.api_key = os.getenv("OPENAI_API_KEY")
        
        if os.getenv("LLM_MODEL"):
            self.llm.model = os.getenv("LLM_MODEL")
        
        if os.getenv("DEBUG"):
            self.debug = os.getenv("DEBUG").lower() == "true"
        
        if os.getenv("LOG_LEVEL"):
            self.log_level = os.getenv("LOG_LEVEL")

# Global configuration instance
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config.load_from_file()
        _config_instance.update_from_env()
    return _config_instance

def set_config(config: Config) -> None:
    """Set global configuration instance"""
    global _config_instance
    _config_instance = config
