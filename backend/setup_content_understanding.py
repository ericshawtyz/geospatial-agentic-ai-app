"""One-time setup: configure Content Understanding default model deployments.

Content Understanding prebuilt analyzers require these models deployed in your Foundry resource:
  - gpt-4.1 (or gpt-4.1-mini) — used by prebuilt-documentSearch
  - text-embedding-3-large — used for embeddings

Run once:  python setup_content_understanding.py
"""

import os
from dotenv import load_dotenv
from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.identity import DefaultAzureCredential

load_dotenv()


def main() -> None:
    endpoint = os.environ.get("AZURE_CONTENT_UNDERSTANDING_ENDPOINT", "")
    if not endpoint:
        print("ERROR: Set AZURE_CONTENT_UNDERSTANDING_ENDPOINT in .env")
        return

    credential = DefaultAzureCredential()
    client = ContentUnderstandingClient(endpoint=endpoint, credential=credential)

    # Map the model names Content Understanding expects → your deployment names.
    # Adjust the values if your deployments have different names.
    # Note: gpt-4.1-mini is mapped to gpt-4.1-nano (closest available model).
    model_deployments: dict[str, str] = {
        "gpt-4.1": os.getenv("CU_GPT41_DEPLOYMENT", "gpt-4.1"),
        "gpt-4.1-mini": os.getenv("CU_GPT41_MINI_DEPLOYMENT", "gpt-4.1-nano"),
        "text-embedding-3-large": os.getenv(
            "CU_EMBEDDING_DEPLOYMENT", "text-embedding-3-large"
        ),
    }

    print(f"Endpoint: {endpoint}")
    print("Configuring model deployment defaults...")
    for model, deployment in model_deployments.items():
        print(f"  {model} -> {deployment}")

    updated = client.update_defaults(model_deployments=model_deployments)

    print("\nDone! Current mappings:")
    if updated.model_deployments:
        for model, deployment in updated.model_deployments.items():
            print(f"  {model}: {deployment}")
    else:
        print("  (none returned)")


if __name__ == "__main__":
    main()
