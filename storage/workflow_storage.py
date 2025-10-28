"""
Workflow storage module for persisting workflow state and results.

This module provides in-memory and file-based storage for workflow execution data.
For production, this can be extended to use a proper database.
"""

import json
import logging
from typing import Dict, Optional, List
from pathlib import Path
from datetime import datetime

from models.tally_workflow import WorkflowResult, WorkflowStatus, BrandIntakeData

logger = logging.getLogger(__name__)


class WorkflowStorage:
    """Storage service for workflow execution data."""

    def __init__(self, storage_dir: str = "outputs/workflows"):
        """
        Initialize workflow storage.

        Args:
            storage_dir: Directory to store workflow data files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache for active workflows
        self._workflows: Dict[str, WorkflowResult] = {}

        logger.info(f"Workflow storage initialized with directory: {self.storage_dir}")

    def create_workflow(
        self,
        workflow_id: str,
        brand_data: BrandIntakeData
    ) -> WorkflowResult:
        """
        Create a new workflow execution record.

        Args:
            workflow_id: Unique workflow identifier
            brand_data: Parsed brand intake data

        Returns:
            WorkflowResult object
        """
        workflow = WorkflowResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
            brand_data=brand_data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self._workflows[workflow_id] = workflow
        self._save_workflow_to_disk(workflow)

        logger.info(f"Created new workflow: {workflow_id}")
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowResult]:
        """
        Retrieve a workflow by ID.

        Args:
            workflow_id: Unique workflow identifier

        Returns:
            WorkflowResult object or None if not found
        """
        # Try in-memory cache first
        if workflow_id in self._workflows:
            return self._workflows[workflow_id]

        # Try loading from disk
        workflow = self._load_workflow_from_disk(workflow_id)
        if workflow:
            self._workflows[workflow_id] = workflow

        return workflow

    def update_workflow_status(
        self,
        workflow_id: str,
        status: WorkflowStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update the status of a workflow.

        Args:
            workflow_id: Unique workflow identifier
            status: New workflow status
            error_message: Optional error message if status is FAILED

        Returns:
            True if successful, False otherwise
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            logger.error(f"Workflow not found: {workflow_id}")
            return False

        workflow.status = status
        workflow.updated_at = datetime.utcnow()

        if error_message:
            workflow.error_message = error_message

        if status == WorkflowStatus.COMPLETED or status == WorkflowStatus.FAILED:
            workflow.completed_at = datetime.utcnow()

        self._workflows[workflow_id] = workflow
        self._save_workflow_to_disk(workflow)

        logger.info(f"Updated workflow {workflow_id} status to {status}")
        return True

    def save_market_research(
        self,
        workflow_id: str,
        research_summary: str,
        research_data: Optional[Dict] = None
    ) -> bool:
        """
        Save market research results to workflow.

        Args:
            workflow_id: Unique workflow identifier
            research_summary: Text summary of research findings
            research_data: Optional structured research data

        Returns:
            True if successful, False otherwise
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            logger.error(f"Workflow not found: {workflow_id}")
            return False

        workflow.market_research_summary = research_summary
        workflow.market_research_data = research_data
        workflow.updated_at = datetime.utcnow()

        self._workflows[workflow_id] = workflow
        self._save_workflow_to_disk(workflow)

        logger.info(f"Saved market research for workflow: {workflow_id}")
        return True

    def save_generated_scripts(
        self,
        workflow_id: str,
        scripts: Dict
    ) -> bool:
        """
        Save generated ad scripts to workflow.

        Args:
            workflow_id: Unique workflow identifier
            scripts: Dictionary containing UGC and Podcast scripts

        Returns:
            True if successful, False otherwise
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            logger.error(f"Workflow not found: {workflow_id}")
            return False

        workflow.generated_scripts = scripts
        workflow.updated_at = datetime.utcnow()

        self._workflows[workflow_id] = workflow
        self._save_workflow_to_disk(workflow)

        logger.info(f"Saved generated scripts for workflow: {workflow_id}")
        return True

    def save_pdf_info(
        self,
        workflow_id: str,
        pdf_file_path: str,
        pdf_url: Optional[str] = None
    ) -> bool:
        """
        Save PDF file information to workflow.

        Args:
            workflow_id: Unique workflow identifier
            pdf_file_path: Local path to generated PDF
            pdf_url: Optional Slack URL to uploaded PDF

        Returns:
            True if successful, False otherwise
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            logger.error(f"Workflow not found: {workflow_id}")
            return False

        workflow.pdf_file_path = pdf_file_path
        workflow.pdf_url = pdf_url
        workflow.updated_at = datetime.utcnow()

        self._workflows[workflow_id] = workflow
        self._save_workflow_to_disk(workflow)

        logger.info(f"Saved PDF info for workflow: {workflow_id}")
        return True

    def save_slack_thread(
        self,
        workflow_id: str,
        thread_ts: str
    ) -> bool:
        """
        Save Slack thread timestamp to workflow.

        Args:
            workflow_id: Unique workflow identifier
            thread_ts: Slack thread timestamp

        Returns:
            True if successful, False otherwise
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            logger.error(f"Workflow not found: {workflow_id}")
            return False

        workflow.slack_thread_ts = thread_ts
        workflow.updated_at = datetime.utcnow()

        self._workflows[workflow_id] = workflow
        self._save_workflow_to_disk(workflow)

        logger.info(f"Saved Slack thread for workflow: {workflow_id}")
        return True

    def list_workflows(
        self,
        limit: int = 50,
        status: Optional[WorkflowStatus] = None
    ) -> List[WorkflowResult]:
        """
        List workflows with optional filtering.

        Args:
            limit: Maximum number of workflows to return
            status: Optional status filter

        Returns:
            List of WorkflowResult objects
        """
        workflows = list(self._workflows.values())

        if status:
            workflows = [w for w in workflows if w.status == status]

        # Sort by created_at descending
        workflows.sort(key=lambda w: w.created_at, reverse=True)

        return workflows[:limit]

    def _save_workflow_to_disk(self, workflow: WorkflowResult) -> None:
        """
        Save workflow data to disk as JSON.

        Args:
            workflow: WorkflowResult object to save
        """
        try:
            workflow_file = self.storage_dir / f"{workflow.workflow_id}.json"

            # Convert to dict and handle datetime serialization
            workflow_dict = workflow.model_dump()
            workflow_dict['created_at'] = workflow.created_at.isoformat()
            workflow_dict['updated_at'] = workflow.updated_at.isoformat()
            if workflow.completed_at:
                workflow_dict['completed_at'] = workflow.completed_at.isoformat()

            with open(workflow_file, 'w', encoding='utf-8') as f:
                json.dump(workflow_dict, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved workflow to disk: {workflow_file}")

        except Exception as e:
            logger.error(f"Error saving workflow to disk: {str(e)}", exc_info=True)

    def _load_workflow_from_disk(self, workflow_id: str) -> Optional[WorkflowResult]:
        """
        Load workflow data from disk.

        Args:
            workflow_id: Unique workflow identifier

        Returns:
            WorkflowResult object or None if not found
        """
        try:
            workflow_file = self.storage_dir / f"{workflow_id}.json"

            if not workflow_file.exists():
                return None

            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow_dict = json.load(f)

            # Convert ISO datetime strings back to datetime objects
            workflow_dict['created_at'] = datetime.fromisoformat(workflow_dict['created_at'])
            workflow_dict['updated_at'] = datetime.fromisoformat(workflow_dict['updated_at'])
            if workflow_dict.get('completed_at'):
                workflow_dict['completed_at'] = datetime.fromisoformat(workflow_dict['completed_at'])

            # Convert brand_data dict to BrandIntakeData model
            workflow_dict['brand_data'] = BrandIntakeData(**workflow_dict['brand_data'])

            # Create WorkflowResult from dict
            workflow = WorkflowResult(**workflow_dict)

            logger.debug(f"Loaded workflow from disk: {workflow_file}")
            return workflow

        except Exception as e:
            logger.error(f"Error loading workflow from disk: {str(e)}", exc_info=True)
            return None

    def cleanup_old_workflows(self, days: int = 30) -> int:
        """
        Remove workflow files older than specified days.

        Args:
            days: Number of days to keep workflows

        Returns:
            Number of workflows deleted
        """
        try:
            cutoff_date = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)
            deleted_count = 0

            for workflow_file in self.storage_dir.glob("*.json"):
                if workflow_file.stat().st_mtime < cutoff_date:
                    workflow_id = workflow_file.stem
                    workflow_file.unlink()

                    # Remove from memory cache if present
                    if workflow_id in self._workflows:
                        del self._workflows[workflow_id]

                    deleted_count += 1

            logger.info(f"Cleaned up {deleted_count} old workflows (older than {days} days)")
            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old workflows: {str(e)}", exc_info=True)
            return 0


# Singleton instance
_workflow_storage = None


def get_workflow_storage() -> WorkflowStorage:
    """Get or create the singleton workflow storage instance."""
    global _workflow_storage
    if _workflow_storage is None:
        _workflow_storage = WorkflowStorage()
    return _workflow_storage
