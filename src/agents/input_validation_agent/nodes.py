from src.agents.input_validation_agent.state import State # Import your state class
from langchain.prompts import ChatPromptTemplate  # Import Langchain's prompt template
# from langchain.llms import <YourLLMClass>  # Import your chosen LLM class (e.g., OpenAI, Gemini)
import json  # For parsing the JSON response
from src.models.get_llm import get_model
from langgraph.graph import END
from src.agents.input_validation_agent.prompts.memory_prompts import input_validation_prompt,keyword_prompt,synopsis_prompt,blog_prompt,validation_prompt,grammar_refinement_prompt,refined_blog_prompt,blog_style_guide_prompt
import re
from dotenv import load_dotenv
import os
import pandas as pd
import numpy as np
import openai
import sklearn
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from pathlib import Path
from typing import Literal,Optional


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


def evaluate_relevance(state: State):
    """
    Evaluates the relevance of the user's topic using an LLM model.
    
    Args:
        state (dict): A dictionary containing the user's topic .
    
    Returns:
        dict: Updated state with rating and recommendations.
    """
    input_text = state.get("user_topic")
    provider = state.get("provider") 
    model = state.get("model") 
    if not input_text:
        state["error_message"] = "Missing or empty user_topic"
        state["rating"] = 0
        state["recommendations"]=[]
        state["reasons"]=[]
        return state
    messages = [{"role": "user", "content": input_text}] 
    if provider == "anthropic":
        system_message = {
            "role": "system",
            "content": "You must return a response strictly in JSON format with keys: 'rating' (integer), 'recommendations' (list) 'reasons'(list). Do not include extra text."
        }
        messages.insert(0, system_message)
    final_prompt = input_validation_prompt.format_messages(messages=messages)  # Format the prompt with the input
    llm = get_model(provider=provider,model_name=model) 
    try:
        llm_output = llm(final_prompt)
        if not llm_output:
            state["error_message"] = "LLM did not return a response"
            state["rating"] = 0
            state["recommendations"]=[]
            state["reasons"]=[]
            return state
        if hasattr(llm_output, 'content'):  # AIMessage
            llm_content = llm_output.content
        elif isinstance(llm_output, str):  # String output
            llm_content = llm_output
        else:
            state["error_message"] = f"Unexpected response type: {type(llm_output)}"
            state["rating"] = 0
            state["recommendations"]=[]
            state["reasons"]=[]
            return state
        # print(llm_content,"==========")
        llm_content=llm_content.replace("```json","").replace("```","").strip()
        try:
        # Attempt to parse as JSON first:
            json_output = json.loads(llm_content)  # Assuming the LLM returns valid JSON
            # print(json_output,"+++++++++++++++++++++")
            rating = json_output.get("rating", 0)
            recommendations = json_output.get("recommendations", [])
            reasons=json_output.get("reasons",[])
            # Ensure rating is a valid integer
            try:
                state["rating"] = int(rating)
                state["recommendations"]=recommendations
                state["reasons"]=reasons
            except (ValueError, TypeError):
                state["rating"] = 0
                state["recommendations"]=[]
                state["reasons"]=[]

    
        except json.JSONDecodeError:
            # If JSON parsing fails, treat as a plain string:
            # state["rating"] = llm_content  # Store the string directly
            state["rating"] = 0
            state["recommendations"] = []
            state["reasons"]=[]
            print("Not a valid JSON, storing as string") # Indicate it's stored as String
            # Optional: You can convert to HTML here if needed (see previous response)
        # recommendations = json_output.get("recommendations", []) # Handle missing recommendations
        print(state)
        print("****************")
        # print(recommendations)
        # state["rating"] = rating
        # state["recommendations"] = recommendations
    except Exception as e:
        state["error_message"] = f"Error processing LLM response: {e}"
        state["rating"] = 0
        state["recommendations"] = []
    return state # Return the state even if there is an error


def route_function(state):
    """
    Determines the next step based on the rating in the state.
    
    Args:
        state (dict): A dictionary containing the rating.
    
    Returns:
        str: The next route based on the rating.
    """
    
    score = state.get("rating", 0)  # Default to 0 if missing

    # Ensure the score is a valid number
    if not isinstance(score, (int, float)):
        score = 0

    if score >= 8:
        return "generate_synopsis"  # Go to the generate_keywords node
    else:
        return END # Go to the end node

