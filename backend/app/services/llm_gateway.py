"""
SecureDocAI — LLM Gateway Service
===================================
Handles transmitting sanitized documents to external LLMs
and re-injecting the real PII data into the responses locally.
"""

from typing import Dict, Any, Optional
import structlog

from app.models.document import ProcessingResult
from app.models.entity import RedactionMap

logger = structlog.get_logger(__name__)

class LLMGateway:
    """
    Acts as a secure proxy to external LLMs.
    Guarantees that sensitive data never leaves the local environment.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        # In a real app, this would be backed by Redis or memory cache with short TTLs
        self._active_mappings: Dict[str, Dict[str, str]] = {}
    
    def register_document(self, document_id: str, redaction_map: RedactionMap) -> None:
        """
        Store the {masked: original} mapping in local volatile memory.
        This enables re-identification of LLM responses later.
        """
        mapping = {}
        # Assuming the redaction map contains the masked_value and original value.
        # Format we expect: {"[PERSON_NAME_1]": "John Doe"}
        # Ensure we only map entities that were actually masked
        for entity in redaction_map.entities:
            if not entity.is_allowlisted and entity.masked_value:
                # Some detectors just output [REDACTED_EMAIL], some output [EMAIL_1]
                # For safety, we match the exact masked output literal
                mapping[entity.masked_value] = entity.value
                
        self._active_mappings[document_id] = mapping
        
        logger.info(
            "llm_map_registered", 
            document_id=document_id,
            entities_mapped=len(mapping)
        )
        
    def query(
        self, 
        document_id: str, 
        sanitized_text: str, 
        prompt: str, 
        provider: str = "mock"
    ) -> str:
        """
        Sends the sanitized_text + prompt to the LLM.
        """
        if not sanitized_text:
            return "No readable text found to send to the LLM."
            
        logger.info(
            "llm_query_sent",
            document_id=document_id,
            provider=provider,
            text_length=len(sanitized_text)
        )
        
        # Build the LLM Prompt Instruction
        full_prompt = (
            f"You are analyzing a document with sensitive data redacted.\n\n"
            f"User Request: {prompt}\n\n"
            f"Document Text:\n{sanitized_text}"
        )

        # Execute Provider
        if provider == "openai" and self.api_key:
            return self._query_openai(full_prompt)
        else:
            return self._query_mock(full_prompt)

    def re_identify(self, document_id: str, formatted_response: str) -> str:
        """
        Re-inject original string values into the LLM response.
        If the LLM outputs `[PERSON_NAME] was denied`, it becomes `John Doe was denied`.
        """
        mapping = self._active_mappings.get(document_id)
        if not mapping:
            logger.warning("llm_map_missing", document_id=document_id)
            return formatted_response
            
        reidentified = formatted_response
        
        # Very simple text replacement. This runs entirely locally.
        for masked_val, real_val in mapping.items():
            reidentified = reidentified.replace(masked_val, real_val)
            
        logger.info("llm_response_reidentified", document_id=document_id)
        return reidentified

    # ── Providers ──

    def _query_mock(self, prompt: str) -> str:
        """Mock LLM response for testing the routing mechanisms."""
        return (
            "This is a mock analysis from SecureDocAI's internal gateway.\n"
            "I noticed you wanted me to process the document text.\n\n"
            f"Your request was: '{prompt.splitlines()[2].replace('User Request: ', '')}'\n\n"
            "If the document contained [REDACTED_PERSON_NAME] or [REDACTED_EMAIL], "
            "it should be completely hidden from me!"
        )

    def _query_openai(self, prompt: str) -> str:
        """Stub for actual OpenAI API call."""
        raise NotImplementedError("OpenAI API integration requires the 'openai' python package.")
