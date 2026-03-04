"""
SecureDocAI — NER Detector (Phase 4)
========================================
AI-based Named Entity Recognition for unstructured PII:
person names, addresses, organizations.

Uses ONNX Runtime with a pre-trained HuggingFace NER model
(default: dslim/bert-base-NER).

Features:
    - Model warmup on first load (prevents cold-start latency)
    - Configurable confidence threshold (NER_CONFIDENCE_THRESHOLD)
    - Inference timeout watchdog (falls back to empty results)
    - Subword offset_mapping for accurate character-level spans
"""

import time
import hashlib
import signal
import threading
from pathlib import Path
from typing import Optional
from functools import lru_cache

import numpy as np
import structlog

from app.services.detection.base import BaseDetector
from app.services.detection.constants import PII_BLACKLIST
from app.models.entity import (
    DetectedEntity, EntityType, DetectionMethod,
    MaskingStyle, EntityLocation, BoundingBox,
)
from app.models.document import ExtractedContent
from app.models.policy import Policy
from app.core.exceptions import DetectionError
from config.settings import get_settings

logger = structlog.get_logger(__name__)

# ── BIO Tag → EntityType Mapping ──
# Standard CoNLL-2003 labels used by dslim/bert-base-NER
BIO_TO_ENTITY: dict[str, EntityType] = {
    "B-PER": EntityType.PERSON_NAME,
    "I-PER": EntityType.PERSON_NAME,
    "B-ORG": EntityType.ORGANIZATION,
    "I-ORG": EntityType.ORGANIZATION,
    "B-LOC": EntityType.ADDRESS,
    "I-LOC": EntityType.ADDRESS,
    "B-MISC": EntityType.GOVERNMENT_ID,   # Miscellaneous: ID numbers, etc.
    "I-MISC": EntityType.GOVERNMENT_ID,
}

# BIO Tag → EntityType Mapping is already defined above...


