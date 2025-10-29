"""LLM service for language model operations."""

from typing import Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from config_loader import config


class LLMService:
    """Service for LLM operations including location extraction and report generation."""
    
    def __init__(self):
        self.llm_config = config.get_llm_config()
        self.model_name = self.llm_config.get("model", "llama-3.1-8b-instant")
        self.groq_api_key = config.get_api_key("groq")
        self.location_temperature = self.llm_config.get("temperature", {}).get("location_extraction", 0)
        self.report_temperature = self.llm_config.get("temperature", {}).get("report_generation", 0.3)
    
    def extract_location(self, user_query: str) -> str:
        """Extract location from user query using LLM.
        
        Args:
            user_query: The user's input query
            
        Returns:
            str: Extracted location string in "City, Country" format
        """
        if not self.groq_api_key:
            return "Unknown"
        
        print(f"Using Groq model: {self.model_name} for determining location")
        llm = ChatGroq(
            api_key=self.groq_api_key, 
            model=self.model_name, 
            temperature=self.location_temperature
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Extract the location from the user's query. Return only the location name in the format "City, Country" or "City, State, Country". 
            If no clear location is mentioned, return "Unknown".
            Examples:
            - "What's the weather in Paris?" -> "Paris, France"
            - "Tell me about New York" -> "New York, USA"
            - "What's happening in Tokyo tonight?" -> "Tokyo, Japan"
            - "How's the weather?" -> "Unknown"
            """),
            ("user", "{query}")
        ])
        
        chain = prompt | llm
        response = chain.invoke({"query": user_query})
        return response.content.strip()
    
    def classify_destination_intent(self, user_query: str) -> bool:
        """Classify whether the query is asking about a destination/place.
        
        Returns True if the user is asking about a city/place/travel info,
        otherwise False.
        """
        if not self.groq_api_key:
            # Without LLM, default to True to preserve existing flow
            return True
        llm = ChatGroq(
            api_key=self.groq_api_key,
            model=self.model_name,
            temperature=0
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You classify user queries. Answer strictly with YES or NO.
Is the user asking about a destination (city/place) or travel-related info about a specific location?
Examples considered YES: weather in Paris, events in Tokyo, tell me about New York.
Examples considered NO: math questions, coding help, generic chit-chat, unrelated tasks.
Answer only YES or NO."""),
            ("user", "{query}")
        ])
        chain = prompt | llm
        resp = chain.invoke({"query": user_query})
        text = (resp.content or "").strip().lower()
        return text.startswith("y")

    def general_chat(self, user_query: str) -> str:
        """Provide a direct response to a non-destination query."""
        if not self.groq_api_key:
            return "I'm set up for destination questions. Please provide a location-related query."
        llm = ChatGroq(
            api_key=self.groq_api_key,
            model=self.model_name,
            temperature=0.5
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a concise helpful assistant. Answer the user's question directly."),
            ("user", "{query}")
        ])
        chain = prompt | llm
        resp = chain.invoke({"query": user_query})
        return resp.content
    
    def generate_report(self, context: str) -> str:
        """Generate a comprehensive markdown report using LLM.
        
        Args:
            context: Formatted context string with all destination data
            
        Returns:
            str: Generated markdown report
        """
        if not self.groq_api_key:
            return "LLM service not available"
        
        llm = ChatGroq(
            api_key=self.groq_api_key, 
            model=self.model_name, 
            temperature=self.report_temperature
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a travel and destination expert. Create a beautiful, comprehensive markdown report about a destination using the provided information.

            Format your response as a well-structured markdown document with:
            - A compelling title with emoji
            - Executive summary section
            - Weather section with current conditions and recommendations
            - Local time and timezone info
            - Recent news highlights (if available)
            - Upcoming events and activities (if available)
            - Travel tips and recommendations based on the data
            - Use emojis, headers, bullet points, and formatting to make it engaging
            - Keep it informative but conversational
            - Include practical advice based on weather and local conditions
            """),
            ("user", """Create a destination report using this information:

            {context}

            Make it engaging and useful for someone planning to visit or currently in this location.""")
        ])
        
        chain = prompt | llm
        response = chain.invoke({"context": context})
        return response.content
