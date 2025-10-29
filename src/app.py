"""Main application file for Destination Compass."""

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# Load environment variables AS EARLY AS POSSIBLE to ensure services see them
load_dotenv()

from models.state import DestinationCompassState
from nodes import (
    parse_query, geocode_location, get_local_time, 
    get_weather, get_news, get_events, aggregate_results
)
from ui import GradioInterface
from config_loader import config


class DestinationCompassApp:
    """Main application class for Destination Compass."""
    
    def __init__(self):
        """Initialize the application."""
        # Environment already loaded at module import time
        
        # Get app configuration
        self.app_config = config.get_app_config()
        self.langgraph_config = self.app_config.get("langgraph", {})
        self.checkpointer_type = self.langgraph_config.get("checkpointer", "memory")
        self.thread_id = self.langgraph_config.get("thread_id", "1")
        
        # Build the workflow
        self.workflow = self._build_workflow()
        
        # Initialize checkpointer
        if self.checkpointer_type == "memory":
            memory = MemorySaver()
            self.graph = self.workflow.compile(checkpointer=memory)
        else:
            self.graph = self.workflow.compile()
        
        # Create execution config
        self.execution_config = {"configurable": {"thread_id": self.thread_id}}
        
        # Initialize UI
        self.ui = GradioInterface(self.chat)
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow.
        
        Returns:
            StateGraph: Configured workflow
        """
        workflow = StateGraph(DestinationCompassState)
        
        # Add nodes
        workflow.add_node("parse_query", parse_query)
        workflow.add_node("geocode_location", geocode_location)
        workflow.add_node("get_local_time", get_local_time)
        workflow.add_node("get_weather", get_weather)
        workflow.add_node("get_news", get_news)
        workflow.add_node("get_events", get_events)
        workflow.add_node("aggregate_results", aggregate_results)
        
        # Router: if parse_query already produced final_output, end early; otherwise continue
        def route_after_parse(state: dict) -> str:
            return "END" if state.get("final_output") else "geocode_location"

        # Add edges
        workflow.add_edge(START, "parse_query")
        workflow.add_conditional_edges("parse_query", route_after_parse, {"geocode_location": "geocode_location", "END": END})
        workflow.add_edge("geocode_location", "get_local_time")
        workflow.add_edge("geocode_location", "get_weather")
        workflow.add_edge("geocode_location", "get_news")
        workflow.add_edge("geocode_location", "get_events")
        workflow.add_edge("get_local_time", "aggregate_results")
        workflow.add_edge("get_weather", "aggregate_results")
        workflow.add_edge("get_news", "aggregate_results")
        workflow.add_edge("get_events", "aggregate_results")
        workflow.add_edge("aggregate_results", END)
        
        return workflow
    
    def chat(self, user_input: str, history):
        """Chat function for processing user input.
        
        Args:
            user_input: User's input message
            history: Chat history
            
        Returns:
            str: Response message
        """
        result = self.graph.invoke(
            {"user_query": user_input}, 
            config=self.execution_config
        )
        return result["final_output"]
    
    def run(self):
        """Run the application."""
        print("Starting Destination Compass...")
        print("Configuration loaded successfully")
        print("Ready to provide destination information!")
        
        # Launch the UI
        self.ui.launch()


def main():
    """Main entry point."""
    app = DestinationCompassApp()
    app.run()


if __name__ == "__main__":
    main()
