from typing import Any

from dify_plugin import Tool

from tools.common import TubeTextMixin
from tubetext_client import TubeTextError, split_list, to_int


class TikTokShopProductsTool(TubeTextMixin, Tool):
    simple_fields = [
        "status", "input", "productId", "url", "title", "price", "originalPrice", "currency",
        "soldCount", "rating", "reviewCount", "totalStock", "shopName", "shopUrl",
        "categories", "freeShipping", "deliveryDays", "reviews", "error",
    ]

    def build_jobs(self, params: dict[str, Any]) -> list[tuple[str, dict[str, Any], int]]:
        urls = split_list(params.get("urls"))
        if not urls:
            raise TubeTextError("Add at least one TikTok Shop product, store or category link in 'Links'.")
        if len(urls) > 100:
            raise TubeTextError("'Links' accepts up to 100 links per call.")
        per_listing = to_int(params.get("max_products_per_listing"), 20, 1, 200)
        actor_input = {
            "urls": urls,
            "includeDetails": bool(params.get("include_details", True)),
            "includeReviews": bool(params.get("include_reviews", False)),
            "maxProductsPerListing": per_listing,
        }
        return [("tiktok_shop", actor_input, len(urls) * per_listing)]
