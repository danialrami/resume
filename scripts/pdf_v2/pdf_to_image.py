"""PDF to image conversion for vision validation."""

from pathlib import Path
from typing import Optional


def pdf_to_images(
    pdf_path: Path,
    output_dir: Optional[Path] = None,
    dpi: int = 150
) -> list[Path]:
    """
    Convert PDF to images for vision model input.
    
    Requires: pip install pdf2image, and poppler (brew install poppler)
    
    Returns:
        List of image paths (one per page)
    """
    try:
        from pdf2image import convert_from_path
    except ImportError:
        print("Warning: pdf2image not installed. Run: pip install pdf2image")
        return []
    
    if output_dir is None:
        output_dir = pdf_path.parent
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    images = convert_from_path(
        str(pdf_path),
        dpi=dpi,
        output_folder=str(output_dir),
        output_prefix=pdf_path.stem
    )
    
    # Return as Path objects
    return [output_dir / f"{pdf_path.stem}-{i+1:02d}.png" for i, _ in enumerate(images)]