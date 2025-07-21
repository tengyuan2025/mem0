import subprocess
import sys
from typing import Literal, Optional

from mem0.configs.embeddings.base import BaseEmbedderConfig
from mem0.embeddings.base import EmbeddingBase

try:
    from ollama import Client
except ImportError:
    # 在Docker环境中自动安装，不等待用户输入
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "ollama"])
            from ollama import Client
        except subprocess.CalledProcessError:
            print("Failed to install 'ollama'. Please install it manually using 'pip install ollama'.")
        sys.exit(1)


class OllamaEmbedding(EmbeddingBase):
    def __init__(self, config: Optional[BaseEmbedderConfig] = None):
        super().__init__(config)

        self.config.model = self.config.model or "nomic-embed-text"
        self.config.embedding_dims = self.config.embedding_dims or 512

        self.client = Client(host=self.config.ollama_base_url)
        self._ensure_model_exists()

    def _ensure_model_exists(self):
        """
        Ensure the specified model exists locally. If not, pull it from Ollama.
        """
        try:
            local_models = self.client.list()["models"]
            # Check if model exists with exact name or with :latest suffix
            model_exists = any(
                model.get("name") == self.config.model or 
                model.get("name") == self.config.model.replace(":latest", "") or
                model.get("name") + ":latest" == self.config.model
                for model in local_models
            )
            
            if not model_exists:
                try:
                    self.client.pull(self.config.model)
                except Exception as pull_error:
                    # If pull fails, try to use the model anyway - it might exist but list failed
                    print(f"Warning: Failed to pull model {self.config.model}: {pull_error}")
                    print("Attempting to use model anyway...")
        except Exception as list_error:
            # If listing models fails, skip model check and try to use the model directly
            print(f"Warning: Failed to list models: {list_error}")
            print("Skipping model existence check...")

    def embed(self, text, memory_action: Optional[Literal["add", "search", "update"]] = None):
        """
        Get the embedding for the given text using Ollama.

        Args:
            text (str): The text to embed.
            memory_action (optional): The type of embedding to use. Must be one of "add", "search", or "update". Defaults to None.
        Returns:
            list: The embedding vector.
        """
        response = self.client.embeddings(model=self.config.model, prompt=text)
        return response["embedding"]
