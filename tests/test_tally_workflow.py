"""
Integration tests for Tally webhook workflow.

These tests verify the complete workflow from Tally submission to PDF delivery.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from models.tally_workflow import (
    TallyWebhookPayload,
    BrandIntakeData,
    WorkflowStatus
)
from services.tally_workflow_service import TallyWorkflowService
from storage.workflow_storage import WorkflowStorage


@pytest.fixture
def sample_tally_payload():
    """Create a sample Tally webhook payload for testing."""
    return TallyWebhookPayload(
        event_id="evt_123456",
        event_type="FORM_RESPONSE",
        created_at=datetime.utcnow().isoformat(),
        data={
            "fields": [
                {"key": "brand_name", "value": "Acme Corp"},
                {"key": "product_name", "value": "Magic Widget"},
                {"key": "product_description", "value": "A revolutionary widget that solves all your problems"},
                {"key": "target_audience", "value": "Tech-savvy millennials aged 25-40"},
                {"key": "unique_value_props", "value": "10x faster, 50% cheaper, eco-friendly"},
                {"key": "core_benefits", "value": "Saves time, reduces costs, sustainable"},
                {"key": "website", "value": "https://acmecorp.example.com"},
                {"key": "competitors", "value": "CompetitorA, CompetitorB"},
            ]
        }
    )


@pytest.fixture
def workflow_service():
    """Create a workflow service instance for testing."""
    return TallyWorkflowService()


@pytest.fixture
def workflow_storage():
    """Create a workflow storage instance for testing."""
    return WorkflowStorage(storage_dir="outputs/test_workflows")


class TestTallyWorkflowService:
    """Test cases for Tally workflow service."""

    def test_parse_tally_submission(self, workflow_service, sample_tally_payload):
        """Test parsing Tally webhook payload into BrandIntakeData."""
        brand_data = workflow_service.parse_tally_submission(sample_tally_payload)

        assert isinstance(brand_data, BrandIntakeData)
        assert brand_data.brand_name == "Acme Corp"
        assert brand_data.product_name == "Magic Widget"
        assert brand_data.target_audience == "Tech-savvy millennials aged 25-40"
        assert brand_data.website_url == "https://acmecorp.example.com"

    def test_parse_tally_submission_missing_fields(self, workflow_service):
        """Test parsing with missing required fields raises error."""
        incomplete_payload = TallyWebhookPayload(
            event_id="evt_123",
            event_type="FORM_RESPONSE",
            created_at=datetime.utcnow().isoformat(),
            data={"fields": []}
        )

        with pytest.raises(ValueError):
            workflow_service.parse_tally_submission(incomplete_payload)

    def test_build_market_research_query(self, workflow_service, sample_tally_payload):
        """Test building market research query from brand data."""
        brand_data = workflow_service.parse_tally_submission(sample_tally_payload)
        query = workflow_service._build_market_research_query(brand_data)

        assert "Acme Corp" in query
        assert "Magic Widget" in query
        assert "Tech-savvy millennials" in query
        assert len(query) > 100  # Should include template + brand info

    @pytest.mark.asyncio
    async def test_execute_market_research_mocked(self, workflow_service, sample_tally_payload):
        """Test market research execution with mocked ResearchService."""
        brand_data = workflow_service.parse_tally_submission(sample_tally_payload)

        # Mock the ResearchService.conduct_research method
        with patch.object(workflow_service.research_service, 'conduct_research') as mock_research:
            # Setup mock response
            mock_result = Mock()
            mock_result.running_summary = "Comprehensive market research findings..."
            mock_research.return_value = mock_result

            # Execute market research
            result = await workflow_service._execute_market_research(
                workflow_id="test_123",
                brand_data=brand_data
            )

            # Verify
            assert 'summary' in result
            assert 'brand_data' in result
            assert result['summary'] == "Comprehensive market research findings..."
            mock_research.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_script_generation_mocked(self, workflow_service, sample_tally_payload):
        """Test script generation with mocked ResearchService."""
        brand_data = workflow_service.parse_tally_submission(sample_tally_payload)
        market_research = {
            'summary': 'Market research findings...',
            'brand_data': brand_data.model_dump()
        }

        # Mock the ResearchService.conduct_research method
        with patch.object(workflow_service.research_service, 'conduct_research') as mock_research:
            # Setup mock response with scripts
            mock_result = Mock()
            mock_result.running_summary = """
            ## UGC Scripts

            ### UGC Script #1
            Hook: Amazing widget discovery...
            Body: Let me tell you about this widget...
            CTA: Get yours today!

            ## Podcast Scripts

            ### Podcast Script #1
            Host 1: Have you heard about the Magic Widget?
            Host 2: Tell me more!
            """
            mock_research.return_value = mock_result

            # Execute script generation
            result = await workflow_service._execute_script_generation(
                workflow_id="test_123",
                brand_data=brand_data,
                market_research=market_research
            )

            # Verify
            assert 'ugc_scripts' in result
            assert 'podcast_scripts' in result
            assert len(result['ugc_scripts']) > 0 or len(result['podcast_scripts']) > 0
            mock_research.assert_called_once()


class TestWorkflowStorage:
    """Test cases for workflow storage."""

    def test_create_workflow(self, workflow_storage, sample_tally_payload):
        """Test creating a new workflow record."""
        brand_data = BrandIntakeData(
            brand_name="Test Brand",
            product_name="Test Product",
            product_description="Test description",
            target_audience="Test audience",
            unique_value_props="Test props",
            core_benefits="Test benefits"
        )

        workflow = workflow_storage.create_workflow(
            workflow_id="test_workflow_1",
            brand_data=brand_data
        )

        assert workflow.workflow_id == "test_workflow_1"
        assert workflow.status == WorkflowStatus.PENDING
        assert workflow.brand_data.brand_name == "Test Brand"

    def test_get_workflow(self, workflow_storage, sample_tally_payload):
        """Test retrieving a workflow by ID."""
        brand_data = BrandIntakeData(
            brand_name="Test Brand",
            product_name="Test Product",
            product_description="Test description",
            target_audience="Test audience",
            unique_value_props="Test props",
            core_benefits="Test benefits"
        )

        # Create workflow
        created = workflow_storage.create_workflow(
            workflow_id="test_workflow_2",
            brand_data=brand_data
        )

        # Retrieve workflow
        retrieved = workflow_storage.get_workflow("test_workflow_2")

        assert retrieved is not None
        assert retrieved.workflow_id == created.workflow_id
        assert retrieved.brand_data.brand_name == "Test Brand"

    def test_update_workflow_status(self, workflow_storage):
        """Test updating workflow status."""
        brand_data = BrandIntakeData(
            brand_name="Test Brand",
            product_name="Test Product",
            product_description="Test description",
            target_audience="Test audience",
            unique_value_props="Test props",
            core_benefits="Test benefits"
        )

        # Create workflow
        workflow_storage.create_workflow(
            workflow_id="test_workflow_3",
            brand_data=brand_data
        )

        # Update status
        success = workflow_storage.update_workflow_status(
            workflow_id="test_workflow_3",
            status=WorkflowStatus.MARKET_RESEARCH
        )

        assert success is True

        # Verify update
        workflow = workflow_storage.get_workflow("test_workflow_3")
        assert workflow.status == WorkflowStatus.MARKET_RESEARCH

    def test_save_market_research(self, workflow_storage):
        """Test saving market research results."""
        brand_data = BrandIntakeData(
            brand_name="Test Brand",
            product_name="Test Product",
            product_description="Test description",
            target_audience="Test audience",
            unique_value_props="Test props",
            core_benefits="Test benefits"
        )

        # Create workflow
        workflow_storage.create_workflow(
            workflow_id="test_workflow_4",
            brand_data=brand_data
        )

        # Save research
        research_summary = "Comprehensive market research findings..."
        research_data = {"key_findings": ["finding1", "finding2"]}

        success = workflow_storage.save_market_research(
            workflow_id="test_workflow_4",
            research_summary=research_summary,
            research_data=research_data
        )

        assert success is True

        # Verify save
        workflow = workflow_storage.get_workflow("test_workflow_4")
        assert workflow.market_research_summary == research_summary
        assert workflow.market_research_data == research_data

    def test_save_generated_scripts(self, workflow_storage):
        """Test saving generated scripts."""
        brand_data = BrandIntakeData(
            brand_name="Test Brand",
            product_name="Test Product",
            product_description="Test description",
            target_audience="Test audience",
            unique_value_props="Test props",
            core_benefits="Test benefits"
        )

        # Create workflow
        workflow_storage.create_workflow(
            workflow_id="test_workflow_5",
            brand_data=brand_data
        )

        # Save scripts
        scripts = {
            "ugc_scripts": ["Script 1", "Script 2"],
            "podcast_scripts": ["Podcast 1", "Podcast 2"]
        }

        success = workflow_storage.save_generated_scripts(
            workflow_id="test_workflow_5",
            scripts=scripts
        )

        assert success is True

        # Verify save
        workflow = workflow_storage.get_workflow("test_workflow_5")
        assert workflow.generated_scripts == scripts


class TestSlackIntegration:
    """Test cases for Slack integration (mocked)."""

    @pytest.mark.asyncio
    async def test_slack_notifications_disabled(self):
        """Test that workflow works when Slack is disabled."""
        from services.slack_service import SlackService

        # Create service without token
        with patch.dict('os.environ', {}, clear=True):
            slack_service = SlackService()

            assert slack_service.is_enabled() is False

            # These should not raise errors
            result = slack_service.send_workflow_start_notification(
                workflow_id="test",
                brand_name="Test",
                product_name="Test"
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_slack_notifications_enabled(self):
        """Test Slack notifications with mocked client."""
        from services.slack_service import SlackService

        with patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'xoxb-test-token'}):
            slack_service = SlackService()

            # Mock the Slack client
            slack_service.client = MagicMock()
            slack_service.client.chat_postMessage.return_value = {"ok": True, "ts": "1234567890.123456"}

            assert slack_service.is_enabled() is True

            # Test start notification
            thread_ts = slack_service.send_workflow_start_notification(
                workflow_id="test_123",
                brand_name="Acme Corp",
                product_name="Magic Widget"
            )

            assert thread_ts is not None
            slack_service.client.chat_postMessage.assert_called_once()


class TestPDFGeneration:
    """Test cases for PDF generation."""

    def test_pdf_generation(self):
        """Test PDF generation with sample data."""
        from services.pdf_service import PDFService

        pdf_service = PDFService(output_dir="outputs/test_pdfs")

        brand_data = {
            'brand_name': 'Acme Corp',
            'product_name': 'Magic Widget',
            'product_description': 'A revolutionary widget',
            'target_audience': 'Tech enthusiasts',
            'unique_value_props': '10x faster',
            'core_benefits': 'Saves time'
        }

        market_research = """
        ## Market Research Findings

        The market analysis reveals strong demand for innovative widgets.

        ## Competitive Landscape

        Current solutions lack key features that our product provides.
        """

        generated_scripts = {
            'ugc_scripts': ['UGC Script 1 content here...', 'UGC Script 2 content here...'],
            'podcast_scripts': ['Podcast Script 1 content here...']
        }

        # Generate PDF
        pdf_path = pdf_service.generate_workflow_pdf(
            workflow_id="test_pdf_1",
            brand_data=brand_data,
            market_research=market_research,
            generated_scripts=generated_scripts
        )

        assert pdf_path is not None
        assert pdf_path.endswith('.pdf')

        # Verify file exists
        from pathlib import Path
        assert Path(pdf_path).exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
