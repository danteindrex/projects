import re
import bleach
import html
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, validator
from app.core.logging import log_event


class InputSanitizer:
    """Centralized input sanitization and validation"""
    
    # Allowed HTML tags for rich text (very restrictive)
    ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li']
    ALLOWED_ATTRIBUTES = {}
    
    # Common malicious patterns
    MALICIOUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',                # JavaScript protocol
        r'vbscript:',                 # VBScript protocol
        r'onload=',                   # Event handlers
        r'onerror=',
        r'onclick=',
        r'onmouseover=',
        r'<iframe[^>]*>.*?</iframe>', # Iframes
        r'<object[^>]*>.*?</object>', # Objects
        r'<embed[^>]*>',              # Embeds
    ]
    
    @classmethod
    def sanitize_html(cls, text: str) -> str:
        """Sanitize HTML content"""
        if not text:
            return ""
        
        try:
            # Remove malicious patterns first
            for pattern in cls.MALICIOUS_PATTERNS:
                text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
            
            # Use bleach to clean HTML
            cleaned = bleach.clean(
                text, 
                tags=cls.ALLOWED_TAGS,
                attributes=cls.ALLOWED_ATTRIBUTES,
                strip=True
            )
            
            return cleaned
            
        except Exception as e:
            log_event("html_sanitization_error", error=str(e), input_text=text[:100])
            # Fallback to HTML escaping
            return html.escape(text)
    
    @classmethod
    def sanitize_text(cls, text: str, max_length: int = 10000) -> str:
        """Sanitize plain text input"""
        if not text:
            return ""
        
        try:
            # Truncate if too long
            if len(text) > max_length:
                text = text[:max_length]
                log_event("text_truncated", original_length=len(text), max_length=max_length)
            
            # Remove null bytes and control characters
            text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
            
            # Escape HTML entities
            text = html.escape(text)
            
            return text.strip()
            
        except Exception as e:
            log_event("text_sanitization_error", error=str(e), input_text=text[:100])
            return ""
    
    @classmethod
    def sanitize_email(cls, email: str) -> str:
        """Sanitize email address"""
        if not email:
            return ""
        
        # Basic email sanitization
        email = email.strip().lower()
        
        # Remove dangerous characters
        email = re.sub(r'[<>"\'\\\x00-\x1f\x7f-\x9f]', '', email)
        
        return email
    
    @classmethod
    def sanitize_username(cls, username: str) -> str:
        """Sanitize username"""
        if not username:
            return ""
        
        # Allow only alphanumeric, underscore, dash, and dot
        username = re.sub(r'[^a-zA-Z0-9._-]', '', username)
        
        # Limit length
        if len(username) > 50:
            username = username[:50]
        
        return username.strip()
    
    @classmethod
    def validate_sql_injection(cls, text: str) -> bool:
        """Check for SQL injection patterns"""
        if not text:
            return True
        
        sql_patterns = [
            r"('|(\\')|(;|\\x3b)|(--|(\\x2d){2})|(\/\*|\*\/))",  # SQL metacharacters
            r"(union|select|insert|delete|update|drop|create|alter|exec|execute)",  # SQL keywords
            r"(script|javascript|vbscript|onload|onerror|onclick)",  # Script injection
        ]
        
        text_lower = text.lower()
        for pattern in sql_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                log_event("sql_injection_attempt_detected", pattern=pattern, input_text=text[:100])
                return False
        
        return True
    
    @classmethod
    def sanitize_json_input(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize JSON input"""
        if not isinstance(data, dict):
            return {}
        
        sanitized = {}
        for key, value in data.items():
            # Sanitize keys
            clean_key = cls.sanitize_text(str(key), max_length=100)
            
            # Sanitize values based on type
            if isinstance(value, str):
                clean_value = cls.sanitize_text(value)
            elif isinstance(value, dict):
                clean_value = cls.sanitize_json_input(value)
            elif isinstance(value, list):
                clean_value = [cls.sanitize_text(str(item)) if isinstance(item, str) else item for item in value]
            else:
                clean_value = value
            
            sanitized[clean_key] = clean_value
        
        return sanitized


class ValidationRules:
    """Common validation rules"""
    
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9._-]{3,50}$')
    PASSWORD_PATTERN = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$')  # Min 8 chars, letter + digit
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """Validate email format"""
        if not email or len(email) > 254:  # RFC 5321 limit
            return False
        return bool(cls.EMAIL_PATTERN.match(email))
    
    @classmethod
    def validate_username(cls, username: str) -> bool:
        """Validate username format"""
        if not username:
            return False
        return bool(cls.USERNAME_PATTERN.match(username))
    
    @classmethod
    def validate_password(cls, password: str) -> bool:
        """Validate password strength"""
        if not password or len(password) < 8:
            return False
        return bool(cls.PASSWORD_PATTERN.match(password))
    
    @classmethod
    def validate_text_length(cls, text: str, min_length: int = 1, max_length: int = 1000) -> bool:
        """Validate text length"""
        if not text:
            return min_length == 0
        return min_length <= len(text) <= max_length
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """Validate URL format"""
        if not url:
            return False
        
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return bool(url_pattern.match(url))


# Pydantic models with validation
class ValidatedUserInput(BaseModel):
    """Validated user input model"""
    email: str
    username: str
    password: str
    full_name: Optional[str] = None
    
    @validator('email')
    def validate_email(cls, v):
        v = InputSanitizer.sanitize_email(v)
        if not ValidationRules.validate_email(v):
            raise ValueError('Invalid email format')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        v = InputSanitizer.sanitize_username(v)
        if not ValidationRules.validate_username(v):
            raise ValueError('Username must be 3-50 characters, alphanumeric with ._- allowed')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if not ValidationRules.validate_password(v):
            raise ValueError('Password must be at least 8 characters with letters and numbers')
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        if v:
            v = InputSanitizer.sanitize_text(v, max_length=100)
            if not ValidationRules.validate_text_length(v, min_length=0, max_length=100):
                raise ValueError('Full name must be under 100 characters')
        return v


class ValidatedChatInput(BaseModel):
    """Validated chat input model"""
    message: str
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('message')
    def validate_message(cls, v):
        v = InputSanitizer.sanitize_text(v, max_length=5000)
        if not ValidationRules.validate_text_length(v, min_length=1, max_length=5000):
            raise ValueError('Message must be 1-5000 characters')
        
        if not InputSanitizer.validate_sql_injection(v):
            raise ValueError('Invalid message content')
        
        return v
    
    @validator('metadata')
    def validate_metadata(cls, v):
        if v:
            v = InputSanitizer.sanitize_json_input(v)
        return v


class ValidatedIntegrationInput(BaseModel):
    """Validated integration input model"""
    name: str
    integration_type: str
    config: Dict[str, Any]
    
    @validator('name')
    def validate_name(cls, v):
        v = InputSanitizer.sanitize_text(v, max_length=100)
        if not ValidationRules.validate_text_length(v, min_length=1, max_length=100):
            raise ValueError('Integration name must be 1-100 characters')
        return v
    
    @validator('integration_type')
    def validate_type(cls, v):
        allowed_types = ['jira', 'zendesk', 'salesforce', 'github', 'custom']
        if v not in allowed_types:
            raise ValueError(f'Integration type must be one of: {allowed_types}')
        return v
    
    @validator('config')
    def validate_config(cls, v):
        v = InputSanitizer.sanitize_json_input(v)
        
        # Validate URLs in config
        if 'endpoint' in v and not ValidationRules.validate_url(v['endpoint']):
            raise ValueError('Invalid endpoint URL')
        
        return v


# Middleware function for request sanitization
def sanitize_request_data(data: Any) -> Any:
    """Middleware function to sanitize request data"""
    if isinstance(data, dict):
        return InputSanitizer.sanitize_json_input(data)
    elif isinstance(data, str):
        return InputSanitizer.sanitize_text(data)
    elif isinstance(data, list):
        return [sanitize_request_data(item) for item in data]
    else:
        return data