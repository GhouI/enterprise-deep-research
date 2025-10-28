"""
Tally webhook router for receiving form submissions.

This router handles incoming webhooks from Tally forms and triggers
the market research and script generation workflow.
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Header
from typing import Optional
import hmac
import hashlib

from models.tally_workflow import (
    TallyWebhookPayload,
    TallyWebhookResponse,
    WorkflowStatusResponse,
    WorkflowStatus
)
from services.tally_workflow_service import get_workflow_service
from storage.workflow_storage import get_workflow_storage

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/tally", tags=["Tally Webhook"])


def verify_tally_signature(
    payload: bytes,
    signature: Optional[str],
    secret: str
) -> bool:
    """
    Verify Tally webhook signature for security.

    Args:
        payload: Raw request body bytes
        signature: Signature header from Tally
        secret: Tally webhook secret from environment

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature or not secret:
        return False

    try:
        # Compute HMAC-SHA256 signature
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Compare signatures
        return hmac.compare_digest(signature, expected_signature)

    except Exception as e:
        logger.error(f"Error verifying Tally signature: {str(e)}")
        return False


@router.post(
    "/webhook",
    response_model=TallyWebhookResponse,
    summary="Receive Tally form submissions",
    description="Webhook endpoint for Tally form submissions. Triggers market research workflow."
)
async def tally_webhook(
    payload: TallyWebhookPayload,
    background_tasks: BackgroundTasks,
    request: Request,
    x_tally_signature: Optional[str] = Header(None)
):
    """
    Receive Tally webhook and start workflow execution.

    This endpoint:
    1. Validates the webhook signature
    2. Returns immediate 200 OK to Tally
    3. Starts workflow execution in background

    The workflow includes:
    - Market research using agents and ValyuSearchTool
    - Script generation using agents
    - PDF generation
    - Slack delivery
    """
    logger.info(f"Received Tally webhook: event_type={payload.event_type}, event_id={payload.event_id}")

    try:
        # Verify webhook signature if secret is configured
        import os
        tally_secret = os.environ.get("TALLY_WEBHOOK_SECRET")

        if tally_secret:
            # Get raw request body for signature verification
            body = await request.body()

            if not verify_tally_signature(body, x_tally_signature, tally_secret):
                logger.warning("Invalid Tally webhook signature")
                raise HTTPException(status_code=401, detail="Invalid webhook signature")

            logger.info("Tally webhook signature verified")
        else:
            logger.warning("TALLY_WEBHOOK_SECRET not configured. Skipping signature verification.")

        # Get workflow service
        workflow_service = get_workflow_service()

        # Parse brand data to validate it early
        try:
            brand_data = workflow_service.parse_tally_submission(payload)
            logger.info(f"Parsed brand submission: {brand_data.brand_name} - {brand_data.product_name}")
        except ValueError as e:
            logger.error(f"Invalid Tally submission data: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

        # Generate workflow ID for tracking
        import uuid
        workflow_id = str(uuid.uuid4())

        # Start workflow execution in background
        background_tasks.add_task(
            workflow_service.execute_workflow,
            payload=payload,
            slack_channel=None  # Uses default from env
        )

        logger.info(f"Workflow started in background: {workflow_id}")

        # Return immediate response to Tally
        return TallyWebhookResponse(
            status="accepted",
            workflow_id=workflow_id,
            message="Workflow started successfully. You will receive updates in Slack.",
            status_url=f"/api/tally/workflow/{workflow_id}/status"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Tally webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/workflow/{workflow_id}/status",
    response_model=WorkflowStatusResponse,
    summary="Get workflow execution status",
    description="Check the status of a workflow execution"
)
async def get_workflow_status(workflow_id: str):
    """
    Get the current status of a workflow execution.

    Args:
        workflow_id: Unique workflow identifier

    Returns:
        WorkflowStatusResponse with current status and progress
    """
    logger.info(f"Status check requested for workflow: {workflow_id}")

    try:
        storage = get_workflow_storage()
        workflow = storage.get_workflow(workflow_id)

        if not workflow:
            logger.warning(f"Workflow not found: {workflow_id}")
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Map status to human-readable step description
        step_descriptions = {
            WorkflowStatus.PENDING: "Initializing workflow",
            WorkflowStatus.PARSING: "Parsing form submission",
            WorkflowStatus.MARKET_RESEARCH: "Conducting market research",
            WorkflowStatus.SCRIPT_GENERATION: "Generating ad scripts",
            WorkflowStatus.PDF_GENERATION: "Creating PDF report",
            WorkflowStatus.COMPLETED: "Workflow completed successfully",
            WorkflowStatus.FAILED: "Workflow failed with errors"
        }

        # Calculate progress percentage
        progress_map = {
            WorkflowStatus.PENDING: 0,
            WorkflowStatus.PARSING: 10,
            WorkflowStatus.MARKET_RESEARCH: 30,
            WorkflowStatus.SCRIPT_GENERATION: 60,
            WorkflowStatus.PDF_GENERATION: 85,
            WorkflowStatus.COMPLETED: 100,
            WorkflowStatus.FAILED: 0
        }

        return WorkflowStatusResponse(
            workflow_id=workflow.workflow_id,
            status=workflow.status,
            current_step=step_descriptions.get(workflow.status, "Unknown"),
            progress_percentage=progress_map.get(workflow.status, 0),
            result_url=workflow.pdf_url,
            error_message=workflow.error_message,
            created_at=workflow.created_at,
            estimated_completion=None  # Could add time estimation logic
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving workflow status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/workflows",
    summary="List recent workflows",
    description="Get a list of recent workflow executions"
)
async def list_workflows(
    limit: int = 20,
    status: Optional[str] = None
):
    """
    List recent workflow executions.

    Args:
        limit: Maximum number of workflows to return (default 20)
        status: Optional status filter (pending, completed, failed, etc.)

    Returns:
        List of workflow summaries
    """
    logger.info(f"Listing workflows: limit={limit}, status={status}")

    try:
        storage = get_workflow_storage()

        # Convert status string to enum if provided
        status_filter = None
        if status:
            try:
                status_filter = WorkflowStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        workflows = storage.list_workflows(limit=limit, status=status_filter)

        # Return summary data
        return {
            "count": len(workflows),
            "workflows": [
                {
                    "workflow_id": w.workflow_id,
                    "brand_name": w.brand_data.brand_name,
                    "product_name": w.brand_data.product_name,
                    "status": w.status,
                    "created_at": w.created_at.isoformat(),
                    "completed_at": w.completed_at.isoformat() if w.completed_at else None,
                    "pdf_url": w.pdf_url
                }
                for w in workflows
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing workflows: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/test",
    summary="Test Tally webhook integration",
    description="Test endpoint for debugging Tally webhook integration"
)
async def test_tally_webhook(payload: dict):
    """
    Test endpoint to debug Tally webhook payload structure.

    This endpoint logs the raw payload for debugging purposes.
    Use this to understand the actual structure of Tally webhooks.
    """
    logger.info("=== TEST TALLY WEBHOOK ===")
    logger.info(f"Payload: {payload}")
    logger.info("=========================")

    return {
        "status": "received",
        "message": "Test payload logged successfully",
        "payload_keys": list(payload.keys()) if isinstance(payload, dict) else "Not a dict"
    }
