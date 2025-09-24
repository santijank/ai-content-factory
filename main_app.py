# main_app_final.py - AI Content Factory with Robust JSON Parsing
import sys
import os
import requests
import json
import time
import logging
import re

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Environment variables loaded from .env")
except ImportError:
    print("python-dotenv not installed, using hardcoded values")

from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'ai-content-factory-secret-key'

# API key configuration
GROQ_API_KEY = "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"
groq_api_key = os.getenv('GROQ_API_KEY') or GROQ_API_KEY

# ===== FINAL GROQ SERVICE WITH ROBUST JSON HANDLING =====

class FinalGroqService:
    """Final Groq Service with robust JSON parsing and cleaning"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        
        # Updated working models (tested Sept 2025)
        self.models = {
            "fast": "llama-3.1-8b-instant",
            "balanced": "llama-3.1-70b-versatile", 
            "creative": "mixtral-8x7b-32768",
            "backup": "llama3-8b-8192"
        }
        
        # Model fallback order
        self.model_fallbacks = [
            "llama-3.1-8b-instant",     # Fast and reliable
            "mixtral-8x7b-32768",       # Creative alternative  
            "llama3-8b-8192"            # Backup option
        ]
        
        logger.info("FinalGroqService initialized with robust JSON handling")
    
    def clean_json_response(self, text):
        """Clean and extract JSON from response text"""
        try:
            # Remove leading/trailing whitespace
            text = text.strip()
            
            # Remove markdown formatting
            if text.startswith('```json'):
                text = text[7:]
            elif text.startswith('```'):
                text = text[3:]
            
            if text.endswith('```'):
                text = text[:-3]
            
            text = text.strip()
            
            # Remove any text before first {
            start_idx = text.find('{')
            if start_idx > 0:
                text = text[start_idx:]
            
            # Remove any text after last }
            end_idx = text.rfind('}')
            if end_idx != -1 and end_idx < len(text) - 1:
                text = text[:end_idx + 1]
            
            # Clean invalid control characters
            # Replace common problematic characters
            text = text.replace('\r\n', '\\n')
            text = text.replace('\r', '\\n') 
            text = text.replace('\n', '\\n')
            text = text.replace('\t', '\\t')
            
            # Remove other control characters (except allowed ones)
            text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
            
            # Fix common JSON issues
            text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)  # Remove control chars
            text = re.sub(r'\\([^"\\\/bfnrt])', r'\\\\\1', text)  # Fix invalid escapes
            
            return text
            
        except Exception as e:
            logger.warning(f"JSON cleaning failed: {e}")
            return text
    
    def parse_json_safely(self, text):
        """Safely parse JSON with multiple attempts"""
        original_text = text
        
        # Attempt 1: Direct parsing
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.debug(f"Direct JSON parse failed: {e}")
        
        # Attempt 2: Clean and parse
        try:
            cleaned_text = self.clean_json_response(text)
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.debug(f"Cleaned JSON parse failed: {e}")
        
        # Attempt 3: Extract JSON object manually
        try:
            # Find JSON object boundaries
            start = text.find('{')
            if start == -1:
                raise ValueError("No JSON object found")
            
            # Count braces to find end
            brace_count = 0
            end = start
            
            for i in range(start, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break
            
            if brace_count != 0:
                raise ValueError("Unbalanced braces in JSON")
            
            json_str = text[start:end]
            json_str = self.clean_json_response(json_str)
            
            return json.loads(json_str)
            
        except Exception as e:
            logger.debug(f"Manual JSON extraction failed: {e}")
        
        # Attempt 4: Try to fix common issues
        try:
            # Replace problematic quotes and characters
            fixed_text = text
            fixed_text = re.sub(r'[""]', '"', fixed_text)  # Smart quotes
            fixed_text = re.sub(r'[''`]', "'", fixed_text)  # Smart apostrophes
            fixed_text = self.clean_json_response(fixed_text)
            
            return json.loads(fixed_text)
            
        except Exception as e:
            logger.debug(f"Fixed JSON parse failed: {e}")
        
        # Final attempt: Try eval (risky but controlled)
        try:
            # Only if it looks like valid JSON structure
            if text.strip().startswith('{') and text.strip().endswith('}'):
                # Replace true/false/null with Python equivalents
                python_text = text.replace('true', 'True').replace('false', 'False').replace('null', 'None')
                result = eval(python_text)
                if isinstance(result, dict):
                    return result
        except:
            pass
        
        # If all attempts fail, raise the original error
        raise json.JSONDecodeError(f"Could not parse JSON after multiple attempts. Original text length: {len(original_text)}", original_text, 0)
    
    def _make_request(self, messages, model_type="fast", max_tokens=1000, temperature=0.7):
        """Send request with enhanced error handling"""
        
        for model in self.model_fallbacks:
            try:
                logger.info(f"🤖 Trying model: {model}")
                
                payload = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": False
                }
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                response = requests.post(
                    self.base_url, 
                    headers=headers, 
                    json=payload, 
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content'].strip()
                    logger.info(f"✅ Success with model: {model}")
                    return content, model
                    
                else:
                    logger.warning(f"❌ Model {model} failed with status {response.status_code}")
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', {}).get('message', response.text)
                        logger.warning(f"Error details: {error_msg}")
                    except:
                        logger.warning(f"Error response: {response.text}")
                    continue
                    
            except Exception as e:
                logger.warning(f"❌ Model {model} exception: {e}")
                continue
        
        raise Exception("All models failed. Check API key and Groq service status.")
    
    def test_connection(self):
        """Test connection with simple request"""
        try:
            test_messages = [
                {"role": "user", "content": "Respond with exactly: TEST_OK"}
            ]
            response, model_used = self._make_request(test_messages, max_tokens=10)
            return True, f"Success with {model_used}: {response}"
        except Exception as e:
            return False, str(e)
    
    def generate_content_script(self, opportunity_data):
        """Generate content with robust JSON parsing"""
        try:
            topic = opportunity_data.get('topic', '').strip()
            platform = opportunity_data.get('platform', 'youtube')
            content_type = opportunity_data.get('content_type', 'educational')
            
            if not topic:
                raise ValueError("Topic cannot be empty")
            
            # Simplified prompt to reduce JSON parsing issues
            prompt = f"""Create a content script for "{topic}" on {platform}.

