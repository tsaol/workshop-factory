"""Model configurations and pipeline settings for workshop-factory."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelConfig:
    slug: str
    model_id: str
    api_format: str  # "anthropic" or "openai"
    input_price_per_m: float
    output_price_per_m: float
    region: str = ""


MODELS: dict[str, ModelConfig] = {
    "claude-opus": ModelConfig(
        slug="claude-opus",
        model_id="us.anthropic.claude-opus-4-6-v1",
        api_format="anthropic",
        input_price_per_m=15.00,
        output_price_per_m=75.00,
    ),
    "kimi-k2.5": ModelConfig(
        slug="kimi-k2.5",
        model_id="moonshotai.kimi-k2.5",
        api_format="openai",
        input_price_per_m=0.30,
        output_price_per_m=1.20,
    ),
    "deepseek-v3.2": ModelConfig(
        slug="deepseek-v3.2",
        model_id="deepseek.v3.2",
        api_format="openai",
        input_price_per_m=0.30,
        output_price_per_m=0.90,
    ),
    "mistral-large-3": ModelConfig(
        slug="mistral-large-3",
        model_id="mistral.mistral-large-3-675b-instruct",
        api_format="openai",
        input_price_per_m=2.00,
        output_price_per_m=6.00,
    ),
    "qwen3-235b": ModelConfig(
        slug="qwen3-235b",
        model_id="qwen.qwen3-235b-a22b-2507-v1:0",
        api_format="openai",
        input_price_per_m=0.28,
        output_price_per_m=1.13,
        region="us-west-2",
    ),
}

# Pipeline step -> model mapping
STEP_MODELS = {
    "writer": "claude-opus",
    "critic": "kimi-k2.5",
    "refiner": "deepseek-v3.2",
    "deai": "mistral-large-3",
    "i18n": "kimi-k2.5",
}

BEDROCK_REGION = "us-east-1"
MAX_RETRIES = 3
RETRY_DELAYS = [5, 10, 20]
READ_TIMEOUT = 600
MAX_TOKENS = 16384
TEMPERATURE = 0.7
