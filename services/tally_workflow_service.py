"""
Tally workflow orchestration service.

This service orchestrates the complete workflow from Tally form submission to
PDF generation and Slack delivery:
1. Parse Tally submission
2. Execute market research with agents (marketPrompt.md)
3. Execute script generation with agents (scriptGenerator.md)
4. Generate PDF report
5. Deliver to Slack

Uses the existing multi-agent research system from src/graph.py
"""

import os
import logging
import asyncio
import uuid
from typing import Dict, Any, Optional
from pathlib import Path

from models.tally_workflow import (
    TallyWebhookPayload,
    BrandIntakeData,
    WorkflowStatus,
    WorkflowResult
)
from services.slack_service import get_slack_service
from services.pdf_service import get_pdf_service
from storage.workflow_storage import get_workflow_storage
from services.research import ResearchService

logger = logging.getLogger(__name__)


class TallyWorkflowService:
    """Service for orchestrating Tally form submission workflows."""

    def __init__(self):
        """Initialize workflow service with dependencies."""
        self.slack_service = get_slack_service()
        self.pdf_service = get_pdf_service()
        self.workflow_storage = get_workflow_storage()
        self.research_service = ResearchService

        # Load prompt templates
        self.market_prompt_template = self._load_prompt_template("marketPrompt.md")
        self.script_prompt_template = self._load_prompt_template("scriptGenerator.md")

        logger.info("TallyWorkflowService initialized")

    def _load_prompt_template(self, filename: str) -> Optional[str]:
        """
        Load a prompt template file.

        Args:
            filename: Name of the prompt file

        Returns:
            Template content as string, or None if not found
        """
        try:
            template_path = Path(filename)
            if not template_path.exists():
                logger.warning(f"Prompt template not found: {filename}")
                return None

            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            logger.info(f"Loaded prompt template: {filename} ({len(content)} chars)")
            return content

        except Exception as e:
            logger.error(f"Error loading prompt template {filename}: {str(e)}")
            return None

    def parse_tally_submission(self, payload: TallyWebhookPayload) -> BrandIntakeData:
        """
        Parse Tally webhook payload into structured brand data.

        Args:
            payload: Tally webhook payload

        Returns:
            Parsed BrandIntakeData

        Raises:
            ValueError: If required fields are missing
        """
        try:
            # Extract form responses from Tally payload
            # Tally structure: payload.data.fields contains array of {key, value}
            form_data = payload.data.get('fields', [])

            # Create mapping of field keys to values
            field_map = {}
            for field in form_data:
                key = field.get('key', '')
                value = field.get('value', '')
                field_map[key] = value

            # Map to BrandIntakeData structure
            # Adjust these field keys based on actual Tally form field names
            brand_data = BrandIntakeData(
                brand_name=field_map.get('brand_name', field_map.get('brand', '')),
                website_url=field_map.get('website_url', field_map.get('website', None)),
                product_name=field_map.get('product_name', field_map.get('product', '')),
                product_description=field_map.get('product_description', field_map.get('description', '')),
                target_audience=field_map.get('target_audience', field_map.get('audience', '')),
                unique_value_props=field_map.get('unique_value_props', field_map.get('value_props', '')),
                core_benefits=field_map.get('core_benefits', field_map.get('benefits', '')),
                current_marketing=field_map.get('current_marketing', None),
                budget_constraints=field_map.get('budget_constraints', None),
                competitors=field_map.get('competitors', None),
                additional_context=field_map.get('additional_context', None)
            )

            logger.info(f"Successfully parsed Tally submission for brand: {brand_data.brand_name}")
            return brand_data

        except Exception as e:
            logger.error(f"Error parsing Tally submission: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to parse Tally submission: {str(e)}")

    async def execute_workflow(
        self,
        payload: TallyWebhookPayload,
        slack_channel: Optional[str] = None
    ) -> str:
        """
        Execute the complete workflow asynchronously.

        Args:
            payload: Tally webhook payload
            slack_channel: Optional Slack channel override

        Returns:
            Workflow ID

        This method is called as a background task and handles the entire workflow.
        """
        workflow_id = str(uuid.uuid4())

        try:
            # Step 1: Parse Tally submission
            logger.info(f"[{workflow_id}] Step 1: Parsing Tally submission")
            brand_data = self.parse_tally_submission(payload)

            # Create workflow record
            workflow = self.workflow_storage.create_workflow(workflow_id, brand_data)

            # Step 2: Send Slack start notification
            logger.info(f"[{workflow_id}] Step 2: Sending Slack start notification")
            thread_ts = self.slack_service.send_workflow_start_notification(
                workflow_id=workflow_id,
                brand_name=brand_data.brand_name,
                product_name=brand_data.product_name,
                channel=slack_channel
            )

            if thread_ts:
                self.workflow_storage.save_slack_thread(workflow_id, thread_ts)

            # Step 3: Execute market research
            logger.info(f"[{workflow_id}] Step 3: Executing market research")
            self.workflow_storage.update_workflow_status(workflow_id, WorkflowStatus.MARKET_RESEARCH)

            self.slack_service.send_progress_update(
                workflow_id=workflow_id,
                status="market_research",
                message="Starting comprehensive market research...",
                channel=slack_channel,
                thread_ts=thread_ts
            )

            market_research_result = await self._execute_market_research(
                workflow_id=workflow_id,
                brand_data=brand_data
            )

            # Save market research results
            self.workflow_storage.save_market_research(
                workflow_id=workflow_id,
                research_summary=market_research_result.get('summary', ''),
                research_data=market_research_result
            )

            # Step 4: Execute script generation
            logger.info(f"[{workflow_id}] Step 4: Executing script generation")
            self.workflow_storage.update_workflow_status(workflow_id, WorkflowStatus.SCRIPT_GENERATION)

            self.slack_service.send_progress_update(
                workflow_id=workflow_id,
                status="script_generation",
                message="Generating UGC and Podcast ad scripts...",
                channel=slack_channel,
                thread_ts=thread_ts
            )

            generated_scripts = await self._execute_script_generation(
                workflow_id=workflow_id,
                brand_data=brand_data,
                market_research=market_research_result
            )

            # Save generated scripts
            self.workflow_storage.save_generated_scripts(workflow_id, generated_scripts)

            # Step 5: Generate PDF
            logger.info(f"[{workflow_id}] Step 5: Generating PDF report")
            self.workflow_storage.update_workflow_status(workflow_id, WorkflowStatus.PDF_GENERATION)

            self.slack_service.send_progress_update(
                workflow_id=workflow_id,
                status="pdf_generation",
                message="Generating PDF report...",
                channel=slack_channel,
                thread_ts=thread_ts
            )

            pdf_path = self.pdf_service.generate_workflow_pdf(
                workflow_id=workflow_id,
                brand_data=brand_data.model_dump(),
                market_research=market_research_result.get('summary', ''),
                generated_scripts=generated_scripts
            )

            if not pdf_path:
                raise Exception("PDF generation failed")

            # Step 6: Upload PDF to Slack
            logger.info(f"[{workflow_id}] Step 6: Uploading PDF to Slack")

            pdf_url = self.slack_service.upload_pdf_file(
                file_path=pdf_path,
                filename=f"{brand_data.brand_name}_research_report.pdf",
                title=f"Market Research & Scripts - {brand_data.brand_name}",
                channel=slack_channel,
                thread_ts=thread_ts
            )

            # Save PDF info
            self.workflow_storage.save_pdf_info(
                workflow_id=workflow_id,
                pdf_file_path=pdf_path,
                pdf_url=pdf_url
            )

            # Step 7: Send completion notification
            logger.info(f"[{workflow_id}] Step 7: Sending completion notification")
            self.workflow_storage.update_workflow_status(workflow_id, WorkflowStatus.COMPLETED)

            self.slack_service.send_workflow_completion_notification(
                workflow_id=workflow_id,
                brand_name=brand_data.brand_name,
                product_name=brand_data.product_name,
                pdf_url=pdf_url,
                channel=slack_channel,
                thread_ts=thread_ts
            )

            logger.info(f"[{workflow_id}] Workflow completed successfully")
            return workflow_id

        except Exception as e:
            logger.error(f"[{workflow_id}] Workflow failed: {str(e)}", exc_info=True)

            # Update workflow status to failed
            self.workflow_storage.update_workflow_status(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                error_message=str(e)
            )

            # Send error notification to Slack
            workflow = self.workflow_storage.get_workflow(workflow_id)
            if workflow:
                self.slack_service.send_workflow_error_notification(
                    workflow_id=workflow_id,
                    brand_name=workflow.brand_data.brand_name,
                    product_name=workflow.brand_data.product_name,
                    error_message=str(e),
                    channel=slack_channel,
                    thread_ts=workflow.slack_thread_ts
                )

            raise

    async def _execute_market_research(
        self,
        workflow_id: str,
        brand_data: BrandIntakeData
    ) -> Dict[str, Any]:
        """
        Execute market research using the agent system with marketPrompt.md.

        Args:
            workflow_id: Unique workflow identifier
            brand_data: Parsed brand intake data

        Returns:
            Dictionary containing research results
        """
        try:
            # Build research query from brand data and market prompt template
            research_query = self._build_market_research_query(brand_data)

            logger.info(f"[{workflow_id}] Starting market research with query length: {len(research_query)}")

            # Execute research using existing ResearchService
            # This uses the multi-agent system with ValyuSearchTool
            result = await self.research_service.conduct_research(
                query=research_query,
                extra_effort=True,  # Enable comprehensive research
                minimum_effort=False,
                benchmark_mode=False,
                streaming=False,
                stream_id=None,
                queue=None,
                provider="openrouter",  # Use OpenRouter with Claude
                model="anthropic/claude-sonnet-4",
                uploaded_data_content=None,
                database_info=None,
                uploaded_files=None,
                steering_enabled=False
            )

            # Extract summary from result
            if hasattr(result, 'running_summary'):
                summary = result.running_summary
            else:
                summary = result.get('running_summary', '')

            logger.info(f"[{workflow_id}] Market research completed. Summary length: {len(summary)}")

            return {
                'summary': summary,
                'full_result': result,
                'brand_data': brand_data.model_dump()
            }

        except Exception as e:
            logger.error(f"[{workflow_id}] Error in market research: {str(e)}", exc_info=True)
            raise

    def _build_market_research_query(self, brand_data: BrandIntakeData) -> str:
        """
        Build the market research query from brand data and template.

        Args:
            brand_data: Parsed brand intake data

        Returns:
            Complete research query string
        """
        # Start with the market prompt template
        query = self.market_prompt_template or ""

        # Append brand-specific context
        query += f"\n\n## BRAND INFORMATION FROM INTAKE FORM\n\n"
        query += f"**Brand Name:** {brand_data.brand_name}\n"
        query += f"**Product Name:** {brand_data.product_name}\n"

        if brand_data.website_url:
            query += f"**Website:** {brand_data.website_url}\n"

        query += f"\n**Product Description:**\n{brand_data.product_description}\n"
        query += f"\n**Target Audience:**\n{brand_data.target_audience}\n"
        query += f"\n**Unique Value Propositions:**\n{brand_data.unique_value_props}\n"
        query += f"\n**Core Benefits:**\n{brand_data.core_benefits}\n"

        if brand_data.current_marketing:
            query += f"\n**Current Marketing Approach:**\n{brand_data.current_marketing}\n"

        if brand_data.competitors:
            query += f"\n**Known Competitors:**\n{brand_data.competitors}\n"

        if brand_data.additional_context:
            query += f"\n**Additional Context:**\n{brand_data.additional_context}\n"

        return query

    async def _execute_script_generation(
        self,
        workflow_id: str,
        brand_data: BrandIntakeData,
        market_research: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute script generation using the agent system with scriptGenerator.md.

        Args:
            workflow_id: Unique workflow identifier
            brand_data: Parsed brand intake data
            market_research: Market research results

        Returns:
            Dictionary containing generated scripts
        """
        try:
            # Build script generation query from research data and script prompt template
            script_query = self._build_script_generation_query(brand_data, market_research)

            logger.info(f"[{workflow_id}] Starting script generation with query length: {len(script_query)}")

            # Execute script generation using ResearchService
            result = await self.research_service.conduct_research(
                query=script_query,
                extra_effort=False,  # Scripts don't need extra research loops
                minimum_effort=False,
                benchmark_mode=False,
                streaming=False,
                stream_id=None,
                queue=None,
                provider="openrouter",
                model="anthropic/claude-sonnet-4",
                uploaded_data_content=None,
                database_info=None,
                uploaded_files=None,
                steering_enabled=False
            )

            # Extract generated scripts from result
            if hasattr(result, 'running_summary'):
                scripts_text = result.running_summary
            else:
                scripts_text = result.get('running_summary', '')

            # Parse scripts (assuming they're formatted as UGC and Podcast sections)
            scripts = self._parse_generated_scripts(scripts_text)

            logger.info(f"[{workflow_id}] Script generation completed. Generated {len(scripts.get('ugc_scripts', []))} UGC and {len(scripts.get('podcast_scripts', []))} Podcast scripts")

            return scripts

        except Exception as e:
            logger.error(f"[{workflow_id}] Error in script generation: {str(e)}", exc_info=True)
            raise

    def _build_script_generation_query(
        self,
        brand_data: BrandIntakeData,
        market_research: Dict[str, Any]
    ) -> str:
        """
        Build the script generation query from market research and template.

        Args:
            brand_data: Parsed brand intake data
            market_research: Market research results

        Returns:
            Complete script generation query string
        """
        # Start with the script prompt template
        query = self.script_prompt_template or ""

        # Append brand and product information
        query += f"\n\n## PRODUCT INFORMATION\n\n"
        query += f"**Brand:** {brand_data.brand_name}\n"
        query += f"**Product:** {brand_data.product_name}\n"

        if brand_data.website_url:
            query += f"**Website:** {brand_data.website_url}\n"

        # Append market research findings
        query += f"\n\n## MARKET RESEARCH FINDINGS\n\n"
        query += market_research.get('summary', '')

        return query

    def _parse_generated_scripts(self, scripts_text: str) -> Dict[str, Any]:
        """
        Parse generated scripts from text format.

        Args:
            scripts_text: Raw script text from generation

        Returns:
            Dictionary with ugc_scripts and podcast_scripts lists
        """
        # Simple parsing logic - split by script delimiters
        # Adjust based on actual output format from scriptGenerator.md

        ugc_scripts = []
        podcast_scripts = []

        # Split by common script delimiters
        sections = scripts_text.split('\n\n')

        current_type = None
        current_script = []

        for section in sections:
            section_lower = section.lower().strip()

            # Detect UGC section
            if 'ugc script' in section_lower or '## ugc' in section_lower:
                current_type = 'ugc'
                continue

            # Detect Podcast section
            if 'podcast script' in section_lower or '## podcast' in section_lower:
                current_type = 'podcast'
                continue

            # Collect script content
            if current_type and section.strip():
                # Check if this is a new script (starts with number or "Script")
                if section.strip().startswith(('1.', '2.', '3.', 'Script #', '###')):
                    # Save previous script
                    if current_script:
                        script_text = '\n\n'.join(current_script)
                        if current_type == 'ugc':
                            ugc_scripts.append(script_text)
                        elif current_type == 'podcast':
                            podcast_scripts.append(script_text)
                        current_script = []

                current_script.append(section)

        # Save last script
        if current_script:
            script_text = '\n\n'.join(current_script)
            if current_type == 'ugc':
                ugc_scripts.append(script_text)
            elif current_type == 'podcast':
                podcast_scripts.append(script_text)

        logger.info(f"Parsed {len(ugc_scripts)} UGC scripts and {len(podcast_scripts)} Podcast scripts")

        return {
            'ugc_scripts': ugc_scripts,
            'podcast_scripts': podcast_scripts,
            'raw_text': scripts_text
        }


# Singleton instance
_workflow_service = None


def get_workflow_service() -> TallyWorkflowService:
    """Get or create the singleton workflow service instance."""
    global _workflow_service
    if _workflow_service is None:
        _workflow_service = TallyWorkflowService()
    return _workflow_service
