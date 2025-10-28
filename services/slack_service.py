"""
Slack service for sending notifications and uploading files.

This module provides functionality to:
- Send workflow start/completion notifications to Slack channels
- Upload PDF files to Slack
- Manage threaded conversations for workflow tracking
"""

import os
import logging
from typing import Optional, Dict, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


class SlackService:
    """Service for Slack notifications and file uploads."""

    def __init__(self):
        """Initialize Slack service with API token from environment."""
        self.slack_token = os.environ.get("SLACK_BOT_TOKEN")
        self.default_channel = os.environ.get("SLACK_DEFAULT_CHANNEL", "#marketing-research")

        if not self.slack_token:
            logger.warning("SLACK_BOT_TOKEN not found in environment. Slack notifications will be disabled.")
            self.client = None
        else:
            self.client = WebClient(token=self.slack_token)
            logger.info(f"Slack service initialized with default channel: {self.default_channel}")

    def is_enabled(self) -> bool:
        """Check if Slack service is enabled."""
        return self.client is not None

    def send_workflow_start_notification(
        self,
        workflow_id: str,
        brand_name: str,
        product_name: str,
        channel: Optional[str] = None
    ) -> Optional[str]:
        """
        Send notification when workflow starts.

        Args:
            workflow_id: Unique workflow identifier
            brand_name: Name of the brand
            product_name: Name of the product
            channel: Slack channel to post to (uses default if not provided)

        Returns:
            Thread timestamp (ts) for follow-up messages, or None if failed
        """
        if not self.is_enabled():
            logger.warning("Slack notifications are disabled. Skipping start notification.")
            return None

        channel = channel or self.default_channel

        message_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚀 Market Research Workflow Started",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Brand:*\n{brand_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Product:*\n{product_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Workflow ID:*\n`{workflow_id}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Status:*\n⏳ In Progress"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "This workflow includes market research and script generation. Estimated time: 10-15 minutes."
                    }
                ]
            }
        ]

        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=f"Market research workflow started for {brand_name} - {product_name}",
                blocks=message_blocks
            )

            thread_ts = response.get("ts")
            logger.info(f"Workflow start notification sent to {channel}. Thread TS: {thread_ts}")
            return thread_ts

        except SlackApiError as e:
            logger.error(f"Error sending Slack start notification: {e.response['error']}")
            return None

    def send_workflow_completion_notification(
        self,
        workflow_id: str,
        brand_name: str,
        product_name: str,
        pdf_url: Optional[str] = None,
        channel: Optional[str] = None,
        thread_ts: Optional[str] = None
    ) -> bool:
        """
        Send notification when workflow completes successfully.

        Args:
            workflow_id: Unique workflow identifier
            brand_name: Name of the brand
            product_name: Name of the product
            pdf_url: URL to the uploaded PDF file
            channel: Slack channel to post to (uses default if not provided)
            thread_ts: Thread timestamp to reply in the same thread

        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            logger.warning("Slack notifications are disabled. Skipping completion notification.")
            return False

        channel = channel or self.default_channel

        message_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "✅ Market Research Workflow Completed",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Brand:*\n{brand_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Product:*\n{product_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Workflow ID:*\n`{workflow_id}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Status:*\n✅ Completed"
                    }
                ]
            }
        ]

        if pdf_url:
            message_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"📄 *Research Report & Scripts:* <{pdf_url}|Download PDF>"
                }
            })

        message_blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "The PDF contains comprehensive market research and generated ad scripts."
                }
            ]
        })

        try:
            self.client.chat_postMessage(
                channel=channel,
                text=f"Market research workflow completed for {brand_name} - {product_name}",
                blocks=message_blocks,
                thread_ts=thread_ts
            )

            logger.info(f"Workflow completion notification sent to {channel}")
            return True

        except SlackApiError as e:
            logger.error(f"Error sending Slack completion notification: {e.response['error']}")
            return False

    def send_workflow_error_notification(
        self,
        workflow_id: str,
        brand_name: str,
        product_name: str,
        error_message: str,
        channel: Optional[str] = None,
        thread_ts: Optional[str] = None
    ) -> bool:
        """
        Send notification when workflow fails with an error.

        Args:
            workflow_id: Unique workflow identifier
            brand_name: Name of the brand
            product_name: Name of the product
            error_message: Description of the error
            channel: Slack channel to post to (uses default if not provided)
            thread_ts: Thread timestamp to reply in the same thread

        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            logger.warning("Slack notifications are disabled. Skipping error notification.")
            return False

        channel = channel or self.default_channel

        message_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "❌ Market Research Workflow Failed",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Brand:*\n{brand_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Product:*\n{product_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Workflow ID:*\n`{workflow_id}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Status:*\n❌ Failed"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Error:*\n```{error_message[:500]}```"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Please check the logs for more details."
                    }
                ]
            }
        ]

        try:
            self.client.chat_postMessage(
                channel=channel,
                text=f"Market research workflow failed for {brand_name} - {product_name}",
                blocks=message_blocks,
                thread_ts=thread_ts
            )

            logger.info(f"Workflow error notification sent to {channel}")
            return True

        except SlackApiError as e:
            logger.error(f"Error sending Slack error notification: {e.response['error']}")
            return False

    def upload_pdf_file(
        self,
        file_path: str,
        filename: str,
        title: str,
        channel: Optional[str] = None,
        thread_ts: Optional[str] = None
    ) -> Optional[str]:
        """
        Upload a PDF file to Slack.

        Args:
            file_path: Local path to the PDF file
            filename: Name for the file in Slack
            title: Title for the file upload
            channel: Slack channel to upload to (uses default if not provided)
            thread_ts: Thread timestamp to upload in the same thread

        Returns:
            URL to the uploaded file, or None if failed
        """
        if not self.is_enabled():
            logger.warning("Slack notifications are disabled. Skipping file upload.")
            return None

        channel = channel or self.default_channel

        try:
            response = self.client.files_upload_v2(
                channel=channel,
                file=file_path,
                filename=filename,
                title=title,
                thread_ts=thread_ts
            )

            # Extract file URL from response
            if response.get("ok") and response.get("file"):
                file_url = response["file"].get("permalink")
                logger.info(f"PDF uploaded to Slack: {file_url}")
                return file_url
            else:
                logger.error(f"File upload response missing expected data: {response}")
                return None

        except SlackApiError as e:
            logger.error(f"Error uploading PDF to Slack: {e.response['error']}")
            return None

    def send_progress_update(
        self,
        workflow_id: str,
        status: str,
        message: str,
        channel: Optional[str] = None,
        thread_ts: Optional[str] = None
    ) -> bool:
        """
        Send a progress update message to a workflow thread.

        Args:
            workflow_id: Unique workflow identifier
            status: Current status (e.g., "market_research", "script_generation")
            message: Progress message to send
            channel: Slack channel to post to (uses default if not provided)
            thread_ts: Thread timestamp to reply in the same thread

        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            return False

        channel = channel or self.default_channel

        # Map status to emoji
        status_emoji_map = {
            "parsing": "📋",
            "market_research": "🔍",
            "script_generation": "✍️",
            "pdf_generation": "📄",
            "completed": "✅",
            "failed": "❌"
        }

        emoji = status_emoji_map.get(status, "⏳")

        try:
            self.client.chat_postMessage(
                channel=channel,
                text=f"{emoji} {message}",
                thread_ts=thread_ts
            )

            logger.info(f"Progress update sent to {channel}: {message}")
            return True

        except SlackApiError as e:
            logger.error(f"Error sending progress update: {e.response['error']}")
            return False


# Singleton instance
_slack_service = None


def get_slack_service() -> SlackService:
    """Get or create the singleton Slack service instance."""
    global _slack_service
    if _slack_service is None:
        _slack_service = SlackService()
    return _slack_service
