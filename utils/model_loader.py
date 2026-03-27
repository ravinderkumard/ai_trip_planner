import logging
import os
from typing import Literal, Optional, Any

from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from utils.config_loader import load_config

logger = logging.getLogger(__name__)


class ConfigLoader:
    def __init__(self):
        self.config = load_config()
        logger.info("Model configuration loaded")
    
    def __getitem__(self, key):
        return self.config[key]

class ModelLoader(BaseModel):
    model_provider: Literal["groq", "openai"] = "openai"
    config: Optional[ConfigLoader] = Field(default=None, exclude=True)

    def model_post_init(self, __context: Any) -> None:
        self.config = ConfigLoader()
    
    class Config:
        arbitrary_types_allowed = True
    
    def load_llm(self):
        """
        Load and return the LLM model.
        """
        logger.info("Loading language model provider=%s", self.model_provider)
        if self.model_provider == "groq":
            groq_api_key = os.getenv("GROQ_API_KEY")
            model_name = os.getenv("GROQ_MODEL_NAME") or self.config["llm"]["groq"]["model_name"]
            if not groq_api_key:
                logger.warning("GROQ_API_KEY is not configured")
            logger.info("Initializing Groq model model_name=%s", model_name)
            llm=ChatGroq(model=model_name, api_key=groq_api_key)
        elif self.model_provider == "openai":
            openai_api_key = os.getenv("OPENAI_API_KEY")
            model_name = os.getenv("OPENAI_MODEL_NAME") or self.config["llm"]["openai"]["model_name"]
            if not openai_api_key:
                logger.warning("OPENAI_API_KEY is not configured")
            logger.info("Initializing OpenAI model model_name=%s", model_name)
            llm = ChatOpenAI(model_name=model_name, api_key=openai_api_key)
        
        return llm
    
