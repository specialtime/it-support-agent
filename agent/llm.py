import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

load_dotenv()

def get_llm():
    """
    Factory para obtener el LLM correspondiente basado en LLM_ENV 
    """
    env = os.getenv("LLM_ENV", "local")
    
    if env == "local":
        return ChatOpenAI(
            base_url="http://localhost:1234/v1",
            api_key="lm-studio",
            model="local-model",
            temperature=0.1,
            max_tokens=1500,
            frequency_penalty=1.0,
            presence_penalty=0.5
        )
    elif env == "groq":
        return ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama-3.3-70b",
            temperature=0
        )
    elif env == "azure":
        from langchain_openai import AzureChatOpenAI
        return AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY")
        )
    
    raise ValueError(f"Unknown LLM_ENV: {env}")
