import os
from typing import Dict, Any
import json
import base64
from io import BytesIO
import httpx
import logging

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

    async def analyze_food_with_claude(self, food_description: str) -> Dict[str, Any]:
        """Analyze food using Claude."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=self.headers,
                    json={
                        "model": "claude-3-5-sonnet-20241022",
                        "max_tokens": 1024,
                        "messages": [
                            {
                                "role": "user",
                                "content": f"""As a nutrition expert, analyze this food description and provide:
                                {food_description}
                                
                                Please provide:
                                1. Estimated calories
                                2. Protein (g)
                                3. Carbohydrates (g)
                                4. Fats (g)
                                5. Brief nutritional analysis
                                
                                Format the response as a JSON object with these keys: calories, protein, carbs, fats, analysis.
                                Only return the JSON object, no additional text."""
                            }
                        ]
                    }
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Claude API response: {result}")
                return json.loads(result['content'][0]['text'])
        except Exception as e:
            logger.error(f"Claude analysis failed: {str(e)}")
            if 'response' in locals():
                logger.error(f"Claude API error response: {response.text}")
            return {"error": f"Claude analysis failed: {str(e)}"}

    async def analyze_food_image(self, image_data: bytes) -> Dict[str, Any]:
        """Analyze food from an image using Claude."""
        try:
            # Convert image to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            logger.info("Image converted to base64 successfully")
            
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 1024,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """As a nutrition expert, analyze this food image and provide:
                                    1. A detailed description of what you see
                                    2. Estimated calories
                                    3. Protein (g)
                                    4. Carbohydrates (g)
                                    5. Fats (g)
                                    6. Brief nutritional analysis
                                    
                                    Format the response as a JSON object with these keys: description, calories, protein, carbs, fats, analysis.
                                    Only return the JSON object, no additional text."""
                                },
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": base64_image
                                    }
                                }
                            ]
                        }
                    ],
                    "system": "You are a nutrition expert. Analyze food images and provide detailed nutritional information in JSON format."
                }
                
                logger.info("Sending request to Claude API...")
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0  # Increase timeout for image processing
                )
                
                if response.status_code != 200:
                    error_data = response.json()
                    error_msg = f"API request failed with status {response.status_code}: {error_data.get('error', {}).get('message', response.text)}"
                    logger.error(error_msg)
                    
                    # Fallback: Try to analyze the image as text
                    logger.info("Attempting fallback text analysis...")
                    try:
                        # First, get a description of the image
                        desc_payload = {
                            "model": "claude-3-sonnet-20240229",
                            "max_tokens": 1024,
                            "messages": [
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": "Please describe what food you see in this image in detail."
                                        },
                                        {
                                            "type": "image",
                                            "source": {
                                                "type": "base64",
                                                "media_type": "image/jpeg",
                                                "data": base64_image
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                        
                        desc_response = await client.post(
                            "https://api.anthropic.com/v1/messages",
                            headers=self.headers,
                            json=desc_payload,
                            timeout=30.0
                        )
                        
                        if desc_response.status_code == 200:
                            description = desc_response.json()['content'][0]['text']
                            logger.info("Got image description, analyzing as text...")
                            
                            # Now analyze the description
                            return await self.analyze_food_with_claude(description)
                    except Exception as fallback_error:
                        logger.error(f"Fallback analysis failed: {str(fallback_error)}")
                    
                    return {"error": error_msg}
                
                result = response.json()
                logger.info("Received response from Claude API")
                
                try:
                    parsed_result = json.loads(result['content'][0]['text'])
                    logger.info("Successfully parsed JSON response")
                    return parsed_result
                except json.JSONDecodeError as e:
                    error_msg = f"Failed to parse JSON response: {str(e)}\nResponse content: {result['content'][0]['text']}"
                    logger.error(error_msg)
                    return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"Image analysis failed: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    async def get_combined_analysis(self, food_description: str) -> Dict[str, Any]:
        """Get analysis from Claude."""
        result = await self.analyze_food_with_claude(food_description)
        
        if "error" in result:
            return result
            
        return {
            "calories": result["calories"],
            "protein": result["protein"],
            "carbs": result["carbs"],
            "fats": result["fats"],
            "analysis": result.get("analysis", "No detailed analysis available")
        }

    async def get_image_analysis(self, image_data: bytes) -> Dict[str, Any]:
        """Get analysis from image."""
        result = await self.analyze_food_image(image_data)
        
        if "error" in result:
            return result
            
        return {
            "description": result.get("description", "No description available"),
            "calories": result["calories"],
            "protein": result["protein"],
            "carbs": result["carbs"],
            "fats": result["fats"],
            "analysis": result.get("analysis", "No detailed analysis available")
        } 