"""ENTSO-E REST API client."""

import logging
from datetime import datetime, timedelta
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.entsoe.constants import (
    ENTSOE_API_BASE_URL,
    REQUEST_TIMEOUT_SECONDS,
    MAX_RETRIES,
    RETRY_DELAY_SECONDS,
)

logger = logging.getLogger(__name__)


class ENTSOEClient:
    """HTTP client for ENTSO-E Transparency Platform REST API.
    
    Handles:
    - API authentication (security token in header)
    - HTTP requests with timeout and retry logic
    - Response validation
    - Error handling (rate limits, timeouts, unavailable)
    
    Reference:
      https://transparency.entsoe.eu/
    """

    def __init__(self, api_token: str | None = None):
        """Initialize ENTSO-E client.
        
        Args:
            api_token: ENTSO-E security token. If None, uses settings.entsoe_api_token.
            
        Raises:
            ValueError: If no API token is provided or configured.
        """
        self.api_token = api_token or settings.entsoe_api_token
        if not self.api_token:
            raise ValueError(
                "ENTSO-E API token not configured. "
                "Set ENTSOE_API_TOKEN environment variable."
            )
        
        self.base_url = ENTSOE_API_BASE_URL
        self.timeout = REQUEST_TIMEOUT_SECONDS

    def _headers(self) -> dict[str, str]:
        """Construct request headers with authentication.
        
        Returns:
            Dictionary of HTTP headers.
        """
        return {
            "SecurityToken": self.api_token,
        }

    async def get_query(
        self,
        document_type: str,
        process_type: str,
        area_code: str,
        start_time: datetime,
        end_time: datetime,
        **kwargs: Any,
    ) -> str:
        """Execute a query against ENTSO-E API.
        
        Args:
            document_type: ENTSO-E document type (e.g., "A65" for load, "A73" for generation)
            process_type: Process type (e.g., "A18" for realtime, "A01" for day ahead)
            area_code: ENTSO-E bidding zone domain code (e.g., "10YNL----------L")
            start_time: Start of query period (UTC)
            end_time: End of query period (UTC)
            **kwargs: Additional query parameters (e.g., psrType for generation queries)
            
        Returns:
            Raw XML response as string.
            
        Raises:
            httpx.TimeoutException: If request times out.
            httpx.HTTPStatusError: If API returns error status.
            ValueError: If response is invalid.
        """
        params = {
            "documentType": document_type,
            "processType": process_type,
            "in_Domain": area_code,
            "out_Domain": area_code,
            "periodStart": start_time.strftime("%Y%m%d%H%M"),
            "periodEnd": end_time.strftime("%Y%m%d%H%M"),
            **kwargs,
        }
        
        # Implement exponential backoff retry logic
        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(
                        self.base_url,
                        params=params,
                        headers=self._headers(),
                    )
                    response.raise_for_status()
                    
                    if not response.text:
                        raise ValueError("Empty response from ENTSO-E API")
                    
                    logger.info(
                        f"ENTSO-E query successful: {document_type} "
                        f"for {area_code} ({start_time} to {end_time})"
                    )
                    return response.text
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limited
                    if attempt < MAX_RETRIES - 1:
                        wait_time = RETRY_DELAY_SECONDS * (2 ** attempt)
                        logger.warning(
                            f"ENTSO-E rate limited. Retrying in {wait_time}s "
                            f"(attempt {attempt + 1}/{MAX_RETRIES})"
                        )
                        await httpx.AsyncClient().aclose()
                        # Use asyncio.sleep equivalent
                        import asyncio
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise
                else:
                    logger.error(
                        f"ENTSO-E API error: {e.response.status_code} "
                        f"({e.response.reason_phrase})"
                    )
                    raise
            except httpx.TimeoutException as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY_SECONDS * (2 ** attempt)
                    logger.warning(
                        f"ENTSO-E request timeout. Retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{MAX_RETRIES})"
                    )
                    import asyncio
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"ENTSO-E request failed after {MAX_RETRIES} attempts: {e}")
                    raise

    async def get_load(
        self,
        area_code: str,
        start_time: datetime,
        end_time: datetime,
        process_type: str = "A18",
    ) -> str:
        """Get actual total load (demand) data.
        
        Args:
            area_code: ENTSO-E bidding zone domain code
            start_time: Start of query period (UTC)
            end_time: End of query period (UTC)
            process_type: Process type (default: realtime)
            
        Returns:
            Raw XML response.
        """
        from app.integrations.entsoe.constants import DOCUMENT_TYPE_LOAD
        
        return await self.get_query(
            document_type=DOCUMENT_TYPE_LOAD,
            process_type=process_type,
            area_code=area_code,
            start_time=start_time,
            end_time=end_time,
        )

    async def get_generation(
        self,
        area_code: str,
        start_time: datetime,
        end_time: datetime,
        process_type: str = "A18",
    ) -> str:
        """Get aggregated generation per type data.
        
        Args:
            area_code: ENTSO-E bidding zone domain code
            start_time: Start of query period (UTC)
            end_time: End of query period (UTC)
            process_type: Process type (default: realtime)
            
        Returns:
            Raw XML response.
        """
        from app.integrations.entsoe.constants import DOCUMENT_TYPE_GENERATION
        
        return await self.get_query(
            document_type=DOCUMENT_TYPE_GENERATION,
            process_type=process_type,
            area_code=area_code,
            start_time=start_time,
            end_time=end_time,
        )

    async def close(self) -> None:
        """Close the HTTP client session."""
        # Will implement proper session management in Phase 3
        pass
