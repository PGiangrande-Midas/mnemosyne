import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def get_embedding(text: str) -> list[float]:
    response = _client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding
