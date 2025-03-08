"""
AWS Bedrock Client Module

This module handles interactions with AWS Bedrock Converse API for Claude models.
"""
import json
import logging
import os
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class BedrockClient:
    """Client for interacting with AWS Bedrock Converse API."""
    
    def __init__(self, model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0", region_name=None):
        """
        Initialize the Bedrock client.
        
        Args:
            model_id (str): The ID of the Bedrock model to use
            region_name (str): AWS region name (defaults to AWS_REGION env var or 'us-east-1')
        """
        self.original_model_id = model_id
        self.region_name = region_name or os.environ.get("AWS_REGION", "us-east-1")
        
        # Map Nova model IDs to their inference profile ARNs if needed
        if "nova" in model_id.lower():
            # Extract your account ID from the environment or configuration
            # This is a placeholder - you should replace with actual logic to get your AWS account ID
            # AWS_ACCOUNT_ID should be set as an environment variable
            account_id = os.environ.get("AWS_ACCOUNT_ID", "")
            
            if account_id:
                if "nova-lite" in model_id.lower():
                    # Format: arn:aws:bedrock:[region]:[account-id]:inference-profile/[profile-name]
                    self.model_id = f"arn:aws:bedrock:{self.region_name}:{account_id}:inference-profile/nova-lite-profile"
                    logger.info(f"Using inference profile ARN for Nova Lite: {self.model_id}")
                elif "nova-pro" in model_id.lower():
                    self.model_id = f"arn:aws:bedrock:{self.region_name}:{account_id}:inference-profile/nova-pro-profile"
                    logger.info(f"Using inference profile ARN for Nova Pro: {self.model_id}")
                else:
                    # Default Nova profile
                    self.model_id = f"arn:aws:bedrock:{self.region_name}:{account_id}:inference-profile/nova-profile"
                    logger.info(f"Using default inference profile ARN for Nova: {self.model_id}")
            else:
                logger.warning("AWS_ACCOUNT_ID not set. Falling back to direct model ID, which may fail for Nova models.")
                self.model_id = model_id
        else:
            # For non-Nova models, use the model ID directly
            self.model_id = model_id
        
        logger.info(f"Initializing Bedrock client with model: {model_id} in region: {self.region_name}")
        
        try:
            # Initialize Bedrock client
            self.bedrock = boto3.client(
                service_name="bedrock-runtime",
                region_name=self.region_name
            )
            logger.info("Bedrock client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {str(e)}")
            raise
    
    def converse(self, messages, max_tokens=4096, temperature=0.0):
        """
        Call the AWS Bedrock Converse API with the provided messages.
        
        Args:
            messages (list): List of message objects with 'role' and 'content'
            max_tokens (int): Maximum number of tokens to generate
            temperature (float): Sampling temperature (0.0 = deterministic)
            
        Returns:
            dict: The model's response
        """
        logger.info(f"Calling Bedrock Converse API with {len(messages)} messages")
        
        try:
            # Create inference config
            inference_config = {
                "maxTokens": max_tokens,
                "temperature": temperature
            }
            
            # Call the Bedrock converse API for all models
            logger.info(f"Using bedrock.converse API for model: {self.model_id}")
            response = self.bedrock.converse(
                modelId=self.model_id,
                messages=messages,
                inferenceConfig=inference_config
            )
            
            # Format response to be consistent
            formatted_response = {
                "content": [
                    {"text": response["output"]["message"]["content"][0]["text"]}
                ]
            }
            
            logger.info("Successfully received response from Bedrock Converse API")
            return formatted_response
        
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            logger.error(f"AWS Bedrock API error ({error_code}): {error_message}")
            raise
        
        except Exception as e:
            logger.error(f"Error calling Bedrock Converse API: {str(e)}")
            raise

    def extract_professional_terms(self, chinese_text, english_text, custom_prompt=None):
        """
        Extract professional terminology pairs using Claude via Bedrock.
        
        Args:
            chinese_text (str): Text extracted from Chinese PDF
            english_text (str): Text extracted from English PDF
            custom_prompt (str, optional): Custom prompt template to use for extraction
            
        Returns:
            list: List of dictionaries containing term pairs
        """
        # Truncate texts if they're too long (Claude has context limitations)
        max_chars = 50000  # Conservative estimate to leave room for system message and response
        
        if len(chinese_text) > max_chars or len(english_text) > max_chars:
            logger.warning(f"Texts too long, truncating to {max_chars} characters")
            chinese_text = chinese_text[:max_chars]
            english_text = english_text[:max_chars]
        
        # Default prompt if no custom prompt is provided
        default_prompt = f"""As a professional translator and terminologist, please help extract professional terminology pairs from these parallel Chinese and English texts:

CHINESE TEXT:
{chinese_text}

ENGLISH TEXT:
{english_text}

Identify all specific professional terms and specialized vocabulary that appears in both texts.
Return the results as an XML-formatted list of term entries with these fields:
- "name": a 6-character random string (e.g., "A2B3C4", "X7Y8Z9", etc.)
- "ZH_CN": The Chinese term
- "EN_US": The corresponding English term

IMPORTANT GUIDELINES:
1. Focus on specialized terminology specific to this document's domain
2. Include only terms that appear in both texts
3. Extract ONLY professional/technical terms, not common words
4. Ensure accurate pairing between Chinese and English terms
5. Return ONLY the XML data without any other text

Return format example:
<terminology>
  <term>
    <name>A2B3C4</name>
    <ZH_CN>数据库</ZH_CN>
    <EN_US>database</EN_US>
  </term>
  <term>
    <name>X7Y8Z9</name>
    <ZH_CN>云计算</ZH_CN>
    <EN_US>cloud computing</EN_US>
  </term>
</terminology>"""

        # Use custom prompt if provided, otherwise use default
        if custom_prompt:
            logger.info("Using custom prompt for terminology extraction")
            try:
                # Try to format the custom prompt with the text placeholders
                formatted_prompt = custom_prompt.format(
                    chinese_text=chinese_text,
                    english_text=english_text
                )
            except (KeyError, ValueError):
                # If formatting fails, append the texts to the custom prompt
                logger.warning("Custom prompt formatting failed. Appending text data.")
                formatted_prompt = f"{custom_prompt}\n\nCHINESE TEXT:\n{chinese_text}\n\nENGLISH TEXT:\n{english_text}"
        else:
            formatted_prompt = default_prompt
        
        # Prepare conversation messages
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "text": formatted_prompt
                    }
                ]
            }
        ]
        
        # Call the API
        try:
            response = self.converse(messages, max_tokens=5000, temperature=0.0)
            
            # Extract the XML content from the response
            if "content" in response and len(response["content"]) > 0:
                content_text = response["content"][0].get("text", "")
                
                # Try to extract XML from the response
                import re
                import xml.etree.ElementTree as ET
                from io import StringIO
                
                # Try to extract XML from within the text (between <terminology> tags)
                xml_match = re.search(r'<terminology>.*</terminology>', content_text, re.DOTALL)
                
                if xml_match:
                    try:
                        # Parse XML and convert to list of dictionaries for compatibility
                        terminology_xml = xml_match.group(0)
                        root = ET.fromstring(terminology_xml)
                        
                        # Convert XML to list of dictionaries with normalized keys
                        terminology_list = []
                        expected_keys = {"name", "ZH_CN", "EN_US"}
                        
                        for term_elem in root.findall('term'):
                            term_dict = {}
                            for child in term_elem:
                                # Normalize key case if needed
                                key = child.tag
                                for expected_key in expected_keys:
                                    if key.lower() == expected_key.lower():
                                        key = expected_key
                                        break
                                
                                term_dict[key] = child.text
                            terminology_list.append(term_dict)
                        
                        return terminology_list
                    except ET.ParseError as e:
                        logger.error(f"Error parsing XML: {str(e)}")
                        logger.debug(f"XML content: {terminology_xml}")
                        raise ValueError(f"Failed to parse XML: {str(e)}")
                
                logger.error("Couldn't extract valid XML from the response")
                logger.debug(f"Raw response content: {content_text}")
                raise ValueError("Failed to extract valid XML from Claude's response")
            else:
                logger.error("No content in the response")
                raise ValueError("No content in Claude's response")
                
        except Exception as e:
            logger.error(f"Error extracting terminology: {str(e)}")
            raise


