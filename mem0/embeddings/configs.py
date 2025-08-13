from typing import Optional

from pydantic import BaseModel, Field, field_validator


class EmbedderConfig(BaseModel):
    provider: str = Field(
        description="Provider of the embedding model (e.g., 'huggingface', 'ollama') - optimized for local Chinese embedding",
        default="huggingface",
    )
    config: Optional[dict] = Field(
        description="Configuration for the specific embedding model - optimized for Chinese", 
        default={"model": "BAAI/bge-large-zh-v1.5"}
    )

    @field_validator("config")
    def validate_config(cls, v, values):
        provider = values.data.get("provider")
        if provider in [
            "openai",
            "ollama",
            "huggingface",
            "azure_openai",
            "gemini",
            "vertexai",
            "together",
            "lmstudio",
            "langchain",
            "aws_bedrock",
        ]:
            return v
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")
