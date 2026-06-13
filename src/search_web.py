from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class SearchResult:
    title: str
    snippet: str
    link: str
    score: float | None = None


class TavilySearchError(RuntimeError):
    pass


class TavilyWebSearch:
    """Small Tavily Search API client for agent experiments.

    Required environment variable:
      TAVILY_API_KEY

    Optional environment variables:
      TAVILY_SEARCH_NUM_RESULTS (default: 5)
      TAVILY_SEARCH_DEPTH (default: basic)
      TAVILY_SEARCH_TOPIC (default: general)
      TAVILY_SEARCH_CACHE (default: outputs/tavily_search_cache.json)

    The implementation deliberately uses ``search_depth=basic`` by default so
    that a normal search consumes the minimum number of Tavily credits.
    """

    def __init__(
        self,
        api_key: str | None = None,
        num_results: int | None = None,
        search_depth: str | None = None,
        topic: str | None = None,
        cache_path: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "").strip()
        self.num_results = max(
            1,
            min(
                int(num_results or os.getenv("TAVILY_SEARCH_NUM_RESULTS", "5")),
                20,
            ),
        )
        self.search_depth = (
            search_depth or os.getenv("TAVILY_SEARCH_DEPTH", "basic")
        ).strip().lower()
        if self.search_depth not in {"basic", "advanced"}:
            raise ValueError(
                "TAVILY_SEARCH_DEPTH must be either 'basic' or 'advanced'."
            )

        self.topic = (topic or os.getenv("TAVILY_SEARCH_TOPIC", "general")).strip()
        self.cache_path = Path(
            cache_path
            or os.getenv(
                "TAVILY_SEARCH_CACHE",
                "outputs/tavily_search_cache.json",
            )
        )
        self._cache = self._load_cache()
        self._client = None

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str) -> Dict[str, Any]:
        query = " ".join(query.split()).strip()
        if not query:
            raise TavilySearchError("Search query is empty.")
        if len(query) > 400:
            query = query[:400].rsplit(" ", 1)[0].strip()

        if not self.configured:
            raise TavilySearchError(
                "Tavily search is not configured. Set TAVILY_API_KEY."
            )

        cache_key = self._cache_key(query)
        if cache_key in self._cache:
            cached = dict(self._cache[cache_key])
            cached["from_cache"] = True
            return cached

        client = self._get_client()
        try:
            payload = client.search(
                query=query,
                search_depth=self.search_depth,
                topic=self.topic,
                max_results=self.num_results,
                include_answer=False,
                include_raw_content=False,
                include_images=False,
            )
        except Exception as exc:  # SDK exposes several provider-specific errors.
            raise TavilySearchError(f"Tavily search failed: {exc}") from exc

        results: List[SearchResult] = []
        for item in payload.get("results", [])[: self.num_results]:
            raw_score = item.get("score")
            try:
                score = float(raw_score) if raw_score is not None else None
            except (TypeError, ValueError):
                score = None

            results.append(
                SearchResult(
                    title=str(item.get("title", "")).strip(),
                    snippet=str(item.get("content", "")).strip(),
                    link=str(item.get("url", "")).strip(),
                    score=score,
                )
            )

        output: Dict[str, Any] = {
            "provider": "tavily",
            "query": query,
            "search_depth": self.search_depth,
            "topic": self.topic,
            "results": [asdict(result) for result in results],
            "result_count": len(results),
            "response_time": payload.get("response_time"),
            "request_id": payload.get("request_id"),
            "from_cache": False,
        }
        self._cache[cache_key] = output
        self._save_cache()
        return output

    @staticmethod
    def format_evidence(search_output: Dict[str, Any]) -> str:
        results = search_output.get("results", [])
        if not results:
            return "No web search results were returned."

        blocks: List[str] = []
        for index, result in enumerate(results, start=1):
            score = result.get("score")
            score_line = f"Relevance score: {score:.4f}" if isinstance(score, float) else ""
            lines = [
                f"Result {index}",
                f"Title: {result.get('title', '')}",
                f"Snippet: {result.get('snippet', '')}",
                f"URL: {result.get('link', '')}",
            ]
            if score_line:
                lines.append(score_line)
            blocks.append("\n".join(lines))
        return "\n\n".join(blocks)

    @staticmethod
    def detect_possible_leakage(
        question: str,
        search_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Heuristic only: flag results that closely repeat the benchmark question."""
        normalized_question = _normalize_text(question)
        question_words = normalized_question.split()
        longest_phrase = " ".join(question_words[:14]) if len(question_words) >= 14 else ""

        flagged: List[Dict[str, Any]] = []
        for index, result in enumerate(search_output.get("results", []), start=1):
            candidate = _normalize_text(
                f"{result.get('title', '')} {result.get('snippet', '')}"
            )
            similarity = SequenceMatcher(
                None,
                normalized_question[:1000],
                candidate[:1000],
            ).ratio()
            contains_long_phrase = bool(longest_phrase and longest_phrase in candidate)
            if similarity >= 0.72 or contains_long_phrase:
                flagged.append(
                    {
                        "result_index": index,
                        "similarity": round(similarity, 4),
                        "contains_long_question_phrase": contains_long_phrase,
                        "url": result.get("link", ""),
                    }
                )

        return {
            "possible_leakage": bool(flagged),
            "flagged_results": flagged,
            "note": "Heuristic flag only; manually inspect flagged search results.",
        }

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from tavily import TavilyClient
        except ImportError as exc:
            raise TavilySearchError(
                "tavily-python is not installed. Run: pip install tavily-python"
            ) from exc

        self._client = TavilyClient(api_key=self.api_key)
        return self._client

    def _cache_key(self, query: str) -> str:
        return (
            f"tavily:{self.search_depth}:{self.topic}:"
            f"{self.num_results}:{query.lower()}"
        )

    def _load_cache(self) -> Dict[str, Any]:
        if not self.cache_path.exists():
            return {}
        try:
            with self.cache_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.cache_path.with_suffix(self.cache_path.suffix + ".tmp")
        with temporary_path.open("w", encoding="utf-8") as handle:
            json.dump(self._cache, handle, ensure_ascii=False, indent=2)
        temporary_path.replace(self.cache_path)


def _normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())
