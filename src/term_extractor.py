"""
Term Extractor Module

This module handles the extraction of professional terminology from texts and saving results.
"""
import csv
import logging
import pandas as pd

logger = logging.getLogger(__name__)

class TermExtractor:
    """Class for extracting professional terminology pairs from texts."""
    
    def __init__(self, bedrock_client, custom_prompt=None):
        """
        Initialize the term extractor.
        
        Args:
            bedrock_client (BedrockClient): Instance of BedrockClient for API calls
            custom_prompt (str, optional): Custom prompt template to use for extraction
        """
        self.bedrock_client = bedrock_client
        self.custom_prompt = custom_prompt
        logger.info("Term extractor initialized" + (" with custom prompt" if custom_prompt else ""))
        
    def extract_terms(self, chinese_text, english_text):
        """
        Extract professional terminology pairs from Chinese and English texts.
        
        Args:
            chinese_text (str): Text extracted from Chinese PDF
            english_text (str): Text extracted from English PDF
            
        Returns:
            list: List of dictionaries containing term pairs
        """
        logger.info("Extracting professional terminology pairs")
        
        # Check if we have enough text to work with
        if not chinese_text or not chinese_text.strip():
            raise ValueError("Chinese text is empty")
        
        if not english_text or not english_text.strip():
            raise ValueError("English text is empty")
        
        # Use the Bedrock client to extract terminology pairs
        try:
            # Pass custom prompt to the BedrockClient if available
            terminology_pairs = self.bedrock_client.extract_professional_terms(
                chinese_text, english_text, custom_prompt=self.custom_prompt
            )
            
            # Validate the returned data structure
            if not isinstance(terminology_pairs, list):
                logger.error(f"Expected list but got {type(terminology_pairs)}")
                raise ValueError("API returned invalid data format (not a list)")
            
            for i, pair in enumerate(terminology_pairs):
                if not isinstance(pair, dict):
                    logger.error(f"Item {i} is not a dictionary: {pair}")
                    raise ValueError(f"API returned invalid item format at index {i}")
                
                required_keys = ["name", "ZH_CN", "EN_US"]
                for key in required_keys:
                    if key not in pair:
                        logger.error(f"Item {i} missing required key '{key}': {pair}")
                        raise ValueError(f"API returned item missing required key '{key}' at index {i}")
            
            logger.info(f"Successfully extracted {len(terminology_pairs)} terminology pairs")
            return terminology_pairs
            
        except Exception as e:
            logger.error(f"Error extracting terminology pairs: {str(e)}")
            raise
    
    def save_to_csv(self, terminology_pairs, output_path):
        """
        Save terminology pairs to a CSV file.
        
        Args:
            terminology_pairs (list): List of dictionaries containing term pairs
            output_path (str): Path to save the CSV file
        """
        logger.info(f"Saving {len(terminology_pairs)} terminology pairs to {output_path}")
        
        try:
            # Convert to pandas DataFrame for easier handling
            df = pd.DataFrame(terminology_pairs)
            
            # Normalize case-sensitive name columns first
            name_columns = [col for col in df.columns if col.lower() == 'name']
            if len(name_columns) > 1:
                # Keep the first non-null value from any name column
                df['name'] = df[name_columns].fillna('').apply(lambda x: next((v for v in x if v), ''), axis=1)
                # Drop the extra name columns
                df = df.drop(columns=[col for col in name_columns if col != 'name'])
            elif len(name_columns) == 1 and name_columns[0] != 'name':
                # Rename single name column to correct case
                df = df.rename(columns={name_columns[0]: 'name'})
            
            # Handle other case-sensitive columns
            for expected_col in ["ZH_CN", "EN_US"]:
                matching_cols = [col for col in df.columns if col.lower() == expected_col.lower()]
                if matching_cols:
                    if len(matching_cols) > 1:
                        # Keep the first non-null value
                        df[expected_col] = df[matching_cols].fillna('').apply(lambda x: next((v for v in x if v), ''), axis=1)
                        # Drop the extra columns
                        df = df.drop(columns=[col for col in matching_cols if col != expected_col])
                    elif matching_cols[0] != expected_col:
                        # Rename to correct case
                        df = df.rename(columns={matching_cols[0]: expected_col})
            
            # Define required columns and add missing ones with empty strings
            required_columns = ["name", "desc", "abbr", "ZH_CN", "EN_US"]
            for col in required_columns:
                if col not in df.columns:
                    logger.info(f"Adding missing column '{col}' with empty values")
                    df[col] = ""
            
            # Ensure columns are in the correct order
            df = df[required_columns]
            
            # Replace NaN values with empty strings
            df = df.fillna('')
            
            # Save to CSV with proper delimiter
            df.to_csv(output_path, index=False, encoding='utf-8-sig', sep=',')  # Use utf-8-sig for Excel compatibility
            
            logger.info(f"Successfully saved terminology pairs to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving terminology pairs to CSV: {str(e)}")
            raise
