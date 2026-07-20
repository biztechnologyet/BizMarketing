import frappe
import json
import unittest
from unittest.mock import patch, MagicMock
from frappe.tests.utils import FrappeTestCase


class TestProcessQueueItem(FrappeTestCase):
    def setUp(self):
        self.queue_id = "TEST-QUEUE-001"

    @patch("bizmarketing.tasks.TelegramClient")
    @patch("bizmarketing.tasks.frappe.get_doc")
    def test_image_url_resolved_for_local_path(self, mock_get_doc, mock_telegram):
        """Test that local /files/ paths get resolved to absolute URL"""
        from bizmarketing.tasks import process_queue_item

        mock_queue = MagicMock()
        mock_queue.name = self.queue_id
        mock_queue.social_media_account = "SMA-TEST"
        mock_queue.social_media_post = "SMP-TEST"
        mock_queue.platform = "Telegram"

        mock_acc = MagicMock()
        mock_acc.get_password.return_value = "fake-token"

        mock_post = MagicMock()
        mock_post.image_url = "/files/test_image.jpg"
        mock_post.content = "<p>Test content</p>"
        mock_post.cta = "Visit now"

        def get_doc_side_effect(doctype, name):
            if doctype == "Publishing Queue":
                return mock_queue
            elif doctype == "Social Media Account":
                return mock_acc
            elif doctype == "Social Media Post":
                return mock_post
            return None

        mock_get_doc.side_effect = get_doc_side_effect

        mock_client = MagicMock()
        mock_client.publish.return_value = "12345"
        mock_telegram.return_value = mock_client

        with patch("frappe.utils.get_url", return_value="https://ethiobiz.et"):
            with patch("frappe.utils.strip_html", return_value="Test content"):
                process_queue_item(self.queue_id)

        # Verify image_url was resolved before passing to publish
        call_kwargs = mock_client.publish.call_args
        self.assertIsNotNone(call_kwargs, "publish() should have been called")
        _, _, call_image_url = call_kwargs[0]
        self.assertEqual(
            call_image_url,
            "https://ethiobiz.et/files/test_image.jpg",
            "Local /files/ path should be resolved to absolute URL",
        )

    @patch("bizmarketing.tasks.TelegramClient")
    @patch("bizmarketing.tasks.frappe.get_doc")
    def test_image_url_passthrough_for_absolute_url(self, mock_get_doc, mock_telegram):
        """Test that absolute https URLs are passed through unchanged"""
        from bizmarketing.tasks import process_queue_item

        mock_queue = MagicMock()
        mock_queue.name = self.queue_id
        mock_queue.social_media_account = "SMA-TEST"
        mock_queue.social_media_post = "SMP-TEST"
        mock_queue.platform = "Telegram"

        mock_acc = MagicMock()
        mock_acc.get_password.return_value = "fake-token"

        mock_post = MagicMock()
        mock_post.image_url = "https://cdn.example.com/photo.jpg"
        mock_post.content = "<p>Test</p>"
        mock_post.cta = ""

        def get_doc_side_effect(doctype, name):
            if doctype == "Publishing Queue":
                return mock_queue
            elif doctype == "Social Media Account":
                return mock_acc
            elif doctype == "Social Media Post":
                return mock_post
            return None

        mock_get_doc.side_effect = get_doc_side_effect

        mock_client = MagicMock()
        mock_client.publish.return_value = "12345"
        mock_telegram.return_value = mock_client

        with patch("frappe.utils.strip_html", return_value="Test"):
            process_queue_item(self.queue_id)

        call_kwargs = mock_client.publish.call_args
        _, _, call_image_url = call_kwargs[0]
        self.assertEqual(
            call_image_url,
            "https://cdn.example.com/photo.jpg",
            "Absolute HTTPS URL should pass through unchanged",
        )

    @patch("bizmarketing.tasks.TelegramClient")
    @patch("bizmarketing.tasks.frappe.get_doc")
    def test_empty_image_url_skipped(self, mock_get_doc, mock_telegram):
        """Test that empty image_url passes None instead of resolving"""
        from bizmarketing.tasks import process_queue_item

        mock_queue = MagicMock()
        mock_queue.name = self.queue_id
        mock_queue.social_media_account = "SMA-TEST"
        mock_queue.social_media_post = "SMP-TEST"
        mock_queue.platform = "Telegram"

        mock_acc = MagicMock()
        mock_acc.get_password.return_value = "fake-token"

        mock_post = MagicMock()
        mock_post.image_url = None
        mock_post.content = "Test"
        mock_post.cta = ""

        def get_doc_side_effect(doctype, name):
            if doctype == "Publishing Queue":
                return mock_queue
            elif doctype == "Social Media Account":
                return mock_acc
            elif doctype == "Social Media Post":
                return mock_post
            return None

        mock_get_doc.side_effect = get_doc_side_effect

        mock_client = MagicMock()
        mock_client.publish.return_value = "12345"
        mock_telegram.return_value = mock_client

        with patch("frappe.utils.strip_html", return_value="Test"):
            process_queue_item(self.queue_id)

        call_kwargs = mock_client.publish.call_args
        _, _, call_image_url = call_kwargs[0]
        self.assertIsNone(call_image_url, "Empty image_url should remain None")

    @patch("bizmarketing.tasks.frappe.get_all")
    @patch("bizmarketing.tasks.process_queue_item")
    def test_process_publishing_queue_filters(self, mock_process, mock_get_all):
        """Test that process_publishing_queue only picks eligible items"""
        from bizmarketing.tasks import process_publishing_queue

        mock_get_all.return_value = [{"name": "PQ-TEST"}]
        process_publishing_queue()

        # Verify the filter includes retry_count < 3
        call_filters = mock_get_all.call_args[1]["filters"]
        self.assertIn("retry_count", call_filters)
        self.assertEqual(call_filters["retry_count"], ("<", 3))

    @patch("bizmarketing.tasks.frappe.get_all")
    @patch("bizmarketing.tasks.frappe.enqueue")
    def test_fetch_engagement_metrics_only_posted(self, mock_enqueue, mock_get_all):
        """Test fetch_engagement_metrics only processes Posted posts"""
        from bizmarketing.tasks import fetch_engagement_metrics

        mock_get_all.return_value = [{"name": "SMP-TEST"}]
        fetch_engagement_metrics()

        call_filters = mock_get_all.call_args[1]["filters"]
        self.assertEqual(call_filters["status"], "Posted")


if __name__ == "__main__":
    unittest.main()
