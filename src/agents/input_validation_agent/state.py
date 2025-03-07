
from typing import List
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from typing_extensions import Annotated, TypedDict


# Define the schema for the state maintained throughout the conversation
class State(TypedDict):
    
    user_topic: str
    """The topic provided by the user."""

    provider:str
    """provider whether it is openai or anthropic."""

    model:str
    """the model provided by the user"""

    rating: int
    """Relevance rating of the topic from 1 to 10."""

    recommendations: List[str]
    """recommendations for irrelevant topics are provided"""
    reasons:List[str]
    """reasons of why topic is irrelevant"""

    error_message: str
    """error messages are stored"""

    refined_blog:str
    """blog after reducing ai content"""

    style_guide_blog:str
    """blog after enhancing the style guide"""

    keywords:List[str]
    """20 keywords for best seo for the given topic are provided"""

    blog_outline:List[str]
    """table of contents are provided"""
    refined_blog_outline:List[str]
    """table of contents are provided"""
    
    blog:str
    """blog for the given topic"""

    validated_blog:str
    """stores the validated blog after checking few criteria"""
    blog_content:str
    """this is refined blog after suggestions"""
    seo_suggestions:str
    """extracted suggestions from semrush scraping"""
    seo_score:str
    """extracted score from semrush scraping"""



__all__ = [
    "State",
]