def generate_synopsis(state:State): # Type hint the state!
    
    """
    Generates synopsis (the blog outline) based on the user topic using an LLM model.
    
    Args:
        state (dict): A dictionary containing the user topic.
    
    Returns:
        dict: Updated state with generated blog outline.
    """
    # print(state.get("user_topic", ""), "----------")
    user_topic = state.get("user_topic","")
    provider = "openai" 
    model =  "gpt-4o"
    messages = [{"role": "user", "content": user_topic}] # Format it as Langchain messages
    if provider == "anthropic":
        system_message = {
            "role": "system",
            "content": "You must return a response strictly in JSON format with a single key 'blog_outline' containing the outline of the blog. Do not include any extra text or unnecessary keys."
        }
        messages.insert(0, system_message)
    final_prompt = synopsis_prompt.format_messages(messages=messages)  # Format the prompt with the input
    # print("-------",final_prompt)
    # llm_output = llm(final_prompt)  # Call the LLM with the formatted prompt
    llm = get_model(provider=provider,model_name=model) 
    llm_output = None  

    try:
        # 4. Parse the JSON response:
        llm_output = llm(final_prompt)
        # print(final_prompt,"generate_synopsis")
        # Extract the content (handle different possible output types):
        # print(llm_output,"synopsis")
        if hasattr(llm_output, 'content'):  # AIMessage
            llm_content = llm_output.content
        elif isinstance(llm_output, str):  # String output
            llm_content = llm_output
        else:
            state["error_message"] = f"Unexpected response type: {type(llm_output)}"
            state["blog_outline"] = []
            return state
        # Validate response length
        if not llm_content or len(llm_content) < 5:
            state["error_message"] = "Invalid or empty response from LLM."
            state["blog_outline"] = []
            return state
        try:
            json_output = json.loads(llm_content)  # Assuming the LLM returns valid JSON
            state["blog_outline"] = json_output.get("blog_outline", []) # Handle missing recommendations
            print("..........blog_outline..............",state["blog_outline"])
        except json.JSONDecodeError:
            # If not valid JSON, store as raw text
            state["blog_outline"] = [llm_content] 
        # print(state["blog_outline"],"----------------synopsis---------------")       
        
        
        # print(state,"+++++++++++++++++++++++++")
    except (ValueError, TypeError) as e:
        state["error_message"] = f"Error processing LLM response: {e}."
        state["blog_outline"] = []

    return state # Return the state even if there is an error

def grammar_refinement(state:State):
    """
    Generates synopsis (the blog outline) based on the user topic using an LLM model.
    
    Args:
        state (dict): A dictionary containing the user topic.
    
    Returns:
        dict: Updated state with generated blog outline.
    """
    user_topic = state.get("user_topic","")
    provider = state.get("provider") 
    model = state.get("model") 
    messages = [{"role": "user", "content": user_topic}] # Format it as Langchain messages
    if provider == "anthropic":
        system_message = {
            "role": "system",
            "content": "You must return a response strictly in JSON format with a single key 'blog_outline' containing the outline of the blog. Do not include any extra text or unnecessary keys."
        }
        messages.insert(0, system_message)
    final_prompt = grammar_refinement_prompt.format_messages(messages=messages)  # Format the prompt with the input
    llm = get_model(provider=provider,model_name=model) 
    llm_output = None
    try:
        llm_output = llm(final_prompt)
        if hasattr(llm_output, 'content'):  # AIMessage
            llm_content = llm_output.content
        elif isinstance(llm_output, str):  # String output
            llm_content = llm_output
        else:
            state["error_message"] = f"Unexpected response type: {type(llm_output)}"
            state["refined_blog_outline"] = []
            return state
        # Validate response length
        print(state,"************************")
        if not llm_content or len(llm_content) < 5:
            state["error_message"] = "Invalid or empty response from LLM."
            state["refined_blog_outline"] = []
            return state
        try:
            json_output = json.loads(llm_content)  # Assuming the LLM returns valid JSON
            state["refined_blog_outline"] = json_output.get("refined_blog_outline", []) # Handle missing recommendations
        except json.JSONDecodeError:
            # If not valid JSON, store as raw text
            state["refined_blog_outline"] = [llm_content]         
        print(state,"+++++++++++++++++++++++++")
    except (ValueError, TypeError) as e:
        # state["error_message"] = f"Error processing LLM response: {e}. Raw Output: {llm_output}"
        state["error_message"] = f"Error processing LLM response: {e}."
        state["refined_blog_outline"] = []
        

    return state # Return the state even if there is an error
  

