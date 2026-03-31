from fastapi import APIRouter, UploadFile

from app.services.file_processor import process_file

router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile):
    """Upload and process a file (GeoJSON, image, document, video)."""
    contents = await file.read()
    result = await process_file(
        file_bytes=contents,
        filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
    )
    return result
