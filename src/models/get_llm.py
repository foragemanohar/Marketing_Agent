from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_anthropic import ChatAnthropic
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from typing import Literal,Optional
import openai


def get_model(provider:Literal['openai','google','meta','anthropic'],model_name:Optional[str] = None):
    if provider == "openai":
        print("*************openai****************")
        print("*********"+model_name+"*********")
        model_name=model_name or "gpt-4o-mini"
        return ChatOpenAI(temperature=0, model=model_name,stream=False,model_kwargs={"response_format": {"type": "json_object"}})
    elif provider == "anthropic":
        print("************anthropic**************")
        model_name=model_name or "claude-3-5-haiku-20241022"
        return ChatAnthropic(temperature=0, model_name=model_name,max_tokens=4096)
    # elif provider == "google":
    #     return ChatGoogleGenerativeAI(temperature=0, model_name="gemini-1.5-pro-exp-0801")
    # elif provider == "meta":
    #     return ChatGroq(temperature=0, model_name="llama-3.1-70b-versatile")
    
