from langgraph.graph import START, StateGraph,END
from langgraph.checkpoint.memory import MemorySaver
from src.agents.input_validation_agent import state as state
from src.agents.input_validation_agent.nodes import evaluate_relevance,route_function,generate_synopsis,grammar_refinement,generate_blog,generate_keywords,blog_validation,blog_refinement,blog_style_guide
from IPython.display import Image, display

# Create the graph
builder = StateGraph(state.State)


# Add nodes to the graph
builder.add_node("evaluate", evaluate_relevance)
builder.add_node("generate_keywords", generate_keywords) 
builder.add_node("generate_synopsis",generate_synopsis)
builder.add_node("grammar_refinement",grammar_refinement)
builder.add_node("generate_blog",generate_blog)
builder.add_node("blog_refinement",blog_refinement)
builder.add_node("blog_style_guide",blog_style_guide)
builder.add_node("blog_validation",blog_validation)


# Add edges to define flow
builder.add_edge(START, "evaluate")
builder.add_conditional_edges("evaluate", route_function,{"generate_synopsis":"generate_synopsis",END:END})
# builder.add_edge("generate_synopsis","grammar_refinement")
# builder.add_edge("grammar_refinement","generate_keywords")
# builder.add_edge("generate_keywords","generate_blog")
builder.add_edge("generate_synopsis","generate_keywords")
builder.add_edge("generate_keywords","generate_blog")
builder.add_edge("generate_blog","blog_refinement")
builder.add_edge("blog_refinement","blog_style_guide")
builder.add_edge("blog_style_guide","blog_validation")
builder.add_edge("blog_validation",END)

# Compile the graph
checkpointer = MemorySaver()
relevance_graph = builder.compile()

display(Image(relevance_graph.get_graph().draw_mermaid_png()))
output_path = "graph.png"
graph_image=relevance_graph.get_graph().draw_mermaid_png()

with open(output_path,"wb") as f:
    f.write(graph_image)

print(f"Graph saved as {output_path}")

# relevance_graph.invoke({"user_topic":"Future Trends in Web Scraping and Data Extraction"})
# result=relevance_graph.invoke({"user_topic":user_topic,"model": model, "streaming": use_streaming})

__all__ = ["relevance_graph"]