"""
Encoding detection and handling utilities for file processing.
"""
import logging
import chardet
from typing import Tuple, Optional, BinaryIO, TextIO
import io

logger = logging.getLogger(__name__)

class EncodingDetector:
    """Utility class for detecting and handling file encodings."""
    
    # Common encodings to try in order of preference
    COMMON_ENCODINGS = [
        'utf-8',
        'windows-1252',  # Common Windows encoding
        'iso-8859-1',    # Latin-1
        'cp1252',        # Another Windows encoding variant
        'utf-16',        # Unicode with BOM
        'ascii'          # Plain ASCII
    ]
    
    @staticmethod
    def detect_encoding(file_stream: BinaryIO, sample_size: int = 10000) -> Tuple[str, float]:
        """
        Detect the encoding of a file stream using chardet.
        
        Args:
            file_stream: Binary file stream to analyze
            sample_size: Number of bytes to read for detection
            
        Returns:
            Tuple of (encoding_name, confidence_score)
        """
        # Save current position
        original_position = file_stream.tell()
        
        try:
            # Read sample for detection
            file_stream.seek(0)
            raw_data = file_stream.read(sample_size)
            
            # Reset to original position
            file_stream.seek(original_position)
            
            if not raw_data:
                logger.warning("Empty file provided for encoding detection")
                return 'utf-8', 0.0
            
            # Use chardet to detect encoding
            detection_result = chardet.detect(raw_data)
            
            if detection_result and detection_result['encoding']:
                encoding = detection_result['encoding'].lower()
                confidence = detection_result['confidence']
                
                logger.info(f"Detected encoding: {encoding} (confidence: {confidence:.2%})")
                return encoding, confidence
            else:
                logger.warning("Chardet could not detect encoding, falling back to utf-8")
                return 'utf-8', 0.0
                
        except Exception as e:
            logger.error(f"Error during encoding detection: {str(e)}")
            # Reset position and return default
            file_stream.seek(original_position)
            return 'utf-8', 0.0
    
    @staticmethod
    def create_text_stream_with_encoding(file_stream: BinaryIO, target_encoding: str = None, 
                                       use_detection: bool = True) -> Tuple[TextIO, str]:
        """
        Create a text stream with proper encoding handling.
        
        Args:
            file_stream: Binary file stream
            target_encoding: Specific encoding to use (optional)
            use_detection: Whether to use auto-detection if target_encoding fails
            
        Returns:
            Tuple of (text_stream, actual_encoding_used)
        """
        original_position = file_stream.tell()
        
        # If specific encoding is requested, try it first
        if target_encoding:
            try:
                file_stream.seek(0)
                text_stream = io.TextIOWrapper(file_stream, encoding=target_encoding)
                # Test read a few lines to validate encoding
                test_lines = []
                for _ in range(5):
                    try:
                        line = text_stream.readline()
                        if not line:
                            break
                        test_lines.append(line)
                    except UnicodeDecodeError:
                        # Encoding failed, need to try another
                        text_stream.close()
                        file_stream.seek(original_position)
                        raise UnicodeDecodeError("Test encoding failed", b"", 0, 1, "")
                
                # Reset to beginning and return working stream
                file_stream.seek(0)
                text_stream = io.TextIOWrapper(file_stream, encoding=target_encoding)
                logger.info(f"Successfully using requested encoding: {target_encoding}")
                return text_stream, target_encoding
                
            except (UnicodeDecodeError, LookupError) as e:
                logger.warning(f"Requested encoding {target_encoding} failed: {str(e)}")
                file_stream.seek(original_position)
        
        # Auto-detect encoding if requested or if target_encoding failed
        if use_detection:
            detected_encoding, confidence = EncodingDetector.detect_encoding(file_stream)
            
            # If confidence is high enough, try detected encoding
            if confidence > 0.7:
                try:
                    file_stream.seek(0)
                    text_stream = io.TextIOWrapper(file_stream, encoding=detected_encoding)
                    # Test read to validate
                    test_line = text_stream.readline()
                    file_stream.seek(0)
                    text_stream = io.TextIOWrapper(file_stream, encoding=detected_encoding)
                    logger.info(f"Using detected encoding: {detected_encoding}")
                    return text_stream, detected_encoding
                except (UnicodeDecodeError, LookupError) as e:
                    logger.warning(f"Detected encoding {detected_encoding} failed: {str(e)}")
                    file_stream.seek(original_position)
        
        # Try common encodings as fallback
        for encoding in EncodingDetector.COMMON_ENCODINGS:
            try:
                file_stream.seek(0)
                text_stream = io.TextIOWrapper(file_stream, encoding=encoding)
                # Test read to validate encoding works
                test_line = text_stream.readline()
                file_stream.seek(0)
                text_stream = io.TextIOWrapper(file_stream, encoding=encoding)
                logger.info(f"Using fallback encoding: {encoding}")
                return text_stream, encoding
                
            except (UnicodeDecodeError, LookupError):
                continue
        
        # Last resort: use utf-8 with error handling
        file_stream.seek(0)
        text_stream = io.TextIOWrapper(file_stream, encoding='utf-8', errors='replace')
        logger.warning("Using UTF-8 with error replacement as last resort")
        return text_stream, 'utf-8-replace'
    
    @staticmethod
    def safe_read_csv_with_encoding(file_stream: BinaryIO, 
                                  preferred_encoding: str = None) -> Tuple[TextIO, str, Optional[str]]:
        """
        Safely read a CSV file with automatic encoding detection and handling.
        
        Args:
            file_stream: Binary file stream
            preferred_encoding: Preferred encoding to try first
            
        Returns:
            Tuple of (text_stream, encoding_used, error_message)
        """
        try:
            text_stream, encoding_used = EncodingDetector.create_text_stream_with_encoding(
                file_stream, 
                target_encoding=preferred_encoding,
                use_detection=True
            )
            
            logger.info(f"Successfully created text stream with encoding: {encoding_used}")
            return text_stream, encoding_used, None
            
        except Exception as e:
            error_msg = f"Failed to create text stream with any encoding: {str(e)}"
            logger.error(error_msg)
            return None, None, error_msg
    
    @staticmethod
    def validate_encoding_support(encoding_name: str) -> bool:
        """
        Validate if an encoding is supported by the system.
        
        Args:
            encoding_name: Name of the encoding to check
            
        Returns:
            True if encoding is supported, False otherwise
        """
        try:
            # Try to encode/decode a test string
            test_string = "Test encoding validation àáâãäåæçèéêë"
            test_string.encode(encoding_name)
            return True
        except (LookupError, TypeError):
            return False
    
    @staticmethod
    def get_encoding_info(encoding_name: str) -> dict:
        """
        Get information about a specific encoding.
        
        Args:
            encoding_name: Name of the encoding
            
        Returns:
            Dictionary with encoding information
        """
        info = {
            'name': encoding_name,
            'supported': EncodingDetector.validate_encoding_support(encoding_name),
            'description': 'Unknown encoding'
        }
        
        # Add descriptions for common encodings
        descriptions = {
            'utf-8': 'Unicode (UTF-8) - Universal encoding',
            'windows-1252': 'Windows Western European encoding',
            'iso-8859-1': 'Latin-1 Western European encoding',
            'cp1252': 'Windows Code Page 1252',
            'ascii': 'Basic ASCII encoding',
            'utf-16': 'Unicode UTF-16 with BOM'
        }
        
        if encoding_name.lower() in descriptions:
            info['description'] = descriptions[encoding_name.lower()]
        
        return info 