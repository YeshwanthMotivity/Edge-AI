import pytest
from pathlib import Path
from PIL import Image, ImageDraw

from app.models.entity import DetectedEntity, EntityType, DetectionMethod, EntityLocation, BoundingBox, RedactionMap
from app.services.redaction.image_redactor import ImageRedactor


@pytest.fixture
def tmp_image_path(tmp_path) -> Path:
    # Create a dummy image
    img = Image.new("RGB", (800, 600), color="white")
    draw = ImageDraw.Draw(img)
    # Draw some text-like lines
    draw.rectangle([100, 100, 300, 150], fill="blue")
    
    path = tmp_path / "test_image.png"
    img.save(path)
    return path


def test_redact_native_image(tmp_image_path, tmp_path):
    redactor = ImageRedactor()
    output_path = tmp_path / "redacted_image.png"
    
    entities = [
        DetectedEntity(
            entity_type=EntityType.PHONE,
            value="555-1234",
            confidence=0.9,
            detection_method=DetectionMethod.REGEX,
            location=EntityLocation(
                start_char=0,
                end_char=8,
                page=0,
                bounding_box=BoundingBox(x0=100, y0=100, x1=300, y1=150, page=0)
            ),
        )
    ]
    
    redaction_map = RedactionMap(
        document_id="test-doc-id",
        entities=entities,
        total_entities=1,
        entity_counts={"PHONE": 1},
        policy_applied="default_policy"
    )
    
    result_path = redactor.redact(tmp_image_path, output_path, redaction_map)
    
    assert result_path.exists()
    
    # Load the output image and verify the box is black
    out_img = Image.open(result_path).convert("RGB")
    # Check a pixel inside the expected black box
    pixel = out_img.getpixel((200, 125)) # center of the box
    assert pixel == (0, 0, 0) # Black
    
    # Check a pixel outside the box to ensure it wasn't all blacked out
    pixel_outside = out_img.getpixel((400, 400))
    assert pixel_outside == (255, 255, 255) # White
