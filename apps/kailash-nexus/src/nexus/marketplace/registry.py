"""
Marketplace Registry for Nexus

Manages workflow marketplace with ratings, reviews, and installation tracking.
Built entirely on Kailash SDK components.
"""

import logging
import statistics
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from kailash.nodes.admin.audit_log import EnterpriseAuditLogNode as AuditLogNode
from kailash.nodes.admin.permission_check import PermissionCheckNode
from kailash.nodes.data.async_sql import AsyncSQLDatabaseNode
from kailash.nodes.validation.validation_nodes import (
    CodeValidationNode as InputValidationNode,
)
from kailash.workflow.builder import WorkflowBuilder

logger = logging.getLogger(__name__)


@dataclass
class MarketplaceReview:
    """User review for a marketplace item."""

    review_id: str
    workflow_id: str
    user_id: str
    rating: int  # 1-5
    comment: str
    created_at: datetime
    is_verified_install: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "review_id": self.review_id,
            "workflow_id": self.workflow_id,
            "user_id": self.user_id,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat(),
            "is_verified_install": self.is_verified_install,
        }


@dataclass
class MarketplaceStats:
    """Statistics for a marketplace item."""

    total_installs: int = 0
    total_reviews: int = 0
    average_rating: float = 0.0
    rating_distribution: Dict[int, int] = field(
        default_factory=lambda: {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    )
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    trending_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_installs": self.total_installs,
            "total_reviews": self.total_reviews,
            "average_rating": round(self.average_rating, 2),
            "rating_distribution": self.rating_distribution,
            "last_updated": self.last_updated.isoformat(),
            "trending_score": round(self.trending_score, 2),
        }


@dataclass
class MarketplaceItem:
    """An item in the workflow marketplace."""

    item_id: str
    workflow_id: str
    publisher_id: str
    name: str
    description: str
    long_description: str
    version: str
    price: float  # 0 for free
    currency: str = "USD"
    license: str = "MIT"
    categories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    screenshots: List[str] = field(default_factory=list)
    demo_url: Optional[str] = None
    support_url: Optional[str] = None
    is_featured: bool = False
    is_verified: bool = False
    is_public: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    stats: MarketplaceStats = field(default_factory=MarketplaceStats)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "item_id": self.item_id,
            "workflow_id": self.workflow_id,
            "publisher_id": self.publisher_id,
            "name": self.name,
            "description": self.description,
            "long_description": self.long_description,
            "version": self.version,
            "price": self.price,
            "currency": self.currency,
            "license": self.license,
            "categories": self.categories,
            "tags": self.tags,
            "requirements": self.requirements,
            "screenshots": self.screenshots,
            "demo_url": self.demo_url,
            "support_url": self.support_url,
            "is_featured": self.is_featured,
            "is_verified": self.is_verified,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "stats": self.stats.to_dict(),
        }