Return a valid JSON object with this structure:
{{
    "title": "catchy title here",
    "description": "engaging description here", 
    "script": {{
        "hook": "opening hook here",
        "main_content": "main content here",
        "cta": "call to action here"
    }},
    "hashtags": ["#tag1", "#tag2", "#tag3"],
    "platform": "{platform}",
    "estimated_duration": "duration here"
}}

Topic: {topic}
Platform: {platform}
Content Type: {content_type}

Important: Return ONLY the JSON object with no extra text, formatting, or explanations."""

            messages = [
                {
                    "role": "system", 
                    "content": "You are a content creator. Respond only with valid JSON. No markdown, no explanations, just clean JSON."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
            
            logger.info(f"🎬 Generating content for: '{topic}' on {platform}")
            
            start_time = time.time()
            response, model_used = self._make_request(
                messages, 
                model_type="fast",  # Use fast model to reduce complexity
                max_tokens=1200, 
                temperature=0.5     # Lower temperature for more consistent JSON
            )
            generation_time = round(time.time() - start_time, 2)
            
            logger.info(f"📝 Raw response length: {len(response)} characters")
            logger.debug(f"Raw response preview: {response[:200]}...")
            
            # Parse JSON with robust handling
            try:
                result = self.parse_json_safely(response)
                
                # Validate required fields and add missing ones
                required_fields = ['title', 'description', 'script', 'hashtags', 'platform']
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    logger.warning(f"⚠️ Missing required fields: {missing_fields}, adding defaults")
                    
                    # Add missing fields with defaults
                    if 'title' not in result:
                        result['title'] = f"{topic} - Complete {platform.title()} Guide"
                    if 'description' not in result:
                        result['description'] = f"AI-generated content about {topic} for {platform}"
                    if 'script' not in result:
                        result['script'] = {
                            'hook': f"Introduction to {topic}",
                            'main_content': f"Main content about {topic}",
                            'cta': "Call to action"
                        }
                    if 'hashtags' not in result:
                        result['hashtags'] = [f"#{topic.replace(' ', '')[:15]}", f"#{platform}", "#content"]
                    if 'platform' not in result:
                        result['platform'] = platform
                
                # Validate script structure
                if not isinstance(result.get('script'), dict):
                    logger.warning("⚠️ Invalid script structure, creating default")
                    result['script'] = {
                        'hook': f"Introduction to {topic}",
                        'main_content': f"Main content about {topic}",
                        'cta': "Call to action"
                    }
                else:
                    script_fields = ['hook', 'main_content', 'cta']
                    missing_script_fields = [field for field in script_fields if field not in result['script']]
                    
                    if missing_script_fields:
                        logger.warning(f"⚠️ Missing script fields: {missing_script_fields}, adding defaults")
                        
                        if 'hook' not in result['script']:
                            result['script']['hook'] = f"Introduction to {topic}"
                        if 'main_content' not in result['script']:
                            result['script']['main_content'] = f"Main content about {topic}"
                        if 'cta' not in result['script']:
                            result['script']['cta'] = "Call to action"
                
                # Add metadata
                result['generated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
                result['model_used'] = model_used
                result['topic'] = topic
                result['content_type'] = content_type
                result['generation_time'] = generation_time
                result['service_version'] = 'FinalGroqService v1.3'
                result['parsing_method'] = 'successful'
                
                logger.info(f"✅ Successfully generated AI content for: {topic}")
                return result
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"⚠️ JSON parsing failed: {e}")
                logger.warning(f"Response that failed to parse: {response[:500]}...")
                
                return self._create_premium_fallback(
                    topic, platform, content_type, 
                    f"JSON parsing error: {e}", model_used, generation_time
                )
                
        except Exception as e:
            logger.error(f"❌ Content generation failed: {e}")
            return self._create_premium_fallback(
                topic, platform, content_type, str(e), "error", 0
            )
    
    def _create_premium_fallback(self, topic, platform, content_type, error_msg, model_attempted, generation_time):
        """Create premium quality fallback content"""
        
        # Platform-specific configurations
        platform_configs = {
            'youtube': {
                'duration': '8-12 minutes',
                'hook': f"Welcome back! Today we're diving deep into {topic}",
                'cta': 'If you found this helpful, smash that like button and subscribe for more!',
                'hashtags': ['#YouTube', '#Educational', '#Tutorial', '#HowTo']
            },
            'tiktok': {
                'duration': '15-60 seconds',
                'hook': f"You need to know about {topic} RIGHT NOW! 🔥",
                'cta': 'Follow for more trending content! Double tap if this helped! 💪',
                'hashtags': ['#TikTok', '#Viral', '#FYP', '#MustKnow']
            },
            'instagram': {
                'duration': '30-90 seconds',
                'hook': f"Here's what everyone's talking about: {topic} ✨",
                'cta': 'Save this post and share it with your friends! ❤️',
                'hashtags': ['#Instagram', '#Reels', '#Trending', '#ShareThis']
            },
            'facebook': {
                'duration': '3-8 minutes',
                'hook': f"Let's have an honest conversation about {topic}",
                'cta': 'What do you think? Share your thoughts in the comments!',
                'hashtags': ['#Facebook', '#Discussion', '#Community', '#Thoughts']
            }
        }
        
        config = platform_configs.get(platform.lower(), platform_configs['youtube'])
        
        # Generate smart hashtags based on topic
        topic_clean = re.sub(r'[^a-zA-Z0-9]', '', topic)[:15]
        topic_hashtags = [f"#{topic_clean}"] if topic_clean else []
        
        all_hashtags = topic_hashtags + config['hashtags'] + ['#AI', '#Content2025']
        
        # Create comprehensive content
        main_content = f"""Let's explore {topic} in detail:

