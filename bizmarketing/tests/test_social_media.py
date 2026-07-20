import frappe
import json
import unittest
from unittest.mock import patch, MagicMock
from frappe.tests.utils import FrappeTestCase


class TestPublishNow(FrappeTestCase):
    def setUp(self):
        self.post_name = "SMP-TEST"

    @patch("bizmarketing.api.social_media.frappe.get_all")
    @patch("bizmarketing.api.social_media.frappe.get_doc")
    @patch("bizmarketing.tasks.process_queue_item")
    def test_publish_now_filters_is_active_accounts(
        self, mock_process, mock_get_doc, mock_get_all
    ):
        """Test publish_now filters accounts by is_active=1"""
        from bizmarketing.api.social_media import publish_now

        mock_post = MagicMock()
        mock_post.name = self.post_name
        mock_post.status = "Approved"
        mock_post.platform = "Telegram"
        mock_post.company = "Biz Technology Solutions"

        def get_doc_side_effect(doctype, name):
            if doctype == "Social Media Post":
                return mock_post
            return MagicMock()

        mock_get_doc.side_effect = get_doc_side_effect

        # First call: check for existing queue items (return empty)
        # Second call: find accounts (return SMA-0001)
        def get_all_side_effect(doctype, filters=None, **kwargs):
            if doctype == "Publishing Queue":
                return []
            if doctype == "Social Media Account":
                # Verify is_active filter is present
                self.assertIn(
                    "is_active",
                    filters,
                    "publish_now should filter by is_active=1",
                )
                self.assertEqual(
                    filters["is_active"],
                    1,
                    "publish_now should require is_active=1",
                )
                self.assertEqual(
                    filters["company"],
                    "Biz Technology Solutions",
                    "publish_now should filter by company",
                )
                return [{"name": "SMA-0001"}]
            return []

        mock_get_all.side_effect = get_all_side_effect

        mock_process.return_value = None

        publish_now(self.post_name)

    @patch("bizmarketing.api.social_media.frappe.get_all")
    @patch("bizmarketing.api.social_media.frappe.get_doc")
    @patch("bizmarketing.tasks.process_queue_item")
    def test_publish_now_deletes_exhausted_queue_items(
        self, mock_process, mock_get_doc, mock_get_all
    ):
        """Test publish_now deletes queue items with retry_count >= 3"""
        from bizmarketing.api.social_media import publish_now

        mock_post = MagicMock()
        mock_post.name = self.post_name
        mock_post.status = "Approved"
        mock_post.platform = "Telegram"
        mock_post.company = "Biz Technology Solutions"

        mock_exhausted_queue = MagicMock()
        mock_exhausted_queue.name = "PQ-EXHAUSTED"
        mock_exhausted_queue.retry_count = 5  # Exhausted retries

        def get_doc_side_effect(doctype, name):
            if doctype == "Social Media Post":
                return mock_post
            if doctype == "Publishing Queue":
                return mock_exhausted_queue
            return MagicMock()

        mock_get_doc.side_effect = get_doc_side_effect

        def get_all_side_effect(doctype, filters=None, **kwargs):
            if doctype == "Publishing Queue":
                return [{"name": "PQ-EXHAUSTED"}]
            if doctype == "Social Media Account":
                return [{"name": "SMA-0001"}]
            return []

        mock_get_all.side_effect = get_all_side_effect

        publish_now(self.post_name)

        # Verify the exhausted queue item was deleted
        mock_exhausted_queue.delete.assert_called_once()

    @patch("bizmarketing.api.social_media.frappe.get_all")
    @patch("bizmarketing.api.social_media.frappe.get_doc")
    @patch("bizmarketing.tasks.process_queue_item")
    def test_publish_now_keeps_valid_queue_items(
        self, mock_process, mock_get_doc, mock_get_all
    ):
        """Test publish_now keeps queue items with retry_count < 3"""
        from bizmarketing.api.social_media import publish_now

        mock_post = MagicMock()
        mock_post.name = self.post_name
        mock_post.status = "Approved"
        mock_post.platform = "Telegram"
        mock_post.company = "Biz Technology Solutions"

        mock_valid_queue = MagicMock()
        mock_valid_queue.name = "PQ-VALID"
        mock_valid_queue.retry_count = 1  # Still has retries left

        def get_doc_side_effect(doctype, name):
            if doctype == "Social Media Post":
                return mock_post
            if doctype == "Publishing Queue":
                return mock_valid_queue
            return MagicMock()

        mock_get_doc.side_effect = get_doc_side_effect

        def get_all_side_effect(doctype, filters=None, **kwargs):
            if doctype == "Publishing Queue":
                return [{"name": "PQ-VALID"}]
            return []

        mock_get_all.side_effect = get_all_side_effect

        publish_now(self.post_name)

        # Verify valid queue item was NOT deleted
        mock_valid_queue.delete.assert_not_called()


class TestBulkSchedulePosts(FrappeTestCase):
    @patch("bizmarketing.api.social_media.frappe.get_all")
    @patch("bizmarketing.api.social_media.frappe.get_doc")
    @patch("bizmarketing.api.social_media.frappe.new_doc")
    @patch("bizmarketing.api.social_media.frappe.db.exists")
    def test_bulk_schedule_filters_is_active_accounts(
        self, mock_exists, mock_new_doc, mock_get_doc, mock_get_all
    ):
        """Test bulk_schedule_posts filters accounts by is_active=1"""
        from bizmarketing.api.social_media import bulk_schedule_posts

        mock_campaign = MagicMock()
        mock_campaign.name = "CAMP-TEST"

        mock_post = MagicMock()
        mock_post.name = "SMP-TEST"
        mock_post.platform = "Telegram"
        mock_post.company = "Biz Technology Solutions"
        mock_post.scheduled_time = None

        def get_doc_side_effect(doctype, name):
            if doctype == "Marketing Campaign":
                return mock_campaign
            if doctype == "Social Media Post":
                return mock_post
            return MagicMock()

        mock_get_doc.side_effect = get_doc_side_effect
        mock_get_all.return_value = [{"name": "SMP-TEST"}]
        mock_exists.return_value = False

        mock_queue_doc = MagicMock()
        mock_new_doc.return_value = mock_queue_doc

        bulk_schedule_posts("CAMP-TEST")

        # Verify find accounts called with is_active=1
        account_call = [
            call
            for call in mock_get_all.call_args_list
            if call[0][0] == "Social Media Account"
        ]
        self.assertTrue(len(account_call) > 0, "Should search for Social Media Account")
        filters = account_call[0][1]["filters"]
        self.assertIn("is_active", filters)
        self.assertEqual(filters["is_active"], 1)
        self.assertEqual(filters["company"], "Biz Technology Solutions")


if __name__ == "__main__":
    unittest.main()