def parse_blog_content(llm_content:str ,field:Literal["blog", "validated_blog"]):
    """
    Parse blog content that may be in JSON format or raw string.
    Handles multiple formats and common JSON parsing issues.
    
    Args:
        llm_content (str): The input content to parse.
        field (Literal["blog", "validated_blog"]): The key to extract (either "blog" or "validated_blog").
        
    Returns:
        str: The extracted blog content.
    """
    try:
        # First try: Direct JSON parsing
        json_output = json.loads(llm_content)
        # print(json_output)
        return json_output.get(field, "")
    except json.JSONDecodeError:
        try:
            # match = re.search(r'"blog":\s*"(.+?)"}', llm_content, re.DOTALL)
            llm_content = f'"""{llm_content}"""'
            # match = re.search(r'"blog":\s*"([^"]+)"', llm_content, re.DOTALL)
            match = re.search(rf'"{field}":\s*"([^"]+)"', llm_content, re.DOTALL)

            if match:
                llm_content = match.group(1).replace("\\n", "\n")  # Replace escaped newlines if needed
                # print(llm_content)
                # print("-----")
                return llm_content
        except:
            pass
            
            # If everything fails, return the original content
            print("Warning: Could not parse as JSON, returning original content")
            return llm_content


import pandas as pd
from pathlib import Path

def keywords_from_csv():
    # Define the file path
    file_path = Path(__file__).resolve().parent / "keywords_semrush.csv"

    try:
        # Load CSV data
        keywords_df = pd.read_csv(file_path)

        # Ensure SV and KD are numeric (handle missing or non-numeric values)
        keywords_df['SV'] = pd.to_numeric(keywords_df['SV'], errors='coerce')
        keywords_df['KD'] = pd.to_numeric(keywords_df['KD'], errors='coerce')

        # Drop any rows where SV or KD is NaN after conversion
        keywords_df.dropna(subset=['SV', 'KD'], inplace=True)

        # Remove KD > 95
        keywords_df = keywords_df[keywords_df['KD'] <= 95]

        # Remove the top 5 lowest SV values
        keywords_df = keywords_df.sort_values(by="SV", ascending=True).iloc[5:]

        # Keep only required columns
        filtered_df = keywords_df[['Keywords', 'KD', 'SV']]

        # Convert to dictionary format
        final_dict = {
            'selected_keywords': filtered_df[['Keywords', 'SV', 'KD']].to_dict(orient='records')
        }

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        final_dict = {}

    except Exception as e:
        print(f"An error occurred: {e}")
        final_dict = {}

    return final_dict  # Return the dictionary


