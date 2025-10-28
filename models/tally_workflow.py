from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    PARSING = "parsing"
    MARKET_RESEARCH = "market_research"
    SCRIPT_GENERATION = "script_generation"
    PDF_GENERATION = "pdf_generation"
    COMPLETED = "completed"
    FAILED = "failed"


class TallyWebhookPayload(BaseModel):
    """
    Model for incoming Tally webhook payload.
    Based on Tally's webhook structure.
    """
    event_id: str = Field(..., description="Unique event identifier from Tally")
    event_type: str = Field(..., description="Type of event (e.g., 'FORM_RESPONSE')")
    created_at: str = Field(..., description="ISO timestamp of event creation")
    data: Dict[str, Any] = Field(..., description="Form submission data")


class BrandIntakeData(BaseModel):
    """
    Parsed brand intake form data from Tally submission.
    Maps to the fields expected in marketPrompt.md workflow.
    """
    brand_name: str = Field(..., description="Brand/company name")
    website_url: Optional[str] = Field(None, description="Brand website URL")
    product_name: str = Field(..., description="Product name")
    product_description: str = Field(..., description="Detailed product description")
    target_audience: str = Field(..., description="Target customer profile")
    unique_value_props: str = Field(..., description="Unique value propositions")
    core_benefits: str = Field(..., description="Core product benefits")
    current_marketing: Optional[str] = Field(None, description="Current marketing approach")
    budget_constraints: Optional[str] = Field(None, description="Budget and constraints")
    competitors: Optional[str] = Field(None, description="Known competitors")
    additional_context: Optional[str] = Field(None, description="Any additional context")


class WorkflowResult(BaseModel):
    """
    Complete workflow execution result.
    """
    workflow_id: str = Field(..., description="Unique workflow execution ID")
    status: WorkflowStatus = Field(..., description="Current workflow status")
    brand_data: BrandIntakeData = Field(..., description="Parsed brand intake data")
    market_research_summary: Optional[str] = Field(None, description="Market research findings")
    market_research_data: Optional[Dict[str, Any]] = Field(None, description="Raw market research data")
    generated_scripts: Optional[Dict[str, Any]] = Field(None, description="Generated UGC and Podcast scripts")
    pdf_file_path: Optional[str] = Field(None, description="Path to generated PDF file")
    pdf_url: Optional[str] = Field(None, description="Slack URL to uploaded PDF")
    error_message: Optional[str] = Field(None, description="Error message if workflow failed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Workflow creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Workflow completion timestamp")
    slack_thread_ts: Optional[str] = Field(None, description="Slack thread timestamp for tracking messages")


class WorkflowStatusResponse(BaseModel):
    """
    Response model for workflow status queries.
    """
    workflow_id: str = Field(..., description="Unique workflow execution ID")
    status: WorkflowStatus = Field(..., description="Current workflow status")
    current_step: str = Field(..., description="Human-readable current step description")
    progress_percentage: int = Field(..., description="Progress percentage (0-100)")
    result_url: Optional[str] = Field(None, description="URL to final PDF if completed")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Workflow start time")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")


class TallyWebhookResponse(BaseModel):
    """
    Response model for Tally webhook endpoint.
    """
    status: str = Field(..., description="Status of webhook processing")
    workflow_id: str = Field(..., description="Unique workflow execution ID")
    message: str = Field(..., description="Human-readable message")
    status_url: str = Field(..., description="URL to check workflow status")
