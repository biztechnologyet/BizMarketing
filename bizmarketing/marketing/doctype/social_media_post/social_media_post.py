import frappe
from frappe.model.document import Document

class SocialMediaPost(Document):
	def on_update(self):
		self.process_automation()

	def on_submit(self):
		self.process_automation()

	def process_automation(self):
		"""
		If the post is marked as Approved, automatically generate
		Publishing Queue entries for all selected platforms.
		"""
		if self.status != "Approved":
			return

		if not self.platform:
			frappe.msgprint("Please select at least one Platform for this post before approving.")
			return

		platforms = [p.strip() for p in self.platform.split(",")]
		
		# For each platform, check if a queue item already exists to avoid duplicates
		# Note: In a true multi-account setup, we would link this. Here we grab the first matching account.
		for plat in platforms:
			# Find an active account for this platform
			account = frappe.db.get_value("Social Media Account", {"platform": plat}, "name")
			if not account:
				frappe.msgprint(f"No configured Social Media Account found for {plat}. Cannot queue.")
				continue
				
			exists = frappe.db.exists("Publishing Queue", {
				"social_media_post": self.name,
				"platform": plat
			})
			
			if not exists:
				queue_doc = frappe.new_doc("Publishing Queue")
				queue_doc.social_media_post = self.name
				queue_doc.company = self.company
				queue_doc.platform = plat
				queue_doc.social_media_account = account
				queue_doc.status = "Pending"
				queue_doc.retry_count = 0
				queue_doc.scheduled_time = self.scheduled_time or frappe.utils.now_datetime()
				queue_doc.insert(ignore_permissions=True)
				
				frappe.msgprint(f"Post automatically queued for {plat}!")