def generate_blog(state: State):
    print("blog called")
    """
    Generates a blog based on the user topic and blog outline provided.

    Args:
        state (dict): A dictionary containing the user topic and blog_outline.

    Returns:
        dict: Updated state with generated blog.
    """
    # print(state.get("user_topic", ""), "----------")
    user_topic = state.get("user_topic", "")
    blog_outline = state.get("blog_outline", [])
    provider = state.get("provider") 
    model = state.get("model") 
    keywords=state.get("keywords")
    input_dict = {
    "user_topic": user_topic,
    "blog_outline": blog_outline,
    "keywords":keywords,
    }
    # # Ensure blog_outline is a list of dictionaries
    # if not isinstance(blog_outline, list):
    #     blog_outline = [blog_outline]  # Convert to list if it's a single dictionary

    # # Extract and format the blog outline properly
    # extracted_outline = []
    # for section in blog_outline:
    #     section_title = section.get("section", "Unknown Section")
    #     points = section.get("points", [])
    #     formatted_points = "\n".join(f"- {point}" for point in points) if isinstance(points, list) else ""
    #     extracted_outline.append(f"**{section_title}**\n{formatted_points}")

    # formatted_outline = "\n\n".join(extracted_outline)
    messages = [{"role": "user", "content": str(input_dict)}]
    final_prompt = blog_prompt.format_messages(messages=messages)  # Format the prompt with the input
    if provider == "anthropic":
        system_message = {
            "role": "system",
            "content": "You must return a response strictly in JSON format with a single key 'blog' containing the markdown format of blog. Do not include any extra text or unnecessary keys.Provide blog from 1500 to 2000 words."
        }
        messages.insert(0, system_message)
    llm =get_model(provider=provider,model_name=model)  
    try:
        llm_output = llm(final_prompt)
        # print(llm_output,"-------------*****")
        # print(llm_output, "llm_output")
        if hasattr(llm_output, 'content'):
            llm_content = llm_output.content
        elif isinstance(llm_output, str):
            llm_content = llm_output
        else:
            raise TypeError(f"Unexpected LLM output type: {type(llm_output)}")
        llm_content=llm_content.replace("```json","").replace("```","").strip()
        # print(llm_content,"llm_content")
        llm_content = llm_content.replace('```json\n', '').replace('\n```', '')
        # llm_content = llm_content.replace('`', '"')
        # # Also need to handle escaped quotes within the blog content
        # llm_content = re.sub(r'(?<!\\)"', '\\"', llm_content[1:-1])
        # print(llm_content,"+++++++++++++++++++++++++++++++++++")
        try:
            state["blog"] = parse_blog_content(llm_content,"blog")
            print("..........blog..............",state["blog"])
            print("Successfully parsed blog content")
        except Exception as e:
            print(f"Error parsing blog content: {str(e)}")
        # try:
        # # Attempt to parse as JSON first:
        #     json_output = json.loads(llm_content)
        #     state["blog"] = json_output.get("blog", "") # Extract if JSON is correct
        #     print(json_output,"json_output")  # Print for debugging
        # except json.JSONDecodeError:
        #     # If JSON parsing fails, treat as a plain string:
        #     # llm_content=llm_content[10:-2]
        #     state["blog"] = llm_content  # Store the string directly
        #     print("Not a valid JSON, storing as string") # Indicate it's stored as String
        #     # Optional: You can convert to HTML here if needed (see previous response)
       
        # json_output = json.loads(llm_content)
        # print(json_output,"json_output")
        # state["blog"] = json_output.get("blog", "") 
        # state["blog"]=llm_content
        # print(state["blog"], "+++++++++++++++++++++++++")
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        error_message = f"Error processing LLM response: {e}."
        state["error_message"] = error_message
        print(error_message, "error message")
        # state["blog_outline"] = state.get("blog_outline", [])
    return state  # Return the state even if there is an error

# blog_refinement,blog_style_guide

def blog_refinement(state: State):
    print("blog refinement called")
    """
    Generates a blog based on the user topic and blog outline provided.

    Args:
        state (dict): A dictionary containing the user topic and blog_outline.

    Returns:
        dict: Updated state with generated blog.
    """
    # print(state.get("user_topic", ""), "----------")
    user_topic = state.get("user_topic", "")
    blog_outline = state.get("blog_outline", [])
    blog=state.get("blog","")
    provider = state.get("provider") 
    model = state.get("model") 
    keywords=state.get("keywords")
    input_dict = {
    "user_topic": user_topic,
    "blog_outline": blog_outline,
    "keywords":keywords,
    "blog":blog
    }
    messages = [{"role": "user", "content": str(input_dict)}]
    final_prompt = refined_blog_prompt.format_messages(messages=messages)  # Format the prompt with the input
    if provider == "anthropic":
        system_message = {
            "role": "system",
            "content": "You must return a response strictly in JSON format with a single key 'refined_blog' containing the markdown format of blog. Do not include any extra text or unnecessary keys.Provide blog from 1500 to 2000 words"
        }
        messages.insert(0, system_message)
    llm =get_model(provider=provider,model_name=model)  
    try:
        llm_output = llm(final_prompt)
        if hasattr(llm_output, 'content'):
            llm_content = llm_output.content
        elif isinstance(llm_output, str):
            llm_content = llm_output
        else:
            raise TypeError(f"Unexpected LLM output type: {type(llm_output)}")
        llm_content=llm_content.replace("```json","").replace("```","").strip()
        llm_content = llm_content.replace('```json\n', '').replace('\n```', '')
        try:
            state["refined_blog"] = parse_blog_content(llm_content,"refined_blog")
            print("Successfully parsed blog content")
        except Exception as e:
            print(f"Error parsing blog content: {str(e)}")
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        error_message = f"Error processing LLM response: {e}."
        state["error_message"] = error_message
        print(error_message, "error message")
        # state["blog_outline"] = state.get("blog_outline", [])
    return state  # Return the state even if there is an error


