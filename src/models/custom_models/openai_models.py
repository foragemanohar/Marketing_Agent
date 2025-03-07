from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
load_dotenv()

print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))
print("OPENAI_MODEL_NAME:", os.getenv("OPENAI_MODEL_NAME"))

def get_open_ai(temperature=0, model=os.getenv("OPENAI_MODEL_NAME")):
# def get_open_ai(temperature=0, model=OPENAI_MODEL_NAME):
    llm = ChatOpenAI(
        model=model,
        temperature = temperature,
        api_key=os.getenv("OPENAI_API_KEY")  
    )
    return llm

def get_open_ai_json(temperature=0, model=os.getenv("OPENAI_MODEL_NAME")):
    llm = ChatOpenAI(
        model=model,
        temperature = temperature,
        model_kwargs={"response_format": {"type": "json_object"}},
    )
    return llm  

llm = get_open_ai()
response = llm.invoke("Tell me a joke")
print(response)
