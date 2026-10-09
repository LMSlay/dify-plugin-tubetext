from typing import Any

from dify_plugin import Tool

from tools.common import TubeTextMixin
from tubetext_client import TubeTextError, split_list, to_int


class AliExpressSearchTool(TubeTextMixin, Tool):
    simple_fields = [
        "status", "keyword", "rank", "productId", "url", "title", "price", "originalPrice",
        "currency", "soldCount", "rating", "shipFrom", "freeShipping", "sponsored",
        "priceIsNewShopperDeal", "error",
    ]

    def build_jobs(self, params: dict[str, Any]) -> list[tuple[str, dict[str, Any], int]]:
        keywords = split_list(params.get("keywords"), allow_commas=False)
        if not keywords:
            raise TubeTextError("Add at least one search term in 'Keywords' (one per line).")
        if len(keywords) > 20:
            raise TubeTextError("'Keywords' accepts up to 20 search terms per call.")
        per_keyword = to_int(params.get("max_items_per_keyword"), 20, 1, 300)
        actor_input: dict[str, Any] = {
            "keywords": keywords,
            "maxItemsPerKeyword": per_keyword,
            "sortBy": params.get("sort_by") or "best_match",
            "shipTo": params.get("ship_to") or "US",
            "currency": params.get("currency") or "USD",
            "skipSponsored": bool(params.get("skip_sponsored", False)),
            "skipNewShopperDeals": bool(params.get("skip_new_shopper_deals", False)),
        }
        for key, field in (("min_price", "minPrice"), ("max_price", "maxPrice")):
            value = params.get(key)
            if value not in (None, ""):
                actor_input[field] = to_int(value, 0, 0, 10_000_000)
        return [("aliexpress", actor_input, len(keywords) * per_keyword)]