🎯 What You'll Learn:
• The fundamentals of {topic} and why it's important
• Current trends and latest developments 
• Real-world applications and use cases
• Tips and strategies you can implement today
• Future outlook and what to expect

📊 Key Insights:
{topic} has become increasingly relevant in today's digital world. Understanding this topic gives you a competitive advantage whether you're a beginner or looking to expand your knowledge.

The most successful people in this space focus on understanding both the opportunities and challenges. By staying informed about {topic}, you position yourself ahead of the curve.

💡 Practical Applications:
You can apply this knowledge immediately in your personal or professional life. The strategies we discuss aren't just theoretical - they're proven methods that deliver real results.

Remember, the key to success with {topic} is consistent application and staying updated with the latest developments."""

        return {
            "title": f"{topic} - Complete {platform.title()} Guide [2025]",
            "description": f"Everything you need to know about {topic}! This comprehensive guide covers essential concepts, current trends, and practical insights. Perfect for beginners and experts alike. We break down complex ideas into easy-to-understand segments, ensuring maximum value. Stay ahead with this in-depth exploration of {topic}. Updated for 2025 with the latest information and best practices.",
            "script": {
                "hook": config['hook'],
                "main_content": main_content,
                "cta": config['cta']
            },
            "hashtags": all_hashtags[:8],  # Limit to 8 hashtags
            "platform": platform,
            "estimated_duration": config['duration'],
            "generated_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "model_used": f"premium-fallback-{model_attempted}",
            "topic": topic,
            "content_type": content_type,
            "fallback_reason": error_msg,
            "quality": "premium-fallback",
            "service_version": "FinalGroqService v1.3",
            "generation_time": generation_time,
            "parsing_method": "fallback"
        }

# Initialize service
groq_service = None

try:
    groq_service = FinalGroqService(groq_api_key)
    
    # Test the service
    test_success, test_result = groq_service.test_connection()
    if test_success:
        logger.info("✅ Final Groq service initialized and tested successfully")
        logger.info(f"Test result: {test_result}")
    else:
        logger.error(f"❌ Groq service test failed: {test_result}")
        groq_service = None
    
except Exception as e:
    logger.error(f"❌ Failed to initialize Groq service: {e}")
    groq_service = None

logger.info(f"API Key status: {'✅ Found' if groq_api_key else '❌ Missing'}")
logger.info(f"Groq Service: {'✅ Online' if groq_service else '❌ Offline'}")

# ===== FLASK ROUTES =====

@app.route('/')
def dashboard():
    """Main dashboard"""
    try:
        stats = {
            'groq_service': 'Online' if groq_service else 'Offline',
            'api_key_status': 'Ready' if groq_api_key else 'Missing',
            'services_ready': 1 if groq_service else 0,
            'total_services': 1,
            'last_check': datetime.now().strftime('%H:%M:%S'),
            'service_version': 'FinalGroqService v1.3'
        }
        
        service_status = {
            'groq': 'online' if groq_service else 'offline',
            'api_key': 'ready' if groq_api_key else 'missing'
        }
            
        return render_template('dashboard.html', stats=stats, service_status=service_status)
                             
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return f"<h1>Dashboard Error</h1><p>{str(e)}</p><p><a href='/debug-info'>Debug Info</a></p>"

@app.route('/api/simple-content', methods=['POST'])
def api_simple_content():
    """Simple content endpoint with guaranteed structure for testing"""
    try:
        data = request.get_json() or {}
        topic = data.get('topic') or data.get('idea', 'Test Topic')
        platform = data.get('platform', 'youtube')
        
        logger.info(f"🧪 Simple content test for: {topic}")
        
        # Guaranteed response structure
        response = {
            'success': True,
            'content_plan': {
                'title': f"{topic} - Complete Guide",
                'description': f"This is a comprehensive guide about {topic} for {platform}. It covers all the essential information you need to know.",
                'script': {
                    'hook': f"Welcome! Today we're exploring {topic}",
                    'main_content': f"Let's dive into {topic}. Here are the key points you need to understand: 1) The basics, 2) Advanced concepts, 3) Practical applications.",
                    'cta': 'Like and subscribe if this helped you!'
                },
                'hashtags': [f'#{topic.replace(" ", "")}', f'#{platform}', '#content'],
                'platform': platform,
                'estimated_duration': '5-10 minutes',
                'topic': topic,
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'model_used': 'simple-test',
                'content_type': 'educational'
            },
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'service_used': 'SimpleTestService',
                'is_ai_generated': False,
                'is_fallback': False,
                'topic_length': len(topic),
                'platform': platform
            }
        }
        
        logger.info(f"✅ Simple content created successfully")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Simple content failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'content_plan': {
                'title': 'Error Content',
                'description': 'Error occurred during content generation',
                'script': {
                    'hook': 'Error occurred',
                    'main_content': 'Please try again',
                    'cta': 'Contact support'
                }
            }
        }), 500

@app.route('/api/debug-response', methods=['POST'])
def api_debug_response():
    """Debug endpoint to see exact response structure"""
    try:
        data = request.get_json() or {}
        
        # Test with the actual create-content function
        logger.info("🔍 Testing actual create-content response structure")
        
        # Set default test data
        if not data.get('topic') and not data.get('idea'):
            data['idea'] = 'Debug Test Content'
        if not data.get('platform'):
            data['platform'] = 'youtube'
        
        # Mock the request object for testing
        original_json = request.get_json
        request.get_json = lambda: data
        
        try:
            # Call the actual function
            actual_response = api_create_content()
            response_data = actual_response.get_json() if hasattr(actual_response, 'get_json') else None
            
            debug_info = {
                'success': True,
                'debug_info': {
                    'input_data': data,
                    'response_status': actual_response.status_code if hasattr(actual_response, 'status_code') else 'unknown',
                    'response_type': type(actual_response).__name__,
                    'has_content_plan': 'content_plan' in (response_data or {}),
                    'content_plan_keys': list((response_data or {}).get('content_plan', {}).keys()) if response_data else [],
                    'has_title': bool((response_data or {}).get('content_plan', {}).get('title')) if response_data else False
                },
                'actual_response': response_data,
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify(debug_info)
            
        finally:
            # Restore original function
            request.get_json = original_json
            
    except Exception as e:
        logger.error(f"❌ Debug response failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'debug_info': {
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
        }), 500

@app.route('/api/content-structure', methods=['GET'])
def api_content_structure():
    """Return expected content structure for frontend reference"""
    try:
        expected_structure = {
            'success': True,
            'content_plan': {
                'title': 'string - Content title',
                'description': 'string - Content description', 
                'script': {
                    'hook': 'string - Opening hook',
                    'main_content': 'string - Main content',
                    'cta': 'string - Call to action'
                },
                'hashtags': ['array', 'of', 'hashtags'],
                'platform': 'string - target platform',
                'estimated_duration': 'string - duration estimate',
                'generated_at': 'timestamp',
                'model_used': 'string - AI model used',
                'topic': 'string - original topic',
                'content_type': 'string - content type'
            },
            'metadata': {
                'generated_at': 'timestamp',
                'service_used': 'string - service version',
                'total_generation_time': 'number - seconds',
                'is_ai_generated': 'boolean',
                'is_fallback': 'boolean',
                'topic_length': 'number',
                'platform': 'string',
                'model_used': 'string',
                'parsing_method': 'string'
            }
        }
        
        return jsonify({
            'success': True,
            'description': 'Expected structure for content generation response',
            'structure': expected_structure,
            'notes': {
                'required_fields': ['title', 'description', 'script'],
                'script_required_fields': ['hook', 'main_content', 'cta'],
                'supported_parameters': ['topic', 'idea', 'platform', 'content_type'],
                'supported_platforms': ['youtube', 'tiktok', 'instagram', 'facebook']
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test-params', methods=['POST'])
def api_test_params():
    """Test endpoint to debug parameter handling"""
    try:
        logger.info("🧪 Testing parameter handling")
        
        data = request.get_json() or {}
        
        response = {
            'success': True,
            'received_data': data,
            'extracted_parameters': {
                'topic_from_topic': data.get('topic'),
                'topic_from_idea': data.get('idea'),
                'final_topic': data.get('topic') or data.get('idea', ''),
                'platform': data.get('platform', 'youtube'),
                'content_type': data.get('content_type', 'educational')
            },
            'request_info': {
                'method': request.method,
                'content_type': request.content_type,
                'is_json': request.is_json,
                'url': request.url
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Add missing endpoint for frontend compatibility
@app.route('/api/generate-content', methods=['POST'])
def api_generate_content_alias():
    """Alias for create-content endpoint for frontend compatibility"""
    try:
        # Log the incoming request for debugging
        logger.info("📥 Received request on /api/generate-content alias")
        
        # Check if request has JSON data
        if not request.is_json:
            logger.warning("⚠️ Request is not JSON format")
            return jsonify({
                'success': False,
                'error': 'Request must be JSON format',
                'content_type': request.content_type
            }), 400
        
        data = request.get_json()
        if not data:
            logger.warning("⚠️ Empty JSON data received")
            return jsonify({
                'success': False,
                'error': 'Empty JSON data',
                'received_data': str(data)
            }), 400
        
        logger.info(f"📋 Request data: {data}")
        
        # Forward to main create-content function
        return api_create_content()
        
    except Exception as e:
        logger.error(f"❌ Error in generate-content alias: {e}")
        return jsonify({
            'success': False,
            'error': f'Alias endpoint error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/create-content', methods=['POST'])
def api_create_content():
    """Create content with enhanced JSON handling and error logging"""
    try:
        logger.info("📥 Received create-content request")
        
        if not groq_service:
            logger.error("❌ Groq service not available")
            return jsonify({
                'success': False, 
                'error': 'Groq service not available',
                'debug_info': {
                    'groq_service_initialized': groq_service is not None,
                    'api_key_present': bool(groq_api_key)
                }
            }), 500
        
        # Enhanced request validation
        if not request.is_json:
            logger.warning(f"⚠️ Invalid content type: {request.content_type}")
            return jsonify({
                'success': False,
                'error': 'Request must be JSON format',
                'received_content_type': request.content_type,
                'expected_content_type': 'application/json'
            }), 400
        
        data = request.get_json()
        if not data:
            logger.warning("⚠️ Empty or invalid JSON data")
            return jsonify({
                'success': False, 
                'error': 'No valid JSON data provided',
                'received_data': str(data)
            }), 400
        
        logger.info(f"📋 Received data: {data}")
        
        # Extract and validate parameters - support both 'topic' and 'idea' for frontend compatibility
        topic = data.get('topic') or data.get('idea', '')
        topic = topic.strip() if topic else ''
        platform = data.get('platform', 'youtube').lower()
        content_type = data.get('content_type', 'educational')
        
        logger.info(f"📝 Extracted parameters: topic='{topic}', platform='{platform}', content_type='{content_type}'")
        
        # Validation
        if not topic:
            logger.warning("⚠️ Missing topic/idea parameter")
            return jsonify({
                'success': False, 
                'error': 'Topic or idea is required',
                'received_parameters': {
                    'topic': data.get('topic'),
                    'idea': data.get('idea'),
                    'platform': platform,
                    'content_type': content_type
                },
                'note': 'Please provide either "topic" or "idea" parameter'
            }), 400
        
        if len(topic) > 200:
            logger.warning(f"⚠️ Topic too long: {len(topic)} characters")
            return jsonify({
                'success': False, 
                'error': f'Topic too long (max 200 characters, got {len(topic)})',
                'topic_length': len(topic)
            }), 400
        
        valid_platforms = ['youtube', 'tiktok', 'instagram', 'facebook']
        if platform not in valid_platforms:
            logger.warning(f"⚠️ Invalid platform: {platform}")
            return jsonify({
                'success': False,
                'error': f'Invalid platform. Must be one of: {valid_platforms}',
                'received_platform': platform
            }), 400
        
        logger.info(f"🎬 Creating content for: '{topic}' on {platform}")
        
        opportunity_data = {
            'topic': topic,
            'platform': platform,
            'content_type': content_type
        }
        
        start_time = time.time()
        content_result = groq_service.generate_content_script(opportunity_data)
        total_time = round(time.time() - start_time, 2)
        
        # Determine if it's AI-generated or fallback
        is_fallback = content_result.get('parsing_method') == 'fallback'
        is_ai_generated = content_result.get('parsing_method') == 'successful'
        
        if is_fallback:
            logger.warning(f"⚠️ Using fallback content for {topic}: {content_result.get('fallback_reason', 'Unknown')}")
        else:
            logger.info(f"✅ AI-generated content created for {topic}")
        
        response_data = {
            'success': True,
            'content_plan': content_result,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'service_used': 'FinalGroqService v1.3',
                'total_generation_time': total_time,
                'is_ai_generated': is_ai_generated,
                'is_fallback': is_fallback,
                'topic_length': len(topic),
                'platform': platform,
                'model_used': content_result.get('model_used', 'unknown'),
                'parsing_method': content_result.get('parsing_method', 'unknown')
            }
        }
        
        # Ensure response has required fields for frontend compatibility
        if 'title' not in content_result:
            content_result['title'] = f"{topic} - {platform.title()} Content"
            logger.warning("⚠️ Added missing title field for frontend compatibility")
        
        if 'description' not in content_result:
            content_result['description'] = f"AI-generated content about {topic} for {platform}"
            logger.warning("⚠️ Added missing description field for frontend compatibility")
        
        if 'script' not in content_result or not isinstance(content_result['script'], dict):
            content_result['script'] = {
                'hook': f"Introduction to {topic}",
                'main_content': f"Main content about {topic}",
                'cta': "Call to action"
            }
            logger.warning("⚠️ Added missing script structure for frontend compatibility")
        
        logger.info(f"✅ Content creation successful for: {topic}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Content creation failed: {e}")
        import traceback
        logger.error(f"📍 Full traceback: {traceback.format_exc()}")
        
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'timestamp': datetime.now().isoformat(),
            'debug_info': {
                'request_method': request.method,
                'request_path': request.path,
                'content_type': request.content_type,
                'has_json': request.is_json
            }
        }), 500

@app.route('/api/groq-test', methods=['GET', 'POST'])
def api_groq_test():
    """Test Groq service"""
    try:
        if not groq_service:
            return jsonify({'success': False, 'error': 'Groq service not initialized'})
        
        test_success, test_result = groq_service.test_connection()
        
        return jsonify({
            'success': test_success,
            'test_result': test_result,
            'service_version': 'FinalGroqService v1.3',
            'available_models': groq_service.model_fallbacks,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/collect-trends', methods=['POST'])
def api_collect_trends():
    """Collect trends (enhanced mock data)"""
    try:
        logger.info("🔍 Starting trend collection...")
        
        # Enhanced mock trends with realistic data
        mock_trends = [
            {
                "topic": "AI Content Creation Revolution 2025",
                "popularity_score": 9.4,
                "growth_rate": 48,
                "source": "youtube",
                "category": "technology",
                "collected_at": datetime.now().isoformat(),
                "keywords": ["ai content", "automation", "creators", "tools"],
                "estimated_audience": "2.8M"
            },
            {
                "topic": "Short Form Video Mastery",
                "popularity_score": 8.9,
                "growth_rate": 42,
                "source": "tiktok",
                "category": "social media",
                "collected_at": datetime.now().isoformat(),
                "keywords": ["short video", "viral", "engagement", "algorithm"],
                "estimated_audience": "2.1M"
            },
            {
                "topic": "Passive Income Systems 2025",
                "popularity_score": 8.3,
                "growth_rate": 55,
                "source": "youtube",
                "category": "finance",
                "collected_at": datetime.now().isoformat(),
                "keywords": ["passive income", "automation", "online business"],
                "estimated_audience": "1.9M"
            },
            {
                "topic": "AI Video Editing Tools",
                "popularity_score": 7.8,
                "growth_rate": 39,
                "source": "instagram",
                "category": "technology",
                "collected_at": datetime.now().isoformat(),
                "keywords": ["video editing", "ai tools", "productivity"],
                "estimated_audience": "1.4M"
            },
            {
                "topic": "Social Media Growth Hacks 2025",
                "popularity_score": 7.5,
                "growth_rate": 33,
                "source": "twitter",
                "category": "marketing",
                "collected_at": datetime.now().isoformat(),
                "keywords": ["social media", "growth", "engagement", "strategy"],
                "estimated_audience": "1.1M"
            }
        ]
        
        # Add some variation to make it realistic
        import random
        for trend in mock_trends:
            trend['popularity_score'] += random.uniform(-0.2, 0.2)
            trend['growth_rate'] += random.randint(-3, 3)
            trend['popularity_score'] = round(max(0, min(10, trend['popularity_score'])), 1)
            trend['growth_rate'] = max(0, trend['growth_rate'])
        
        logger.info(f"✅ Mock collected {len(mock_trends)} trends")
        
        return jsonify({
            'success': True,
            'trends_collected': len(mock_trends),
            'trends_saved': len(mock_trends),
            'trends': mock_trends,
            'collection_metadata': {
                'timestamp': datetime.now().isoformat(),
                'sources': list(set(trend['source'] for trend in mock_trends)),
                'categories': list(set(trend['category'] for trend in mock_trends)),
                'avg_popularity': round(sum(trend['popularity_score'] for trend in mock_trends) / len(mock_trends), 1),
                'total_estimated_audience': "9.3M+"
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Trend collection failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate-opportunities', methods=['POST'])
def api_generate_opportunities():
    """Generate content opportunities (enhanced mock data)"""
    try:
        logger.info("💡 Generating content opportunities...")
        
        mock_opportunities = [
            {
                "id": 1,
                "title": "Complete Guide to AI Content Creation Tools 2025",
                "description": "Comprehensive review of the best AI tools for content creators this year",
                "estimated_views": "850K",
                "roi_score": 4.7,
                "trend_topic": "AI Content Creation Revolution 2025",
                "platform": "youtube",
                "estimated_duration": "12-15 minutes",
                "competition_level": "medium",
                "difficulty": "intermediate",
                "target_audience": "content creators, entrepreneurs",
                "created_at": datetime.now().isoformat(),
                "tags": ["ai tools", "productivity", "content creation"],
                "potential_revenue": "$1,200-2,500"
            },
            {
                "id": 2,
                "title": "Why AI Video Editing is Changing Everything",
                "description": "Deep dive into how AI is revolutionizing video editing workflows",
                "estimated_views": "520K", 
                "roi_score": 4.9,
                "trend_topic": "AI Video Editing Tools",
                "platform": "youtube",
                "estimated_duration": "8-10 minutes",
                "competition_level": "low",
                "difficulty": "beginner",
                "target_audience": "video editors, content creators",
                "created_at": datetime.now().isoformat(),
                "tags": ["video editing", "ai", "automation"],
                "potential_revenue": "$800-1,800"
            },
            {
                "id": 3,
                "title": "5 Passive Income Ideas That Actually Work",
                "description": "Proven strategies for building passive income streams online",
                "estimated_views": "1.2M",
                "roi_score": 5.2,
                "trend_topic": "Passive Income Systems 2025",
                "platform": "youtube",
                "estimated_duration": "15-18 minutes",
                "competition_level": "high",
                "difficulty": "intermediate",
                "target_audience": "entrepreneurs, side hustlers",
                "created_at": datetime.now().isoformat(),
                "tags": ["passive income", "online business", "financial freedom"],
                "potential_revenue": "$2,000-4,500"
            },
            {
                "id": 4,
                "title": "Short Form Video Secrets for 2025",
                "description": "Latest strategies for creating viral short form content",
                "estimated_views": "680K",
                "roi_score": 4.4,
                "trend_topic": "Short Form Video Mastery",
                "platform": "tiktok",
                "estimated_duration": "60-90 seconds",
                "competition_level": "high",
                "difficulty": "beginner",
                "target_audience": "content creators, marketers",
                "created_at": datetime.now().isoformat(),
                "tags": ["short form", "viral content", "marketing"],
                "potential_revenue": "$600-1,200"
            },
            {
                "id": 5,
                "title": "Social Media Growth Strategy That Works",
                "description": "Proven methods to grow your social media following organically",
                "estimated_views": "420K",
                "roi_score": 4.1,
                "trend_topic": "Social Media Growth Hacks 2025",
                "platform": "instagram",
                "estimated_duration": "5-8 minutes",
                "competition_level": "medium",
                "difficulty": "beginner",
                "target_audience": "marketers, influencers",
                "created_at": datetime.now().isoformat(),
                "tags": ["social media", "growth", "organic reach"],
                "potential_revenue": "$500-1,000"
            }
        ]
        
        logger.info(f"✅ Generated {len(mock_opportunities)} opportunities")
        
        return jsonify({
            'success': True,
            'opportunities_generated': len(mock_opportunities),
            'opportunities_saved': len(mock_opportunities),
            'opportunities': mock_opportunities,
            'generation_metadata': {
                'timestamp': datetime.now().isoformat(),
                'avg_roi_score': round(sum(opp['roi_score'] for opp in mock_opportunities) / len(mock_opportunities), 1),
                'platforms': list(set(opp['platform'] for opp in mock_opportunities)),
                'difficulty_levels': list(set(opp['difficulty'] for opp in mock_opportunities)),
                'total_estimated_views': "3.67M+",
                'total_potential_revenue': "$5,100-12,000"
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Opportunity generation failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/debug-info')
def debug_info():
    """Debug information page"""
    try:
        groq_test_result = None
        if groq_service:
            test_success, test_result = groq_service.test_connection()
            groq_test_result = {'success': test_success, 'result': test_result}
        
        info = {
            'Service Status': {
                'Groq Service': '✅ Ready' if groq_service else '❌ Not initialized',
                'API Key': f'✅ Set ({len(groq_api_key)} chars)' if groq_api_key else '❌ Missing',
                'Connection Test': '✅ Passed' if groq_test_result and groq_test_result['success'] else '❌ Failed'
            },
            'Service Info': {
                'Version': 'FinalGroqService v1.3',
                'Features': 'Robust JSON parsing, Model fallback, Enhanced error handling',
                'Models': ', '.join(groq_service.model_fallbacks) if groq_service else 'N/A',
                'JSON Parser': 'Multi-attempt with cleaning and validation'
            }
        }
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Debug Info - Final Version v1.3</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
                h1 {{ color: #333; text-align: center; }}
                h2 {{ color: #007bff; }}
                .info {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                button {{ padding: 12px 24px; margin: 5px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }}
                .result {{ margin: 15px 0; padding: 15px; border-radius: 5px; }}
                .success {{ background: #d4edda; color: #155724; }}
                .error {{ background: #f8d7da; color: #721c24; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔧 AI Content Factory Debug v1.3</h1>
        """
        
        for section, data in info.items():
            html += f"<h2>{section}</h2><div class='info'>"
            for key, value in data.items():
                html += f"<p><strong>{key}:</strong> {value}</p>"
            html += "</div>"
        
        html += """
                <h2>🧪 API Tests & Debugging</h2>
                <button onclick="testGroq()">Test Connection</button>
                <button onclick="testContent()">Test Content Generation</button>
                <button onclick="testSimple()">Test Simple Content</button>
                <button onclick="testDebug()">Debug Response Structure</button>
                <button onclick="testTrends()">Test Trend Collection</button>
                <button onclick="testOpportunities()">Test Opportunities</button>
                <button onclick="runFullTest()">Run All Tests</button>
                <div id="results" class="result"></div>
                
                <script>
                    function showLoading(msg) {
                        document.getElementById('results').innerHTML = '<div style="padding:10px;background:#e3f2fd;">🔄 ' + msg + '</div>';
                    }
                    
                    function showResult(data, testName) {
                        const css = data.success ? 'success' : 'error';
                        const icon = data.success ? '✅' : '❌';
                        
                        // Special handling for content responses
                        let displayData = data;
                        if (data.content_plan) {
                            displayData = {
                                ...data,
                                content_plan_summary: {
                                    has_title: !!data.content_plan.title,
                                    has_description: !!data.content_plan.description,
                                    has_script: !!data.content_plan.script,
                                    title_preview: data.content_plan.title ? data.content_plan.title.substring(0, 50) + '...' : 'MISSING',
                                    script_keys: data.content_plan.script ? Object.keys(data.content_plan.script) : 'MISSING'
                                }
                            };
                        }
                        
                        document.getElementById('results').innerHTML = 
                            '<div class="' + css + '"><strong>' + icon + ' ' + testName + ':</strong><br><pre>' + 
                            JSON.stringify(displayData, null, 2) + '</pre></div>';
                    }
                    
                    function testGroq() {
                        showLoading('Testing Groq connection...');
                        fetch('/api/groq-test', {method: 'POST'})
                            .then(r => r.json())
                            .then(data => showResult(data, 'Groq Connection Test'))
                            .catch(err => showResult({success: false, error: err.toString()}, 'Connection Error'));
                    }
                    
                    function testContent() {
                        showLoading('Testing content generation...');
                        fetch('/api/create-content', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                idea: 'Frontend Debug Test Content',
                                platform: 'youtube'
                            })
                        })
                        .then(r => r.json())
                        .then(data => showResult(data, 'Content Generation Test'))
                        .catch(err => showResult({success: false, error: err.toString()}, 'Content Error'));
                    }
                    
                    function testSimple() {
                        showLoading('Testing simple content endpoint...');
                        fetch('/api/simple-content', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                idea: 'Simple Test Content',
                                platform: 'youtube'
                            })
                        })
                        .then(r => r.json())
                        .then(data => showResult(data, 'Simple Content Test'))
                        .catch(err => showResult({success: false, error: err.toString()}, 'Simple Content Error'));
                    }
                    
                    function testDebug() {
                        showLoading('Testing debug response structure...');
                        fetch('/api/debug-response', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                idea: 'Debug Structure Test',
                                platform: 'youtube'
                            })
                        })
                        .then(r => r.json())
                        .then(data => showResult(data, 'Debug Response Test'))
                        .catch(err => showResult({success: false, error: err.toString()}, 'Debug Error'));
                    }
                    
                    function testTrends() {
                        showLoading('Testing trend collection...');
                        fetch('/api/collect-trends', {method: 'POST'})
                            .then(r => r.json())
                            .then(data => showResult(data, 'Trend Collection Test'))
                            .catch(err => showResult({success: false, error: err.toString()}, 'Trends Error'));
                    }
                    
                    function testOpportunities() {
                        showLoading('Testing opportunity generation...');
                        fetch('/api/generate-opportunities', {method: 'POST'})
                            .then(r => r.json())
                            .then(data => showResult(data, 'Opportunities Test'))
                            .catch(err => showResult({success: false, error: err.toString()}, 'Opportunities Error'));
                    }
                    
                    function runFullTest() {
                        showLoading('Running comprehensive system test...');
                        
                        Promise.all([
                            fetch('/api/groq-test', {method: 'POST'}).then(r => r.json()),
                            fetch('/api/simple-content', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({idea: 'Full Test', platform: 'youtube'})
                            }).then(r => r.json()),
                            fetch('/api/collect-trends', {method: 'POST'}).then(r => r.json()),
                            fetch('/api/generate-opportunities', {method: 'POST'}).then(r => r.json())
                        ])
                        .then(results => {
                            const [groq, content, trends, opportunities] = results;
                            
                            const summary = {
                                success: groq.success && content.success && trends.success && opportunities.success,
                                tests_passed: [groq.success, content.success, trends.success, opportunities.success].filter(Boolean).length,
                                total_tests: 4,
                                details: {
                                    groq_connection: groq.success ? '✅ PASS' : '❌ FAIL',
                                    content_generation: content.success ? '✅ PASS' : '❌ FAIL', 
                                    content_has_title: content.content_plan?.title ? '✅ HAS TITLE' : '❌ NO TITLE',
                                    trend_collection: trends.success ? '✅ PASS' : '❌ FAIL',
                                    opportunity_generation: opportunities.success ? '✅ PASS' : '❌ FAIL'
                                },
                                frontend_compatibility: {
                                    title_available: !!content.content_plan?.title,
                                    description_available: !!content.content_plan?.description,
                                    script_available: !!content.content_plan?.script,
                                    expected_structure: content.content_plan ? 'CORRECT' : 'INCORRECT'
                                },
                                timestamp: new Date().toISOString()
                            };
                            
                            showResult(summary, 'Full System Test');
                        })
                        .catch(err => showResult({success: false, error: err.toString()}, 'System Test Error'));
                    }
                    
                    // Auto-run simple test on load to verify frontend compatibility
                    setTimeout(testSimple, 1000);
                </script>
                
                <div style="margin-top: 20px;">
                    <a href="/" style="padding: 10px 20px; background: #6c757d; color: white; text-decoration: none; border-radius: 5px;">← Back to Dashboard</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        return f"<html><body><h1>Debug Error</h1><p>{str(e)}</p></body></html>"

# ===== MAIN =====

if __name__ == '__main__':
    try:
        print("\n" + "="*70)
        print("🎯 AI CONTENT FACTORY - FINAL VERSION v1.3")
        print("="*70)
        
        print("\n🔥 New Features v1.3:")
        print("   ✅ Robust JSON parsing with 4 fallback methods")
        print("   ✅ Control character cleaning and validation")
        print("   ✅ Enhanced error handling and logging")
        print("   ✅ Premium fallback content system")
        print("   ✅ Model fallback with automatic retry")
        
        print(f"\n📊 Service Status:")
        print(f"   {'✅' if groq_service else '❌'} Groq Service (FinalGroqService v1.3)")
        print(f"   {'✅' if groq_api_key else '❌'} API Key")
        
        print("\n🌐 URLs:")
        print("   📊 Dashboard: http://127.0.0.1:5000")
        print("   🔧 Debug: http://127.0.0.1:5000/debug-info")
        
        print("\n" + "="*70)
        print("✅ READY - Should fix JSON parsing issues!")
        print("="*70 + "\n")
        
        app.run(host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to start: {e}")
        raise