def blog_style_guide(state: State):
    print("blog style guide called")
    """
    Generates a blog based on the user topic and blog outline provided.

    Args:
        state (dict): A dictionary containing the user topic and blog_outline.

    Returns:
        dict: Updated state with generated blog.
    """
    # print(state.get("user_topic", ""), "----------")
    user_topic = state.get("user_topic", "")
    blog_outline = state.get("blog_outline", [])
    provider = state.get("provider") 
    model = state.get("model") 
    keywords=state.get("keywords") 
    input_dict = {
    "user_topic": user_topic,
    "blog_outline": blog_outline,
    "keywords":keywords
   
    }
    messages = [{"role": "user", "content": str(input_dict)}]
    final_prompt = blog_style_guide_prompt.format_messages(messages=messages)  # Format the prompt with the input
    if provider == "anthropic":
        system_message = {
            "role": "system",
            "content": "You must return a response strictly in JSON format with a single key 'style_guide_blog' containing the markdown format of blog. Do not include any extra text or unnecessary keys.Provide blog from 1500 to 2000 words"
        }
        messages.insert(0, system_message)
    llm =get_model(provider=provider,model_name=model)  
    try:
        llm_output = llm(final_prompt)
        # print(llm_output,"-------------*****")
        # print(llm_output, "llm_output")
        if hasattr(llm_output, 'content'):
            llm_content = llm_output.content
        elif isinstance(llm_output, str):
            llm_content = llm_output
        else:
            raise TypeError(f"Unexpected LLM output type: {type(llm_output)}")
        llm_content=llm_content.replace("```json","").replace("```","").strip()
        # print(llm_content,"llm_content")
        llm_content = llm_content.replace('```json\n', '').replace('\n```', '')
        try:
            state["style_guide_blog"] = parse_blog_content(llm_content,"style_guide_blog")
            print(state["style_guide_blog"],"+++++++++++")
            print("Successfully parsed blog content")
        except Exception as e:
            print(f"Error parsing blog content: {str(e)}")
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        error_message = f"Error processing LLM response: {e}."
        state["error_message"] = error_message
        print(error_message, "error message")
        # state["blog_outline"] = state.get("blog_outline", [])
    return state  # Return the state even if there is an error

def generate_keywords(state:State): # Type hint the state!
    """
    Generates keywords based on the user topic using an LLM model.
    
    Args:
        state (dict): A dictionary containing the user topic.
    
    Returns:
        dict: Updated state with generated keywords.
    """
    
    # print(state.get("user_topic", ""), "----------")
    user_topic = state.get("user_topic")
    blog_outline=state.get("blog_outline")
    provider = state.get("provider") 
    model = state.get("model") 
    keywords=keywords_from_csv()
    input_dict = {
    "user_topic": user_topic,
    "blog_outline": blog_outline,
    "keywords":keywords
    }
    messages = [{"role": "user", "content": str(input_dict)}] # Format it as Langchain messages
    final_prompt = keyword_prompt.format_messages(messages=messages)  # Format the prompt with the input
    # print("-------",final_prompt)
    # llm_output = llm(final_prompt)  # Call the LLM with the formatted prompt
    llm = get_model(provider=provider,model_name=model) 
    try:
        # 4. Parse the JSON response:
        llm_output = llm(final_prompt)
        # Extract the content (handle different possible output types):
        if hasattr(llm_output, 'content'):  # AIMessage
            llm_content = llm_output.content
        elif isinstance(llm_output, str):  # String output
            llm_content = llm_output
        else:
            raise TypeError(f"Unexpected LLM output type: {type(llm_output)}")
        json_output = json.loads(llm_content)  # Assuming the LLM returns valid JSON
        user_topic = json_output.get("user_topic","")
        generate_keywords = json_output.get("generate_keywords", []) # Handle missing recommendations
        state["keywords"] = generate_keywords
        # print(state,"+++++++++++++++++++++++++")
        

    except (json.JSONDecodeError, ValueError,TypeError) as e:
        # Handle parsing or validation errors:
        error_message = f"Error processing LLM response: {e}."
        state["error_message"] = error_message  # Store the error in the state
        # print(error_message,"error message")  # Print for debugging
        state["keywords"] = llm_content
    return state # Return the state even if there is an error

