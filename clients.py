"""Bedrock API wrapper supporting both Anthropic and OpenAI message formats."""

import json
import time
from dataclasses import dataclass
from typing import Optional

import boto3
from botocore.config import Config

from config import (
    BEDROCK_REGION,
    MAX_RETRIES,
    READ_TIMEOUT,
    RETRY_DELAYS,
    ModelConfig,
)


@dataclass
class InvokeResult:
    output: str
    input_tokens: int
    output_tokens: int
    elapsed: float
    cost: float
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None


class BedrockClient:
    def __init__(self, region: str = BEDROCK_REGION):
        self._default_region = region
        self._clients: dict[str, object] = {}
        self._clients[region] = self._create_client(region)

    def _create_client(self, region: str):
        return boto3.client(
            "bedrock-runtime",
            region_name=region,
            config=Config(read_timeout=READ_TIMEOUT, retries={"max_attempts": 0}),
        )

    def _get_client(self, model: ModelConfig):
        region = model.region or self._default_region
        if region not in self._clients:
            self._clients[region] = self._create_client(region)
        return self._clients[region]

    def invoke(
        self,
        model: ModelConfig,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 8192,
        temperature: float = 0.7,
    ) -> InvokeResult:
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                return self._invoke_once(model, system_prompt, user_message, max_tokens, temperature)
            except Exception as e:
                last_error = str(e)
                retryable = any(kw in last_error.lower() for kw in [
                    "throttling", "throttled", "5xx", "500", "502", "503", "529", "toomany"
                ])
                if not retryable or attempt == MAX_RETRIES - 1:
                    break
                delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                print(f"  [retry] {model.slug} attempt {attempt+1}: {last_error[:80]}... {delay}s")
                time.sleep(delay)

        return InvokeResult(output="", input_tokens=0, output_tokens=0, elapsed=0.0, cost=0.0, error=last_error)

    def _invoke_once(self, model, system_prompt, user_message, max_tokens, temperature):
        if model.api_format == "anthropic":
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_message}],
            }
        else:
            body = {
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            }

        start = time.time()
        client = self._get_client(model)
        resp = client.invoke_model(
            modelId=model.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )
        elapsed = time.time() - start
        resp_body = json.loads(resp["body"].read())

        if model.api_format == "anthropic":
            output = "".join(b["text"] for b in resp_body.get("content", []) if b.get("type") == "text")
            usage = resp_body.get("usage", {})
            in_tok, out_tok = usage.get("input_tokens", 0), usage.get("output_tokens", 0)
        else:
            choices = resp_body.get("choices", [])
            output = choices[0].get("message", {}).get("content", "") if choices else ""
            usage = resp_body.get("usage", {})
            in_tok, out_tok = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)

        cost = in_tok * model.input_price_per_m / 1e6 + out_tok * model.output_price_per_m / 1e6
        return InvokeResult(output=output, input_tokens=in_tok, output_tokens=out_tok, elapsed=elapsed, cost=cost)
