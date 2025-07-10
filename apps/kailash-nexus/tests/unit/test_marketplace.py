"""
Unit tests for Marketplace Registry.
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from nexus.marketplace.registry import (
    MarketplaceItem,
    MarketplaceRegistry,
    MarketplaceReview,
    MarketplaceStats,
)


class TestMarketplaceRegistry:
    """Test MarketplaceRegistry class."""

    @pytest.fixture
    def registry(self):
        """Create a marketplace registry instance."""
        return MarketplaceRegistry()

    def test_initialization(self, registry):
        """Test registry initialization."""
        assert len(registry._items) == 0
        assert len(registry._reviews) == 0
        assert len(registry._installs) == 0
        assert len(registry._user_installs) == 0

    def test_publish_item(self, registry):
        """Test publishing a workflow to marketplace."""
        item = registry.publish(
            workflow_id="workflow/test1",
            publisher_id="publisher1",
            name="Test Workflow",
            description="A test workflow for unit tests",
            version="1.0.0",
            price=0.0,
        )

        assert item.item_id.startswith("mp_")
        assert item.workflow_id == "workflow/test1"
        assert item.publisher_id == "publisher1"
        assert item.name == "Test Workflow"
        assert item.description == "A test workflow for unit tests"
        assert item.version == "1.0.0"
        assert item.price == 0.0
        assert item.currency == "USD"
        assert item.license == "MIT"
        assert item.is_public is True

        # Check storage
        assert item.item_id in registry._items

    def test_publish_with_details(self, registry):
        """Test publishing with full details."""
        item = registry.publish(
            workflow_id="workflow/advanced",
            publisher_id="publisher2",
            name="Advanced Workflow",
            description="Advanced features",
            long_description="This workflow provides advanced features...",
            version="2.0.0",
            price=49.99,
            categories=["automation", "data"],
            tags=["api", "processing", "enterprise"],
            requirements=["python>=3.8", "requests"],
            screenshots=["screenshot1.png", "screenshot2.png"],
            demo_url="https://demo.example.com",
            support_url="https://support.example.com",
            license="Apache-2.0",
        )

        assert item.long_description == "This workflow provides advanced features..."
        assert item.price == 49.99
        assert item.categories == ["automation", "data"]
        assert item.tags == ["api", "processing", "enterprise"]
        assert item.requirements == ["python>=3.8", "requests"]
        assert item.screenshots == ["screenshot1.png", "screenshot2.png"]
        assert item.demo_url == "https://demo.example.com"
        assert item.support_url == "https://support.example.com"
        assert item.license == "Apache-2.0"

    def test_get_item(self, registry):
        """Test getting marketplace item."""
        item = registry.publish(
            workflow_id="workflow/get",
            publisher_id="publisher1",
            name="Get Test",
            description="Test getting",
        )

        # Get existing item
        retrieved = registry.get_item(item.item_id)
        assert retrieved is not None
        assert retrieved.name == "Get Test"

        # Get non-existent item
        retrieved = registry.get_item("nonexistent")
        assert retrieved is None

    def test_search_basic(self, registry):
        """Test basic search functionality."""
        # Publish multiple items
        registry.publish(
            workflow_id="w1",
            publisher_id="p1",
            name="Data Processor",
            description="Process data efficiently",
            tags=["data", "processing"],
        )
        registry.publish(
            workflow_id="w2",
            publisher_id="p1",
            name="API Connector",
            description="Connect to external APIs",
            tags=["api", "integration"],
        )
        registry.publish(
            workflow_id="w3",
            publisher_id="p2",
            name="Data Analyzer",
            description="Analyze data patterns",
            tags=["data", "analytics"],
        )

        # Search by query
        results, total = registry.search(query="data")
        assert total >= 2
        assert any("Data" in r.name for r in results)

        # Search with limit
        results, total = registry.search(query="data", limit=1)
        assert len(results) == 1
        assert total >= 2

    def test_search_with_filters(self, registry):
        """Test search with various filters."""
        # Publish items with different attributes
        item1 = registry.publish(
            workflow_id="w1",
            publisher_id="p1",
            name="Free Tool",
            description="Free automation",
            price=0.0,
            categories=["automation"],
            tags=["free"],
        )
        item2 = registry.publish(
            workflow_id="w2",
            publisher_id="p1",
            name="Premium Tool",
            description="Premium features",
            price=99.99,
            categories=["automation", "enterprise"],
            tags=["premium"],
        )
        item3 = registry.publish(
            workflow_id="w3",
            publisher_id="p2",
            name="Data Tool",
            description="Data processing",
            price=49.99,
            categories=["data"],
            tags=["data", "processing"],
        )

        # Give item1 a good rating
        registry._reviews[item1.workflow_id] = [
            MarketplaceReview(
                review_id="r1",
                workflow_id=item1.workflow_id,
                user_id="u1",
                rating=5,
                comment="Excellent!",
                created_at=datetime.now(timezone.utc),
            )
        ]
        registry._update_review_stats(item1)

        # Filter by category
        results, _ = registry.search(categories=["automation"])
        assert len(results) >= 2
        assert all("automation" in r.categories for r in results)

        # Filter by tags
        results, _ = registry.search(tags=["premium"])
        assert any(r.name == "Premium Tool" for r in results)

        # Filter by price range
        results, _ = registry.search(price_range=(0, 50))
        assert all(r.price <= 50 for r in results)

        # Filter by minimum rating
        results, _ = registry.search(min_rating=4.0)
        assert all(
            r.stats.average_rating >= 4.0 for r in results if r.stats.average_rating > 0
        )

    def test_search_sorting(self, registry):
        """Test search result sorting."""
        # Create items with different attributes
        items = []
        for i in range(3):
            item = registry.publish(
                workflow_id=f"w{i}",
                publisher_id="p1",
                name=f"Item {i}",
                description="Test",
                price=float(i * 10),
            )
            # Add some stats
            item.stats.total_installs = i * 10
            item.stats.average_rating = 5 - i
            item.stats.trending_score = i * 100
            items.append(item)

        # Sort by trending
        results, _ = registry.search(sort_by="trending")
        assert results[0].stats.trending_score >= results[1].stats.trending_score

        # Sort by rating
        results, _ = registry.search(sort_by="rating")
        assert results[0].stats.average_rating >= results[1].stats.average_rating

        # Sort by installs
        results, _ = registry.search(sort_by="installs")
        assert results[0].stats.total_installs >= results[1].stats.total_installs

        # Sort by price (low to high)
        results, _ = registry.search(sort_by="price_low")
        assert results[0].price <= results[1].price

        # Sort by price (high to low)
        results, _ = registry.search(sort_by="price_high")
        assert results[0].price >= results[1].price

    def test_get_featured(self, registry):
        """Test getting featured items."""
        # Create items
        regular = registry.publish(
            workflow_id="regular",
            publisher_id="p1",
            name="Regular Item",
            description="Not featured",
        )
        featured1 = registry.publish(
            workflow_id="featured1",
            publisher_id="p1",
            name="Featured 1",
            description="Featured item",
        )
        featured2 = registry.publish(
            workflow_id="featured2",
            publisher_id="p1",
            name="Featured 2",
            description="Another featured",
        )

        # Feature some items
        registry.feature_item(featured1.item_id, True)
        registry.feature_item(featured2.item_id, True)

        # Update trending scores
        featured1.stats.trending_score = 200
        featured2.stats.trending_score = 100

        # Get featured
        featured = registry.get_featured(limit=10)
        assert len(featured) == 2
        assert featured[0].item_id == featured1.item_id  # Higher trending score
        assert featured[1].item_id == featured2.item_id
        assert regular.item_id not in [f.item_id for f in featured]

    def test_install_item(self, registry):
        """Test installing marketplace item."""
        item = registry.publish(
            workflow_id="workflow/install",
            publisher_id="publisher1",
            name="Install Test",
            description="Test installation",
        )

        # Install item
        result = registry.install(
            item_id=item.item_id, user_id="user1", tenant_id="tenant1"
        )

        assert result["success"] is True
        assert result["workflow_id"] == "workflow/install"
        assert result["install_count"] == 1

        # Check tracking
        assert "workflow/install" in registry._installs
        assert "user1" in registry._installs["workflow/install"]
        assert "user1" in registry._user_installs
        assert "workflow/install" in registry._user_installs["user1"]

        # Check stats updated
        assert item.stats.total_installs == 1

        # Install again by same user (should not duplicate)
        result = registry.install(item.item_id, "user1", "tenant1")
        assert result["install_count"] == 1

        # Install by different user
        result = registry.install(item.item_id, "user2", "tenant2")
        assert result["install_count"] == 2
        assert item.stats.total_installs == 2

    def test_uninstall_item(self, registry):
        """Test uninstalling marketplace item."""
        item = registry.publish(
            workflow_id="workflow/uninstall",
            publisher_id="publisher1",
            name="Uninstall Test",
            description="Test uninstallation",
        )

        # Install first
        registry.install(item.item_id, "user1")
        assert item.stats.total_installs == 1

        # Uninstall
        result = registry.uninstall(item.item_id, "user1")
        assert result is True
        assert item.stats.total_installs == 0
        assert "user1" not in registry._installs.get("workflow/uninstall", [])

        # Uninstall non-existent
        result = registry.uninstall("nonexistent", "user1")
        assert result is False

    def test_add_review(self, registry):
        """Test adding reviews."""
        item = registry.publish(
            workflow_id="workflow/review",
            publisher_id="publisher1",
            name="Review Test",
            description="Test reviews",
        )

        # Add review without installation
        review1 = registry.add_review(
            item_id=item.item_id,
            user_id="user1",
            rating=4,
            comment="Good workflow, but could be better",
        )

        assert review1.review_id.startswith("rev_")
        assert review1.workflow_id == "workflow/review"
        assert review1.user_id == "user1"
        assert review1.rating == 4
        assert review1.comment == "Good workflow, but could be better"
        assert review1.is_verified_install is False

        # Install and add verified review
        registry.install(item.item_id, "user2")
        review2 = registry.add_review(
            item_id=item.item_id,
            user_id="user2",
            rating=5,
            comment="Excellent! Works perfectly",
        )
        assert review2.is_verified_install is True

        # Check stats updated
        assert item.stats.total_reviews == 2
        assert item.stats.average_rating == 4.5
        assert item.stats.rating_distribution[4] == 1
        assert item.stats.rating_distribution[5] == 1

    def test_get_reviews(self, registry):
        """Test getting reviews."""
        item = registry.publish(
            workflow_id="workflow/getreviews",
            publisher_id="publisher1",
            name="Get Reviews Test",
            description="Test getting reviews",
        )

        # Add multiple reviews
        for i in range(5):
            registry.add_review(
                item_id=item.item_id,
                user_id=f"user{i}",
                rating=5 - i,
                comment=f"Review {i}",
            )

        # Get all reviews
        reviews, total = registry.get_reviews(item.item_id)
        assert total == 5
        assert len(reviews) == 5

        # Check sorting (newest first)
        assert reviews[0].comment == "Review 4"

        # Get with pagination
        reviews, total = registry.get_reviews(item.item_id, limit=2, offset=1)
        assert len(reviews) == 2
        assert total == 5

    def test_get_user_installs(self, registry):
        """Test getting user's installed items."""
        # Create and install multiple items
        items = []
        for i in range(3):
            item = registry.publish(
                workflow_id=f"w{i}",
                publisher_id="p1",
                name=f"Item {i}",
                description="Test",
            )
            registry.install(item.item_id, "user1")
            items.append(item)

        # Install one more by different user
        registry.install(items[0].item_id, "user2")

        # Get user installs
        user_items = registry.get_user_installs("user1")
        assert len(user_items) == 3
        assert all(item in user_items for item in items)

        user2_items = registry.get_user_installs("user2")
        assert len(user2_items) == 1

    def test_get_publisher_items(self, registry):
        """Test getting publisher's items."""
        # Publish multiple items
        for i in range(3):
            registry.publish(
                workflow_id=f"pub1_w{i}",
                publisher_id="publisher1",
                name=f"Publisher 1 Item {i}",
                description="Test",
            )

        # Publish by different publisher
        registry.publish(
            workflow_id="pub2_w1",
            publisher_id="publisher2",
            name="Publisher 2 Item",
            description="Test",
        )

        # Get publisher items
        pub1_items = registry.get_publisher_items("publisher1")
        assert len(pub1_items) == 3
        assert all(item.publisher_id == "publisher1" for item in pub1_items)

        pub2_items = registry.get_publisher_items("publisher2")
        assert len(pub2_items) == 1

    def test_update_item(self, registry):
        """Test updating marketplace item."""
        item = registry.publish(
            workflow_id="workflow/update",
            publisher_id="publisher1",
            name="Update Test",
            description="Original description",
            version="1.0.0",
            price=0.0,
        )

        # Update item
        updated = registry.update_item(
            item.item_id,
            {
                "description": "Updated description",
                "long_description": "Now with detailed info",
                "version": "1.1.0",
                "price": 9.99,
                "tags": ["updated", "new"],
            },
        )

        assert updated.description == "Updated description"
        assert updated.long_description == "Now with detailed info"
        assert updated.version == "1.1.0"
        assert updated.price == 9.99
        assert updated.tags == ["updated", "new"]
        assert updated.updated_at > updated.created_at

        # Name should not be updatable
        registry.update_item(item.item_id, {"name": "Should Not Change"})
        assert updated.name == "Update Test"

    def test_feature_verify_item(self, registry):
        """Test featuring and verifying items."""
        item = registry.publish(
            workflow_id="workflow/special",
            publisher_id="publisher1",
            name="Special Item",
            description="Test featuring",
        )

        assert item.is_featured is False
        assert item.is_verified is False

        # Feature item
        registry.feature_item(item.item_id, True)
        assert item.is_featured is True

        # Unfeature
        registry.feature_item(item.item_id, False)
        assert item.is_featured is False

        # Verify item
        registry.verify_item(item.item_id, True)
        assert item.is_verified is True

    @pytest.mark.asyncio
    async def test_health_check(self, registry):
        """Test marketplace health check."""
        # Create some data
        for i in range(3):
            item = registry.publish(
                workflow_id=f"w{i}",
                publisher_id="p1",
                name=f"Item {i}",
                description="Test",
                price=0 if i == 0 else 10.0,
            )
            if i == 0:
                registry.feature_item(item.item_id, True)
            if i == 1:
                registry.verify_item(item.item_id, True)

            # Add install and review
            registry.install(item.item_id, f"user{i}")
            registry.add_review(item.item_id, f"user{i}", 5, "Great!")

        health = await registry.health_check()

        assert health["healthy"] is True
        assert health["total_items"] == 3
        assert health["public_items"] == 3
        assert health["featured_items"] == 1
        assert health["verified_items"] == 1
        assert health["total_installs"] == 3
        assert health["total_reviews"] == 3

    def test_marketplace_item_model(self):
        """Test MarketplaceItem model."""
        item = MarketplaceItem(
            item_id="mp_test",
            workflow_id="workflow/test",
            publisher_id="pub1",
            name="Test Item",
            description="Test description",
            long_description="Detailed description",
            version="1.0.0",
            price=0.0,
        )

        assert item.item_id == "mp_test"
        assert item.price == 0.0
        assert item.currency == "USD"
        assert item.license == "MIT"
        assert isinstance(item.stats, MarketplaceStats)

        # Test to_dict
        item_dict = item.to_dict()
        assert item_dict["item_id"] == "mp_test"
        assert "stats" in item_dict
        assert isinstance(item_dict["created_at"], str)