def blog_validation(state:State,iteration: Optional[int] = None,blog_content:Optional[str]=None):
    print("blog validation called")
     
    """
    Generates blog after validating few criteria.
    
    Args:
        state (dict): A dictionary containing the user topic.
        blog(string): blog
    
    Returns:
        str: Updated blog after validation.
    """
    user_topic = state.get("user_topic")
    blog_outline=state.get("blog_outline")
    provider = state.get("provider") 
    model = state.get("model") 
    seo_suggestions=state.get("seo_suggestions")
    # seo_score=state.get("seo_score")
    if iteration:
        print(iteration,";;;;;;")
        blog=state.get("blog_content")
        print(":::::::::::::::::::::::",blog)
        input_dict = {
        "blog": blog,
        "seo_suggestions":seo_suggestions,
        }
    else:
        blog=state.get("style_guide_blog")
        input_dict = {
        "user_topic": user_topic,
        "blog": blog,
        "blog_outline":blog_outline,
        "seo_suggestions":seo_suggestions,
        }
    print(input_dict,"[[[[[[]]]]]]")

    messages = [{"role": "user", "content": str(input_dict)}] # Format it as Langchain messages
    final_prompt = validation_prompt.format_messages(messages=messages)  # Format the prompt with the input
    if iteration and iteration>3:
        system_message = {
            "role": "system",
            "content": ("The blog has been generated more than 3 times.Ensure the SEO score reaches **9.5** by making the content more structured, simplifying language, and improving paragraph splitting by carefully checking seo_suggestions and seo_score.**Simplify the language**: Use short, clear sentences.**Improve paragraph structure**: Split long paragraphs for better readability.**Enhance SEO keywords**: Ensure all target keywords are naturally included.**Fix sentence flow**: Make the blog sound human-like, avoiding redundancy."
            )
        }
        messages.insert(0, system_message)
    if provider == "anthropic":
        system_message = {
            "role": "system",
            "content": "You must return a response strictly in JSON format with a single key 'validated_blog' containing the markdown format of blog. Do not include any extra text or unnecessary keys.Provide blog from 1500 to 2000 words"
        }
        messages.insert(0, system_message)
    
    # print("-------",final_prompt)
    # llm_output = llm(final_prompt)  # Call the LLM with the formatted prompt
    llm = get_model(provider=provider,model_name=model) 
    try:
        # 4. Parse the JSON response:
        llm_output = llm(final_prompt)
        # Extract the content (handle different possible output types):
        if hasattr(llm_output, 'content'):  # AIMessage
            llm_content = llm_output.content
        elif isinstance(llm_output, str):  # String output
            llm_content = llm_output
        else:
            raise TypeError(f"Unexpected LLM output type: {type(llm_output)}")
        llm_content = llm_content.replace('```json\n', '').replace('\n```', '')
        # breakpoint()
        try:
            llm_output = None  # ✅ Initialize before the try block

            print(llm_content,"[[[[[[[]]]]]]]")
            # If llm_content is already a dict, use it directly
            if isinstance(llm_content, dict):
                result = llm_content.get('validated_blog', '')
            else:
                # Otherwise clean up and parse
                llm_content = llm_content.replace("```json","").replace("```","").strip()
                result = parse_blog_content(llm_content, "validated_blog")
                
            # print(result)
            # with open("validated_blog.md", "w", encoding="utf-8") as file:
            #     file.write(result)
            state["validated_blog"] = result
            print("........validatedblog.......",state["validated_blog"])
            # print(state.get("validated_blog"),"========")
            # if state.get("validated_blog"):
            #     with open("validated_blog.md", "w", encoding="utf-8") as file:
            #         file.write(result)
            print("Successfully parsed blog content")
        except Exception as e:
            print(f"Error parsing blog content: {str(e)}")
        # json_output = json.loads(llm_content)  # Assuming the LLM returns valid JSON
        # user_topic = json_output.get("user_topic","")
        # validated_blog = json_output.get("validated_blog","") # Handle missing recommendations
        # state["validated_blog"] = validated_blog
        # Save validated blog to a markdown file
        
    except (json.JSONDecodeError, ValueError,TypeError) as e:
        # Handle parsing or validation errors:
        error_message = f"Error processing LLM response: {e}."
        state["error_message"] = error_message  # Store the error in the state
        print(error_message,"error message")  # Print for debugging
        state["validated_blog"] = llm_content
    return state # Return the state even if there is an error

     


