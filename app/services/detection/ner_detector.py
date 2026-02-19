"""
SecureDocAI — NER Detector (Stub)
====================================
AI-based Named Entity Recognition for unstructured PII:
person names, addresses, organizations.

Will use ONNX Runtime with DistilBERT/DeBERTa-small in Phase 2.
"""

import structlog

from app.services.detection.base import BaseDetector
from app.models.entity import (
    DetectedEntity, EntityType, DetectionMethod,
    MaskingStyle, EntityLocation,
)
from app.models.document import ExtractedContent
from app.models.policy import Policy
from app.core.exceptions import DetectionError

logger = structlog.get_logger(__name__)


class NerDetector(BaseDetector):
    """
    AI-based NER detector using ONNX Runtime.

    Detects:
        - Person names (PERSON_NAME)
        - Physical addresses (ADDRESS)
        - Organization names (ORGANIZATION)

    Phase 2 Implementation:
        - Load ONNX model (DistilBERT/DeBERTa-small)
        - Tokenize extracted text
        - Run inference on GPU/NPU
        - Map BIO tags to entity spans
    """

    def __init__(self, model_path: str = None):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self._is_loaded = False

    def get_supported_entity_types(self) -> list[str]:
        return [
            EntityType.PERSON_NAME.value,
            EntityType.ADDRESS.value,
            EntityType.ORGANIZATION.value,
        ]

    def load_model(self) -> None:
        """
        Load the ONNX NER model and tokenizer.

        TODO (Phase 2):
            - Load ONNX model via onnxruntime.InferenceSession
            - Load tokenizer from transformers
            - Configure GPU/NPU execution provider
        """
        logger.info("ner_model_load", status="stub", model_path=self.model_path)
        self._is_loaded = True

    def detect(
        self,
        content: ExtractedContent,
        policy: Policy,
    ) -> list[DetectedEntity]:
        """
        Detect named entities using the NER model.

        TODO (Phase 2):
            1. Tokenize text with sliding window
            2. Run ONNX inference
            3. Decode BIO tags to entity spans
            4. Map character offsets to bounding boxes
            5. Apply confidence thresholds

        Currently returns empty list (stub).
        """
        logger.warning(
            "ner_detection_stub",
            document_id=content.document_id,
            message="NER detection not yet implemented — returning empty results",
        )
        return []

    def _tokenize(self, text: str) -> dict:
        """Tokenize text for ONNX inference (Phase 2)."""
        raise NotImplementedError("NER tokenization not yet implemented")

    def _decode_predictions(self, tokens: list, predictions: list) -> list[DetectedEntity]:
        """Decode model predictions to entity spans (Phase 2)."""
        raise NotImplementedError("NER prediction decoding not yet implemented")
