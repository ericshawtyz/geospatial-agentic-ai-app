import json
from pathlib import Path

from openai import AsyncAzureOpenAI
from azure.identity.aio import DefaultAzureCredential

from app.config import settings


async def process_file(file_bytes: bytes, filename: str, content_type: str) -> dict:
    """Process an uploaded file and return extracted content + optional map data."""
    ext = Path(filename).suffix.lower()

    if ext in (".geojson", ".json"):
        return _process_geojson(file_bytes, filename)
    elif ext in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
        return await _process_image(file_bytes, filename, content_type)
    elif ext == ".pdf":
        return await _process_document(file_bytes, filename, content_type)
    elif ext in (".mp4", ".mov", ".avi"):
        return await _process_video(file_bytes, filename, content_type)
    else:
        return {
            "type": "unsupported",
            "filename": filename,
            "message": f"File type '{ext}' is not supported.",
        }


def _process_geojson(file_bytes: bytes, filename: str) -> dict:
    """Parse and validate GeoJSON, return geometry for map rendering."""
    data = json.loads(file_bytes.decode("utf-8"))

    geojson_type = data.get("type", "")
    if geojson_type not in (
        "FeatureCollection",
        "Feature",
        "Point",
        "MultiPoint",
        "LineString",
        "MultiLineString",
        "Polygon",
        "MultiPolygon",
        "GeometryCollection",
    ):
        return {
            "type": "error",
            "filename": filename,
            "message": "Invalid GeoJSON: missing or unrecognized 'type' field.",
        }

    return {
        "type": "geojson",
        "filename": filename,
        "geojson": data,
        "summary": f"GeoJSON {geojson_type} loaded from {filename}",
    }


async def _process_image(
    file_bytes: bytes, filename: str, content_type: str
) -> dict:
    """Process image using GPT-4o vision to extract text and spatial info."""
    import base64

    b64 = base64.b64encode(file_bytes).decode("utf-8")

    credential = DefaultAzureCredential()
    try:
        token = await credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        )
        client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_content_understanding_endpoint
            or settings.azure_ai_project_endpoint.split("/api/")[0],
            azure_ad_token=token.token,
            api_version="2024-12-01-preview",
        )

        response = await client.chat.completions.create(
            model=settings.model_deployment_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Analyze this image. Extract any text (OCR), identify locations, "
                                "addresses, or spatial features. If it's a map or contains geographic "
                                "information, describe the areas and features shown. "
                                "Return a structured summary."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{content_type};base64,{b64}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=2000,
        )

        return {
            "type": "image_analysis",
            "filename": filename,
            "content": response.choices[0].message.content,
        }
    finally:
        await credential.close()


async def _process_document(
    file_bytes: bytes, filename: str, content_type: str
) -> dict:
    """Process PDF/document using Azure Content Understanding for text and table extraction."""
    from azure.ai.contentunderstanding.aio import ContentUnderstandingClient
    from azure.ai.contentunderstanding.models import DocumentContent

    endpoint = settings.azure_content_understanding_endpoint
    if not endpoint:
        return {
            "type": "error",
            "filename": filename,
            "message": (
                "PDF processing requires Azure Content Understanding. "
                "Set AZURE_CONTENT_UNDERSTANDING_ENDPOINT in your .env file."
            ),
        }

    credential = DefaultAzureCredential()
    try:
        async with ContentUnderstandingClient(
            endpoint=endpoint, credential=credential
        ) as client:
            poller = await client.begin_analyze_binary(
                analyzer_id="prebuilt-documentSearch",
                binary_input=file_bytes,
            )
            result = await poller.result()

        if not result.contents or len(result.contents) == 0:
            return {
                "type": "error",
                "filename": filename,
                "message": "No content extracted from document.",
            }

        content_item = result.contents[0]
        markdown = content_item.markdown or ""

        # Truncate if extremely large to avoid context window issues
        if len(markdown) > 15000:
            markdown = markdown[:15000] + "\n\n... (document truncated, showing first ~15000 characters)"

        page_count = 0
        if isinstance(content_item, DocumentContent):
            start = content_item.start_page_number or 1
            end = content_item.end_page_number or 1
            page_count = end - start + 1

        return {
            "type": "document_analysis",
            "filename": filename,
            "content": markdown,
            "page_count": page_count,
        }
    except Exception as e:
        return {
            "type": "error",
            "filename": filename,
            "message": f"Content Understanding error: {e}",
        }
    finally:
        await credential.close()


async def _process_video(
    file_bytes: bytes, filename: str, content_type: str
) -> dict:
    """Process video — placeholder for frame extraction + vision analysis."""
    return {
        "type": "video_analysis",
        "filename": filename,
        "content": (
            "Video processing is available. Upload individual frames as images "
            "for detailed analysis, or this file will be processed when Azure "
            "Content Understanding video analysis is configured."
        ),
    }
