import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

class ArgoQueryProcessor:
    def __init__(self, db_session):
        self.db = db_session
        self.param_keywords = {
            'temperature': 'TEMP', 'temp': 'TEMP', 'thermal': 'TEMP',
            'salinity': 'PSAL', 'salt': 'PSAL', 'saline': 'PSAL',
            'pressure': 'PRES', 'depth': 'PRES', 'pres': 'PRES', 'deep': 'PRES'
        }
        self.region_keywords = {
            'arabian': 'Arabian Sea', 'arabian sea': 'Arabian Sea',
            'bengal': 'Bay of Bengal', 'bay of bengal': 'Bay of Bengal',
            'indian': 'Indian Ocean', 'indian ocean': 'Indian Ocean'
        }

    def process_query(self, question: str) -> Dict[str, Any]:
        """Process a natural language query about ARGO data"""
        question_lower = question.lower()
        
        # Check for greeting
        if any(word in question_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            return self._generate_greeting_response()
        
        # Check for help request
        if any(word in question_lower for word in ['help', 'what can you do', 'capabilities']):
            return self._generate_help_response()
        
        # Extract date information
        date_info = self._extract_date_info(question)
        
        # Extract parameters
        parameters = self._extract_parameters(question)
        
        # Extract region
        region = self._extract_region(question)
        
        # Extract depth information
        depth = self._extract_depth(question)
        
        # Determine query type and process
        if any(word in question_lower for word in ['show', 'display', 'find', 'get', 'what is']):
            return self._process_data_query(question, date_info, parameters, region, depth)
        elif any(word in question_lower for word in ['compare', 'difference', 'versus', 'vs']):
            return self._process_comparison_query(question, date_info, parameters, region, depth)
        elif any(word in question_lower for word in ['list', 'all floats', 'available']):
            return self._process_listing_query()
        else:
            return self._generate_default_response()

    def _extract_date_info(self, question: str) -> Dict[str, Any]:
        """Extract date information from the question"""
        date_info = {}
        
        # Extract specific months
        month_pattern = r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})\b'
        month_matches = re.findall(month_pattern, question.lower())
        if month_matches:
            month, year = month_matches[0]
            date_info['month'] = month
            date_info['year'] = int(year)
        
        # Extract year only
        year_pattern = r'\b(202[4-5])\b'
        year_matches = re.findall(year_pattern, question)
        if year_matches and 'year' not in date_info:
            date_info['year'] = int(year_matches[0])
        
        # Extract date ranges
        range_pattern = r'\b(from|between)\s+(\w+\s+\d{4})\s+(to|and)\s+(\w+\s+\d{4})\b'
        range_matches = re.findall(range_pattern, question.lower())
        if range_matches:
            date_info['range'] = {
                'start': range_matches[0][1],
                'end': range_matches[0][3]
            }
        
        return date_info

    def _extract_parameters(self, question: str) -> List[str]:
        """Extract parameters from the question"""
        parameters = []
        question_lower = question.lower()
        
        for keyword, param in self.param_keywords.items():
            if keyword in question_lower:
                parameters.append(param)
        
        return list(set(parameters))  # Remove duplicates

    def _extract_region(self, question: str) -> Optional[str]:
        """Extract region from the question"""
        question_lower = question.lower()
        
        for keyword, region in self.region_keywords.items():
            if keyword in question_lower:
                return region
        
        return None

    def _extract_depth(self, question: str) -> Optional[int]:
        """Extract depth information from the question"""
        depth_pattern = r'\b(\d+)\s*(m|meters?|depth)\b'
        depth_matches = re.findall(depth_pattern, question.lower())
        
        if depth_matches:
            return int(depth_matches[0][0])
        
        return None

    def _process_data_query(self, question, date_info, parameters, region, depth):
        """Process data retrieval queries"""
        from models import ArgoFloat
        
        # Build query
        query = self.db.query(ArgoFloat)
        
        # Apply date filters
        if 'year' in date_info:
            year = date_info['year']
            query = query.filter(ArgoFloat.juld >= datetime(year, 1, 1))
            query = query.filter(ArgoFloat.juld < datetime(year + 1, 1, 1))
        
        # Apply region filter
        if region:
            # This would require storing region in database or calculating from coordinates
            pass
        
        # Get results
        results = query.all()
        
        if not results:
            return {
                "response": "I couldn't find any ARGO float data matching your query.",
                "map_data": None,
                "visualizations": None
            }
        
        # Prepare response based on parameters
        if parameters:
            param_text = ", ".join(parameters)
            response = f"I found {len(results)} ARGO floats with {param_text} data"
            
            if 'year' in date_info:
                response += f" from {date_info['year']}"
            if region:
                response += f" in the {region}"
            
            response += ". Here are the details:"
        else:
            response = f"I found {len(results)} ARGO floats"
            if 'year' in date_info:
                response += f" from {date_info['year']}"
            if region:
                response += f" in the {region}"
            response += ". What specific data would you like to see?"
        
        # Prepare map data
        map_data = self._generate_map_data(results)
        
        # Prepare visualizations
        visualizations = self._prepare_visualizations(results, parameters, depth)
        
        return {
            "response": response,
            "map_data": map_data,
            "visualizations": visualizations
        }

    def _process_comparison_query(self, question, date_info, parameters, region, depth):
        """Process comparison queries"""
        # This would implement comparison logic between different floats or time periods
        return {
            "response": "I can help you compare ARGO float data. Please specify what you'd like to compare (e.g., 'Compare temperature between Arabian Sea and Bay of Bengal in 2024').",
            "map_data": None,
            "visualizations": None
        }

    def _process_listing_query(self):
        """Process listing queries"""
        from models import ArgoFloat
        
        floats = self.db.query(ArgoFloat).all()
        float_count = len(floats)
        
        if float_count == 0:
            response = "I don't have any ARGO float data yet. Please upload some NetCDF files first."
        else:
            response = f"I have data from {float_count} ARGO floats. "
            
            # Get unique years
            years = set()
            for f in floats:
                if f.juld:
                    years.add(f.juld.year)
            
            if years:
                years_list = sorted(list(years))
                response += f"Data is available for the years: {', '.join(map(str, years_list))}. "
            
            response += "What specific information would you like to know?"
        
        return {
            "response": response,
            "map_data": None,
            "visualizations": None
        }

    def _generate_map_data(self, floats):
        """Generate map data for the response"""
        markers = []
        
        for f in floats:
            if f.latitude and f.longitude:
                marker = {
                    "position": [f.latitude, f.longitude],
                    "popup": f"Float {f.platform_number}",
                    "data": {
                        "platform_number": f.platform_number,
                        "date": f.juld.isoformat() if f.juld else "Unknown",
                        "parameters": f.parameters
                    }
                }
                markers.append(marker)
        
        if markers:
            # Calculate center point
            lats = [m["position"][0] for m in markers]
            lons = [m["position"][1] for m in markers]
            
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            
            return {
                "center": [center_lat, center_lon],
                "zoom": 4,
                "markers": markers
            }
        
        return None

    def _prepare_visualizations(self, floats, parameters, depth):
        """Prepare visualization data"""
        if not parameters or not floats:
            return None
        
        visualizations = {}
        
        for param in parameters:
            if param == 'TEMP':
                visualizations['temperature'] = self._prepare_temperature_viz(floats, depth)
            elif param == 'PSAL':
                visualizations['salinity'] = self._prepare_salinity_viz(floats, depth)
            elif param == 'PRES':
                visualizations['pressure'] = self._prepare_pressure_viz(floats, depth)
        
        return visualizations

    def _prepare_temperature_viz(self, floats, depth):
        """Prepare temperature visualization"""
        # Simplified visualization data
        return {
            "type": "scatter",
            "data": {
                "labels": [f.platform_number for f in floats],
                "datasets": [{
                    "label": "Surface Temperature (°C)",
                    "data": [20 + (i % 5) for i in range(len(floats))],  # Mock data
                    "backgroundColor": "rgba(255, 99, 132, 0.6)"
                }]
            },
            "options": {
                "title": {"display": True, "text": "Temperature Comparison"}
            }
        }

    def _prepare_salinity_viz(self, floats, depth):
        """Prepare salinity visualization"""
        # Similar to temperature but with different mock data
        return {
            "type": "bar",
            "data": {
                "labels": [f.platform_number for f in floats],
                "datasets": [{
                    "label": "Salinity (PSU)",
                    "data": [35.0 + (i * 0.1) for i in range(len(floats))],  # Mock data
                    "backgroundColor": "rgba(54, 162, 235, 0.6)"
                }]
            }
        }

    def _prepare_pressure_viz(self, floats, depth):
        """Prepare pressure visualization"""
        return {
            "type": "line",
            "data": {
                "labels": [f"Float {f.platform_number}" for f in floats],
                "datasets": [{
                    "label": "Pressure (dbar)",
                    "data": [500 + (i * 100) for i in range(len(floats))],  # Mock data
                    "borderColor": "rgba(75, 192, 192, 1)",
                    "fill": False
                }]
            }
        }

    def _generate_greeting_response(self):
        """Generate greeting response"""
        return {
            "response": "Hello! I'm your ARGO data assistant. I can help you explore ocean data from ARGO floats. You can ask me about temperature, salinity, pressure, or compare data between different regions or time periods.",
            "map_data": None,
            "visualizations": None
        }

    def _generate_help_response(self):
        """Generate help response"""
        help_text = """
        I can help you with ARGO float data analysis. Here's what you can ask me:

        - **Data queries**: "Show temperature in Arabian Sea in 2024", "What was the salinity at 100m depth?"
        - **Comparisons**: "Compare temperature between Arabian Sea and Bay of Bengal"
        - **List data**: "What ARGO floats do you have data for?", "Show me all floats from 2024"
        - **Specific floats**: "Show me data from float 5906221"

        You can also upload new NetCDF files using the upload button.
        """
        
        return {
            "response": help_text,
            "map_data": None,
            "visualizations": None
        }

    def _generate_default_response(self):
        """Generate default response for unrecognized queries"""
        return {
            "response": "I'm not sure how to answer that. I specialize in ARGO float data analysis. You can ask me about ocean temperature, salinity, pressure, or request comparisons between different regions or time periods.",
            "map_data": None,
            "visualizations": None
        }