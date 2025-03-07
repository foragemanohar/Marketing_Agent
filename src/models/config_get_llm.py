# import os
# from langchain_openai import ChatOpenAI
# # from langchain_google_genai import ChatGoogleGenerativeAI
# # from langchain_groq import ChatGroq
# # from langchain_aws import ChatBedrock
# from src.config.constants import *
# from src.config.graph_config import ModelConfig as GraphConfig
# from dotenv import load_dotenv
# load_dotenv()


# def get_llm_model(config: GraphConfig):
#     if isinstance(config, dict):
#         config_dict = config.get('configurable', {})
#         desired_model = config_dict.get('llm_model', 'OpenAI : gpt-4o')
#         temperature = config_dict.get('temperature', 0)
#         prompt_name = config_dict.get('system_prompt', 'Default-LLM')
#     else:
#         desired_model = config.llm_model
#         temperature = config.temperature
#         prompt_name = config.system_prompt

#     system_prompt = CUSTOM_PROMPTS[prompt_name]
#     provider, model_name = desired_model.split(' : ')[0].strip().lower(), desired_model.split(' : ')[-1].strip()
#     try:
#         if provider == "openai" and os.getenv("OPENAI_API_KEY"):
#             model = ChatOpenAI(temperature=temperature, model=model_name)
#         # elif provider == "google" and os.getenv("GOOGLE_API_KEY"):
#         #     model = ChatGoogleGenerativeAI(temperature=temperature, model=model_name)
#         # elif provider == 'groq' and os.getenv("GROQ_API_KEY"):
#         #     model = ChatGroq(temperature=temperature, model=model_name)
#         # elif provider == 'aws' and os.getenv("AWS_API_KEY"):
#         #     model = ChatBedrock(model_id=model_name, model_kwargs={'temperature': temperature})
#         else:
#             raise ValueError(f"Unsupported provider: {provider}")
#     except Exception as e:
#         print(f"Error creating model: {str(e)}")
#         raise

#     return model, system_prompt


# def retrieve_model_name(model):
#     attributes = ['model_name', 'model', 'model_id']
#     for attr in attributes:
#         if hasattr(model, attr):
#             return getattr(model, attr)
#     return "Unknown Model"