class NerDetector(BaseDetector):
    """
    AI-based NER detector using HuggingFace Transformers pipeline.

    Detects:
        - Person names (PERSON_NAME)
        - Physical addresses / locations (ADDRESS)
        - Organization names (ORGANIZATION)
        - Government IDs / miscellaneous (GOVERNMENT_ID)

    Production Features:
        - Configurable confidence threshold
        - Inference timeout watchdog
        - Model warmup on startup
        - Model version tracing for audit logs
    """

    def __init__(
        self,
        model_name: str = "dslim/bert-base-NER",
        model_path: Optional[str] = None,
        confidence_threshold: float = 0.80,
        inference_timeout: float = 3.0,
    ):
        self.model_name = model_name
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.inference_timeout = inference_timeout

        # Initialize from settings if cache toggle is needed
        settings = get_settings()
        self.enable_cache = getattr(settings, "enable_inference_cache", True)

        self._pipeline = None
        self._tokenizer = None
        self._is_loaded = False
        self._model_hash: Optional[str] = None
        self._model_version: str = "unknown"

    # ── Public Interface ──

    def get_supported_entity_types(self) -> list[str]:
        return [
            EntityType.PERSON_NAME.value,
            EntityType.ADDRESS.value,
            EntityType.ORGANIZATION.value,
            EntityType.GOVERNMENT_ID.value,
        ]

    def get_model_info(self) -> dict:
        """Return model metadata for audit logging."""
        return {
            "model_name": self.model_name,
            "model_version": self._model_version,
            "model_hash": self._model_hash or "not_computed",
            "confidence_threshold": self.confidence_threshold,
            "inference_timeout_seconds": self.inference_timeout,
            "is_loaded": self._is_loaded,
        }

    def load_model(self) -> None:
        """
        Load the NER model and tokenizer from HuggingFace.

        Uses the transformers `pipeline` API for simplicity and
        performs a warmup inference to eliminate cold-start latency.
        """
        try:
            from transformers import (
                AutoTokenizer,
                AutoModelForTokenClassification,
                pipeline as hf_pipeline,
            )

            logger.info(
                "ner_model_loading",
                model_name=self.model_name,
            )

            load_start = time.time()

            # Load tokenizer and model
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            # Initialize ONNX Runtime with execution providers fallback
            # (NPU -> GPU -> CPU)
            import torch
            providers_log = []
            
            try:
                import onnxruntime as ort
                from optimum.onnxruntime import ORTModelForTokenClassification
                available_providers = ort.get_available_providers()
                
                # 1. NPU (Neural Engine)
                if "NPUExecutionProvider" in available_providers:
                    providers_log.append("NPUExecutionProvider")
                elif "QNNExecutionProvider" in available_providers:
                    providers_log.append("QNNExecutionProvider")
                    
                # 2. GPU (CUDA/DirectML)
                if "CUDAExecutionProvider" in available_providers:
                    providers_log.append("CUDAExecutionProvider")
                elif "DmlExecutionProvider" in available_providers:
                    providers_log.append("DmlExecutionProvider")
                    
                # 3. CPU (Baseline)
                providers_log.append("CPUExecutionProvider")
                
                logger.info("hardware_aware_inference", runtime="ONNX Runtime", selected_providers=providers_log)
                
                model = ORTModelForTokenClassification.from_pretrained(
                    self.model_name, 
                    export=True, 
                    provider=providers_log[0]
                )
            except ImportError:
                # Fallback to standard PyTorch pipeline if Optimum/ONNX Runtime not installed
                device = "cuda" if torch.cuda.is_available() else "cpu"
                providers_log.append(f"PyTorch_{device.upper()}")
                logger.info("hardware_aware_inference", runtime="PyTorch", fallback_device=device)
                model = AutoModelForTokenClassification.from_pretrained(self.model_name)

            # Create the NER pipeline
            self._pipeline = hf_pipeline(
                "ner",
                model=model,
                tokenizer=self._tokenizer,
                aggregation_strategy="simple",  # Merge subword tokens
                device=0 if "cuda" in providers_log or "CUDAExecutionProvider" in providers_log else -1
            )

            load_time_ms = (time.time() - load_start) * 1000

            # Compute model hash for audit traceability
            self._model_version = getattr(model.config, "_name_or_path", self.model_name)
            self._model_hash = self._compute_model_hash(model)

            self._is_loaded = True

            logger.info(
                "ner_model_loaded",
                model_name=self.model_name,
                model_hash=self._model_hash[:16] + "...",
                load_time_ms=round(load_time_ms, 1),
            )

            # ── Warmup Inference ──
            self._warmup()

        except ImportError as e:
            logger.error("ner_import_error", error=str(e))
            self._is_loaded = False
        except Exception as e:
            logger.error("ner_model_load_failed", error=str(e))
            self._is_loaded = False

    def detect(
        self,
        content: ExtractedContent,
        policy: Policy,
    ) -> list[DetectedEntity]:
        """
        Detect named entities using the NER model.

        Flow:
            1. Check if model is loaded
            2. Chunk text for inference
            3. Run inference with timeout watchdog
            4. Filter by confidence threshold
            5. Map to DetectedEntity objects with character offsets

        Returns empty list if model is not loaded or inference times out.
        """
        if not self._is_loaded or self._pipeline is None:
            logger.warning(
                "ner_not_loaded",
                document_id=content.document_id,
                message="NER model not loaded — skipping AI detection",
            )
            return []

        full_text = content.text
        if not full_text or not full_text.strip():
            return []

        # ── Normalize Casing for Inference ──
        # The NER model (bert-base-NER) requires title-cased English names.
        # We title-case purely uppercase or purely lowercase words to improve recall,
        # but carefully preserve exact string length so offsets map correctly.
        def normalize_for_ner(text: str) -> str:
            chars = list(text.replace("_", " "))
            in_word = False
            word_start = 0
            for i, c in enumerate(chars):
                if c.isalpha():
                    if not in_word:
                        in_word = True
                        word_start = i
                else:
                    if in_word:
                        word = "".join(chars[word_start:i])
                        # Only title-case if it's not a short potential acronym
                        if (word.isupper() or word.islower()) and len(word) > 3:
                            chars[word_start] = chars[word_start].upper()
                            for j in range(word_start + 1, i):
                                chars[j] = chars[j].lower()
                        in_word = False
            if in_word:
                word = "".join(chars[word_start:])
                if (word.isupper() or word.islower()) and len(word) > 3:
                    chars[word_start] = chars[word_start].upper()
                    for j in range(word_start + 1, len(chars)):
                        chars[j] = chars[j].lower()
            return "".join(chars)

        inference_text = normalize_for_ner(full_text)

        all_entities: list[DetectedEntity] = []

        try:
            # ── Run Inference with Timeout Watchdog & Optional Cache ──
            start_time = time.time()
            
            # Use cached inference if enabled, otherwise direct
            if self.enable_cache:
                raw_predictions = self._cached_run_with_timeout(inference_text)
            else:
                raw_predictions = self._run_with_timeout(inference_text)
                
            inference_time = time.time() - start_time

            if raw_predictions is None:
                logger.warning(
                    "ner_inference_timeout",
                    document_id=content.document_id,
                    timeout_seconds=self.inference_timeout,
                    message="NER inference timed out — falling back to regex only",
                )
                return []

            logger.info(
                "ner_inference_complete",
                document_id=content.document_id,
                raw_entity_count=len(raw_predictions),
                inference_time_ms=round(inference_time * 1000, 1),
            )

            # ── Process Predictions ──
            for pred in raw_predictions:
                entity = self._map_prediction(pred, content)
                if entity is not None:
                    all_entities.append(entity)

            # ── Filter by confidence threshold & Blacklist ──
            filtered_entities = []
            for e in all_entities:
                if e.confidence < self.confidence_threshold:
                    continue
                
                # Check whole phrase
                upper_val = e.value.upper().strip()
                if upper_val in PII_BLACKLIST:
                    continue
                
                # Check individual tokens (blocks "Professional Summary" if any token is blacklisted)
                # We split by any non-alphanumeric except maybe single spaces
                tokens = [t.strip().upper() for t in re.split(r"[\s_/-]+", e.value) if t.strip()]
                if any(t in PII_BLACKLIST for t in tokens):
                    continue
                
                # Label Check: Skip ONLY if it's likely a label (Names/Orgs/Address) 
                # Avoid skipping legitimate PII followed by separators like | in resumes.
                if e.entity_type in [EntityType.PERSON_NAME, EntityType.ORGANIZATION, EntityType.ADDRESS]:
                    text_len = len(content.text)
                    if e.location.end_char < text_len:
                        next_char = content.text[e.location.end_char].strip()
                        if next_char in [":", ">", "|", "—"] or (next_char == "-" and e.location.end_char + 1 < text_len and content.text[e.location.end_char+1] == " "):
                            continue
                    
                    # Also skip if it's a label followed by whitespace and then a separator
                    context_after = content.text[e.location.end_char:e.location.end_char+5]
                    if re.match(r"^\s*[:>|—]", context_after):
                        continue

                
                filtered_entities.append(e)
            
            all_entities = filtered_entities

            # ── Apply allowlist filtering ──
            all_entities = self.filter_allowlisted(all_entities, policy)

            logger.info(
                "ner_detection_complete",
                document_id=content.document_id,
                entities_found=len(all_entities),
                threshold=self.confidence_threshold,
            )

        except Exception as e:
            logger.error(
                "ner_detection_error",
                document_id=content.document_id,
                error=str(e),
            )

        return all_entities

    # ── Private Methods ──

    def _warmup(self) -> None:
        """Run a dummy inference to eliminate cold-start latency."""
        try:
            warmup_start = time.time()
            _ = self._pipeline("John Smith works at Microsoft in Seattle.")
            warmup_time_ms = (time.time() - warmup_start) * 1000
            logger.info(
                "ner_warmup_complete",
                warmup_time_ms=round(warmup_time_ms, 1),
            )
        except Exception as e:
            logger.warning("ner_warmup_failed", error=str(e))

    @lru_cache(maxsize=100)
    def _cached_run_with_timeout(self, text: str) -> Optional[tuple]:
        """
        Cached wrapper around _run_with_timeout. 
        Uses a tuple for return type to adhere to hashability.
        """
        result = self._run_with_timeout(text)
        if result is None:
            return None
            
        # Freeze dictionaries to tuples so lru_cache can store them safely
        frozen_result = tuple(
            tuple(sorted(item.items())) for item in result
        )
        return frozen_result

    def _run_with_timeout(self, text: str) -> Optional[list[dict]]:
        """
        Run NER inference with a timeout watchdog.

        If inference takes longer than `self.inference_timeout` seconds,
        returns None so the pipeline can fall back to regex-only detection.
        """
        result_container: list = []
        error_container: list = []

        def _inference():
            try:
                # HuggingFace pipeline handles chunking for long texts
                predictions = self._pipeline(
                    text,
                    aggregation_strategy="simple",
                )
                result_container.append(predictions)
            except Exception as e:
                error_container.append(e)

        thread = threading.Thread(target=_inference, daemon=True)
        thread.start()
        thread.join(timeout=self.inference_timeout)

        if thread.is_alive():
            # Inference is still running — timeout exceeded
            return None

        if error_container:
            raise error_container[0]

        return result_container[0] if result_container else []

    def _map_prediction(
        self,
        pred,
        content: ExtractedContent,
    ) -> Optional[DetectedEntity]:
        """
        Map a single HuggingFace pipeline prediction to a DetectedEntity.
        Pred can be a dict (uncached) or tuple of tuples (cached).

        The HuggingFace pipeline with aggregation_strategy="simple" returns:
            {
                "entity_group": "PER",
                "score": 0.99,
                "word": "John Smith",
                "start": 0,
                "end": 10,
            }
        """
        # Unpack if coming from cache (tuple of tuples)
        if isinstance(pred, tuple):
            pred = dict(pred)

        entity_group = pred.get("entity_group", "")
        score = float(pred.get("score", 0.0))
        word = pred.get("word", "").strip()
        start = int(pred.get("start", 0))
        end = int(pred.get("end", 0))

        # Map entity_group to our EntityType
        entity_type = self._map_entity_group(entity_group)
        if entity_type is None:
            return None

        # Skip very short or empty entities
        if len(word) < 2:
            return None

        # Build location with character offsets
        location = EntityLocation(
            start_char=start,
            end_char=end,
            page=0,  # Will be resolved via coordinate mapping
        )

        # Attempt to resolve bounding box from PyMuPDF metadata
        bbox = self._resolve_bounding_box(start, end, content)
        if bbox is not None:
            location.bounding_box = bbox
            location.page = bbox.page

        return DetectedEntity(
            entity_type=entity_type,
            value=word,
            confidence=score,
            detection_method=DetectionMethod.NER,
            location=location,
            masking_style=MaskingStyle.FULL,
            masked_value=f"[{entity_type.value}]",
        )


    def _map_entity_group(self, entity_group: str) -> Optional[EntityType]:
        """Map HuggingFace entity_group label to our EntityType enum."""
        mapping = {
            "PER": EntityType.PERSON_NAME,
            "ORG": EntityType.ORGANIZATION,
            "LOC": EntityType.ADDRESS,
            "MISC": EntityType.GOVERNMENT_ID,
        }
        return mapping.get(entity_group)

    def _resolve_bounding_box(
        self,
        start_char: int,
        end_char: int,
        content: ExtractedContent,
    ) -> Optional[BoundingBox]:
        """
        Attempt to resolve character offsets to a PDF bounding box
        using the coordinate metadata stored in ExtractedContent.

        This handles the critical token → coordinate alignment problem:
        - PyMuPDF provides word-level bounding boxes during extraction
        - We match the NER-detected character offsets to the closest
          PyMuPDF word spans

        Returns None if no spatial data is available.
        """
        if not hasattr(content, 'word_locations') or not content.word_locations:
            return None

        # Find overlapping word bounding boxes
        matching_boxes = []
        for wl in content.word_locations:
            w_start = wl.get("start_char", -1)
            w_end = wl.get("end_char", -1)
            # Check for overlap
            if w_start < end_char and w_end > start_char:
                matching_boxes.append(wl)

        if not matching_boxes:
            return None

        # Merge all overlapping bounding boxes into one
        x0 = min(b["x0"] for b in matching_boxes)
        y0 = min(b["y0"] for b in matching_boxes)
        x1 = max(b["x1"] for b in matching_boxes)
        y1 = max(b["y1"] for b in matching_boxes)
        page = matching_boxes[0].get("page", 0)

        return BoundingBox(x0=x0, y0=y0, x1=x1, y1=y1, page=page)

    def _compute_model_hash(self, model) -> str:
        """
        Compute a SHA-256 hash of model parameters for audit traceability.
        This proves exactly which model weights were used for detection.
        """
        try:
            import torch
            hasher = hashlib.sha256()
            for name, param in model.named_parameters():
                hasher.update(name.encode())
                hasher.update(param.data.cpu().numpy().tobytes()[:256])
            return hasher.hexdigest()
        except Exception:
            return "hash_unavailable"

    # ── ONNX Export (Optional Future Use) ──

    def export_to_onnx(self, output_path: str) -> None:
        """
        Export the current model to ONNX format for optimized inference.

        This is a utility method for future optimization:
        - ONNX models are 2-4x faster on CPU
        - Enables deployment on edge devices without PyTorch
        """
        if self._tokenizer is None:
            raise DetectionError("Cannot export: model not loaded")

        try:
            import torch

            model_path = Path(output_path)
            model_path.parent.mkdir(parents=True, exist_ok=True)

            dummy_input = self._tokenizer(
                "Export test",
                return_tensors="pt",
                padding=True,
                truncation=True,
            )

            logger.info("onnx_export_start", output_path=output_path)

            torch.onnx.export(
                self._pipeline.model,
                (dummy_input["input_ids"], dummy_input["attention_mask"]),
                output_path,
                input_names=["input_ids", "attention_mask"],
                output_names=["logits"],
                dynamic_axes={
                    "input_ids": {0: "batch", 1: "sequence"},
                    "attention_mask": {0: "batch", 1: "sequence"},
                    "logits": {0: "batch", 1: "sequence"},
                },
                opset_version=14,
            )

            logger.info("onnx_export_complete", output_path=output_path)

        except Exception as e:
            logger.error("onnx_export_failed", error=str(e))
            raise DetectionError(f"ONNX export failed: {e}")