class MarketplaceRegistry:
    """Registry for workflow marketplace.

    Manages workflow publishing, discovery, ratings, and installations.
    Built entirely on Kailash SDK components.
    """

    def __init__(self):
        """Initialize marketplace registry."""
        # Storage
        self._items: Dict[str, MarketplaceItem] = {}
        self._reviews: Dict[str, List[MarketplaceReview]] = {}  # workflow_id -> reviews
        self._installs: Dict[str, List[str]] = {}  # workflow_id -> [user_ids]
        self._user_installs: Dict[str, List[str]] = {}  # user_id -> [workflow_ids]

        # Create management workflows
        self._init_management_workflows()

        logger.info("Marketplace registry initialized")

    def _init_management_workflows(self):
        """Initialize marketplace management workflows using SDK nodes."""
        # Publishing workflow
        self.publish_workflow = WorkflowBuilder()

        # Validate input
        self.publish_workflow.add_node(
            "InputValidationNode",
            "validate_item",
            {
                "rules": {
                    "name": {"required": True, "type": "string", "min_length": 3},
                    "description": {
                        "required": True,
                        "type": "string",
                        "min_length": 10,
                    },
                    "version": {"required": True, "pattern": r"^\d+\.\d+\.\d+$"},
                    "price": {"required": True, "type": "number", "min": 0},
                }
            },
        )

        # Check access
        self.publish_workflow.add_node(
            "PermissionCheckNode",
            "check_publisher",
            {
                "resource_type": "marketplace_publish",
                "required_permissions": ["publish"],
            },
        )

        # Audit publishing
        self.publish_workflow.add_node(
            "AuditLogNode",
            "audit_publish",
            {"event_type": "marketplace_publish", "include_user": True},
        )

        # Connect nodes
        self.publish_workflow.add_connection(
            "validate_item", "valid", "check_publisher", "input"
        )
        self.publish_workflow.add_connection(
            "check_publisher", "allowed", "audit_publish", "event"
        )

        # Review workflow
        self.review_workflow = WorkflowBuilder()

        # Validate review
        self.review_workflow.add_node(
            "InputValidationNode",
            "validate_review",
            {
                "rules": {
                    "rating": {"required": True, "type": "integer", "min": 1, "max": 5},
                    "comment": {"required": True, "type": "string", "min_length": 10},
                }
            },
        )

        # Check if user has installed
        self.review_workflow.add_node(
            "PythonCodeNode",
            "check_install",
            {
                "code": """
# Check if user has installed the workflow
user_id = context.get('user_id')
workflow_id = context.get('workflow_id')

# In production, would check actual install records
result = {
    'has_installed': True,  # Simplified for now
    'install_date': datetime.now(timezone.utc).isoformat()
}
"""
            },
        )

        # Audit review
        self.review_workflow.add_node(
            "AuditLogNode", "audit_review", {"event_type": "marketplace_review"}
        )

        self.review_workflow.add_connection(
            "validate_review", "valid", "check_install", "input"
        )
        self.review_workflow.add_connection(
            "check_install", "result", "audit_review", "event"
        )

    async def initialize(self):
        """Initialize the marketplace registry."""
        # In production, would initialize database connections
        logger.info("Marketplace registry initialized")

    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Marketplace registry cleaned up")

    def publish(
        self,
        workflow_id: str,
        publisher_id: str,
        name: str,
        description: str,
        long_description: str = "",
        version: str = "1.0.0",
        price: float = 0.0,
        **kwargs,
    ) -> MarketplaceItem:
        """Publish a workflow to the marketplace.

        Args:
            workflow_id: The workflow to publish
            publisher_id: Publisher user/org ID
            name: Display name
            description: Short description
            long_description: Detailed description
            version: Semantic version
            price: Price (0 for free)
            **kwargs: Additional fields

        Returns:
            MarketplaceItem instance
        """
        item_id = f"mp_{uuid.uuid4().hex[:8]}"

        # Create marketplace item
        item = MarketplaceItem(
            item_id=item_id,
            workflow_id=workflow_id,
            publisher_id=publisher_id,
            name=name,
            description=description,
            long_description=long_description or description,
            version=version,
            price=price,
            categories=kwargs.get("categories", []),
            tags=kwargs.get("tags", []),
            requirements=kwargs.get("requirements", []),
            screenshots=kwargs.get("screenshots", []),
            demo_url=kwargs.get("demo_url"),
            support_url=kwargs.get("support_url"),
            license=kwargs.get("license", "MIT"),
        )

        # Store item
        self._items[item_id] = item

        logger.info(f"Published workflow to marketplace: {item_id} ({name})")
        return item

    def get_item(self, item_id: str) -> Optional[MarketplaceItem]:
        """Get a marketplace item by ID.

        Args:
            item_id: Item identifier

        Returns:
            MarketplaceItem or None
        """
        return self._items.get(item_id)

    def search(
        self,
        query: Optional[str] = None,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        price_range: Optional[Tuple[float, float]] = None,
        min_rating: Optional[float] = None,
        sort_by: str = "trending",
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[MarketplaceItem], int]:
        """Search marketplace items.

        Args:
            query: Search text
            categories: Filter by categories
            tags: Filter by tags
            price_range: Price range (min, max)
            min_rating: Minimum average rating
            sort_by: Sort field (trending, rating, installs, newest)
            limit: Maximum results
            offset: Results offset

        Returns:
            Tuple of (items, total_count)
        """
        results = list(self._items.values())

        # Apply filters
        if query:
            query_lower = query.lower()
            results = [
                item
                for item in results
                if (
                    query_lower in item.name.lower()
                    or query_lower in item.description.lower()
                    or any(query_lower in tag.lower() for tag in item.tags)
                )
            ]

        if categories:
            results = [
                item
                for item in results
                if any(cat in item.categories for cat in categories)
            ]

        if tags:
            results = [
                item for item in results if any(tag in item.tags for tag in tags)
            ]

        if price_range:
            min_price, max_price = price_range
            results = [item for item in results if min_price <= item.price <= max_price]

        if min_rating:
            results = [
                item for item in results if item.stats.average_rating >= min_rating
            ]

        # Sort results
        if sort_by == "trending":
            results.sort(key=lambda x: x.stats.trending_score, reverse=True)
        elif sort_by == "rating":
            results.sort(key=lambda x: x.stats.average_rating, reverse=True)
        elif sort_by == "installs":
            results.sort(key=lambda x: x.stats.total_installs, reverse=True)
        elif sort_by == "newest":
            results.sort(key=lambda x: x.created_at, reverse=True)
        elif sort_by == "price_low":
            results.sort(key=lambda x: x.price)
        elif sort_by == "price_high":
            results.sort(key=lambda x: x.price, reverse=True)

        # Apply pagination
        total = len(results)
        results = results[offset : offset + limit]

        return results, total

    def get_featured(self, limit: int = 10) -> List[MarketplaceItem]:
        """Get featured marketplace items.

        Args:
            limit: Maximum items

        Returns:
            List of featured items
        """
        featured = [item for item in self._items.values() if item.is_featured]
        featured.sort(key=lambda x: x.stats.trending_score, reverse=True)
        return featured[:limit]

    def get_trending(
        self, limit: int = 10, timeframe: str = "week"
    ) -> List[MarketplaceItem]:
        """Get trending marketplace items.

        Args:
            limit: Maximum items
            timeframe: Time period (day, week, month)

        Returns:
            List of trending items
        """
        # Calculate trending scores based on recent activity
        # In production, would use actual time-based metrics
        items = list(self._items.values())
        items.sort(key=lambda x: x.stats.trending_score, reverse=True)
        return items[:limit]

    def install(
        self, item_id: str, user_id: str, tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Install a marketplace item.

        Args:
            item_id: Item to install
            user_id: Installing user
            tenant_id: Optional tenant ID

        Returns:
            Installation result
        """
        item = self._items.get(item_id)
        if not item:
            raise ValueError(f"Item {item_id} not found")

        workflow_id = item.workflow_id

        # Track install
        if workflow_id not in self._installs:
            self._installs[workflow_id] = []
        if user_id not in self._installs[workflow_id]:
            self._installs[workflow_id].append(user_id)

        if user_id not in self._user_installs:
            self._user_installs[user_id] = []
        if workflow_id not in self._user_installs[user_id]:
            self._user_installs[user_id].append(workflow_id)

        # Update stats
        item.stats.total_installs = len(self._installs[workflow_id])
        item.stats.last_updated = datetime.now(timezone.utc)

        # Update trending score
        self._update_trending_score(item)

        logger.info(f"User {user_id} installed item: {item_id}")

        return {
            "success": True,
            "item_id": item_id,
            "workflow_id": workflow_id,
            "install_count": item.stats.total_installs,
        }

    def uninstall(self, item_id: str, user_id: str) -> bool:
        """Uninstall a marketplace item.

        Args:
            item_id: Item to uninstall
            user_id: User ID

        Returns:
            True if uninstalled
        """
        item = self._items.get(item_id)
        if not item:
            return False

        workflow_id = item.workflow_id

        # Remove install tracking
        if workflow_id in self._installs and user_id in self._installs[workflow_id]:
            self._installs[workflow_id].remove(user_id)
            item.stats.total_installs = len(self._installs[workflow_id])

        if (
            user_id in self._user_installs
            and workflow_id in self._user_installs[user_id]
        ):
            self._user_installs[user_id].remove(workflow_id)

        logger.info(f"User {user_id} uninstalled item: {item_id}")
        return True

    def add_review(
        self, item_id: str, user_id: str, rating: int, comment: str
    ) -> MarketplaceReview:
        """Add a review for a marketplace item.

        Args:
            item_id: Item to review
            user_id: Reviewing user
            rating: Rating 1-5
            comment: Review comment

        Returns:
            MarketplaceReview instance
        """
        item = self._items.get(item_id)
        if not item:
            raise ValueError(f"Item {item_id} not found")

        workflow_id = item.workflow_id

        # Check if user has installed
        has_installed = user_id in self._installs.get(workflow_id, [])

        # Create review
        review = MarketplaceReview(
            review_id=f"rev_{uuid.uuid4().hex[:8]}",
            workflow_id=workflow_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
            created_at=datetime.now(timezone.utc),
            is_verified_install=has_installed,
        )

        # Store review
        if workflow_id not in self._reviews:
            self._reviews[workflow_id] = []
        self._reviews[workflow_id].append(review)

        # Update stats
        self._update_review_stats(item)

        logger.info(f"User {user_id} reviewed item: {item_id} ({rating} stars)")
        return review

    def get_reviews(
        self, item_id: str, limit: int = 20, offset: int = 0
    ) -> Tuple[List[MarketplaceReview], int]:
        """Get reviews for a marketplace item.

        Args:
            item_id: Item ID
            limit: Maximum reviews
            offset: Reviews offset

        Returns:
            Tuple of (reviews, total_count)
        """
        item = self._items.get(item_id)
        if not item:
            return [], 0

        reviews = self._reviews.get(item.workflow_id, [])

        # Sort by newest first
        reviews.sort(key=lambda x: x.created_at, reverse=True)

        total = len(reviews)
        results = reviews[offset : offset + limit]

        return results, total

    def _update_review_stats(self, item: MarketplaceItem):
        """Update review statistics for an item."""
        reviews = self._reviews.get(item.workflow_id, [])

        if not reviews:
            return

        # Calculate stats
        ratings = [r.rating for r in reviews]
        item.stats.total_reviews = len(reviews)
        item.stats.average_rating = statistics.mean(ratings)

        # Update rating distribution
        for rating in range(1, 6):
            item.stats.rating_distribution[rating] = ratings.count(rating)

        item.stats.last_updated = datetime.now(timezone.utc)

        # Update trending score
        self._update_trending_score(item)

    def _update_trending_score(self, item: MarketplaceItem):
        """Update trending score for an item.

        Simple algorithm based on:
        - Recent installs
        - Average rating
        - Total reviews
        """
        # Simplified trending algorithm
        # In production, would use time-weighted metrics
        base_score = item.stats.total_installs * 0.5
        rating_boost = item.stats.average_rating * item.stats.total_reviews * 0.3
        recency_boost = 10 if item.is_featured else 0

        item.stats.trending_score = base_score + rating_boost + recency_boost

    def get_user_installs(self, user_id: str) -> List[MarketplaceItem]:
        """Get items installed by a user.

        Args:
            user_id: User identifier

        Returns:
            List of installed items
        """
        workflow_ids = self._user_installs.get(user_id, [])

        items = []
        for item in self._items.values():
            if item.workflow_id in workflow_ids:
                items.append(item)

        return items

    def get_publisher_items(self, publisher_id: str) -> List[MarketplaceItem]:
        """Get items published by a user/org.

        Args:
            publisher_id: Publisher identifier

        Returns:
            List of published items
        """
        items = [
            item for item in self._items.values() if item.publisher_id == publisher_id
        ]

        items.sort(key=lambda x: x.created_at, reverse=True)
        return items

    def update_item(self, item_id: str, updates: Dict[str, Any]) -> MarketplaceItem:
        """Update a marketplace item.

        Args:
            item_id: Item to update
            updates: Fields to update

        Returns:
            Updated item
        """
        item = self._items.get(item_id)
        if not item:
            raise ValueError(f"Item {item_id} not found")

        # Update allowed fields
        allowed_fields = [
            "description",
            "long_description",
            "version",
            "price",
            "categories",
            "tags",
            "requirements",
            "screenshots",
            "demo_url",
            "support_url",
        ]

        for field_name, value in updates.items():
            if field_name in allowed_fields:
                setattr(item, field_name, value)

        item.updated_at = datetime.now(timezone.utc)

        logger.info(f"Updated marketplace item: {item_id}")
        return item

    def feature_item(self, item_id: str, featured: bool = True):
        """Feature or unfeature a marketplace item.

        Args:
            item_id: Item to feature
            featured: Feature status
        """
        item = self._items.get(item_id)
        if item:
            item.is_featured = featured
            self._update_trending_score(item)
            logger.info(f"{'Featured' if featured else 'Unfeatured'} item: {item_id}")

    def verify_item(self, item_id: str, verified: bool = True):
        """Verify or unverify a marketplace item.

        Args:
            item_id: Item to verify
            verified: Verification status
        """
        item = self._items.get(item_id)
        if item:
            item.is_verified = verified
            logger.info(f"{'Verified' if verified else 'Unverified'} item: {item_id}")

    async def health_check(self) -> Dict[str, Any]:
        """Get health status of marketplace.

        Returns:
            Health status dictionary
        """
        return {
            "healthy": True,
            "total_items": len(self._items),
            "public_items": len([i for i in self._items.values() if i.is_public]),
            "featured_items": len([i for i in self._items.values() if i.is_featured]),
            "verified_items": len([i for i in self._items.values() if i.is_verified]),
            "total_installs": sum(
                len(installs) for installs in self._installs.values()
            ),
            "total_reviews": sum(len(reviews) for reviews in self._reviews.values()),
        }
