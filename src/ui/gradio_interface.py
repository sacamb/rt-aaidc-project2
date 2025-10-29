"""Gradio interface for Destination Compass."""

import gradio as gr
from config_loader import config


class GradioInterface:
    """Gradio chat interface for Destination Compass."""
    
    def __init__(self, chat_function):
        """Initialize the Gradio interface.
        
        Args:
            chat_function: The chat function to use for processing user input
        """
        self.chat_function = chat_function
        self.app_config = config.get_app_config()
        self.gradio_config = self.app_config.get("gradio", {})
        
        # Get configuration values
        self.interface_type = self.gradio_config.get("interface_type", "messages")
        self.title = self.gradio_config.get("title", "Destination Compass")
        self.description = self.gradio_config.get("description", "Get comprehensive destination information including weather, news, and events")
        self.share = self.gradio_config.get("share", False)
        self.debug = self.gradio_config.get("debug", True)
        self.show_error = self.gradio_config.get("show_error", True)
    
    def create_interface(self):
        """Create and return the Gradio interface.
        
        Returns:
            gr.ChatInterface: Configured Gradio chat interface
        """
        return gr.ChatInterface(
            self.chat_function,
            type=self.interface_type,
            title=self.title,
            description=self.description,
        )
    
    def launch(self):
        """Launch the Gradio interface."""
        interface = self.create_interface()
        interface.launch(
            share=self.share,
            debug=self.debug,
            show_error=self.show_error
        )
