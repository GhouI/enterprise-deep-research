"""
PDF generation service for market research reports and ad scripts.

This module provides functionality to generate professionally formatted PDFs
from market research data and generated ad scripts.
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

logger = logging.getLogger(__name__)


class PDFService:
    """Service for generating PDF reports from workflow results."""

    def __init__(self, output_dir: str = "outputs/pdfs"):
        """
        Initialize PDF service.

        Args:
            output_dir: Directory to save generated PDFs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"PDF service initialized with output directory: {self.output_dir}")

    def _get_custom_styles(self) -> Dict[str, ParagraphStyle]:
        """
        Create custom paragraph styles for the PDF.

        Returns:
            Dictionary of custom styles
        """
        styles = getSampleStyleSheet()

        # Custom styles
        custom_styles = {
            'CustomTitle': ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=24,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
                alignment=TA_CENTER
            ),
            'CustomHeading1': ParagraphStyle(
                'CustomHeading1',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#2c3e50'),
                spaceBefore=20,
                spaceAfter=12,
                borderPadding=5
            ),
            'CustomHeading2': ParagraphStyle(
                'CustomHeading2',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#34495e'),
                spaceBefore=15,
                spaceAfter=10
            ),
            'CustomBodyText': ParagraphStyle(
                'CustomBodyText',
                parent=styles['BodyText'],
                fontSize=11,
                alignment=TA_JUSTIFY,
                spaceAfter=12
            ),
            'ScriptText': ParagraphStyle(
                'ScriptText',
                parent=styles['Code'],
                fontSize=10,
                leftIndent=20,
                rightIndent=20,
                spaceBefore=10,
                spaceAfter=10,
                borderPadding=10,
                backColor=colors.HexColor('#f8f9fa')
            )
        }

        return custom_styles

    def generate_workflow_pdf(
        self,
        workflow_id: str,
        brand_data: Dict[str, Any],
        market_research: Optional[str] = None,
        generated_scripts: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Generate a complete PDF report from workflow results.

        Args:
            workflow_id: Unique workflow identifier
            brand_data: Brand intake data
            market_research: Market research summary text
            generated_scripts: Dictionary containing UGC and Podcast scripts

        Returns:
            Path to the generated PDF file, or None if failed
        """
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            brand_name_safe = brand_data.get('brand_name', 'unknown').replace(' ', '_').lower()
            filename = f"{brand_name_safe}_research_scripts_{timestamp}.pdf"
            pdf_path = self.output_dir / filename

            # Create PDF document
            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )

            # Get custom styles
            custom_styles = self._get_custom_styles()

            # Build story (content)
            story = []

            # Title page
            story.append(Spacer(1, 0.5 * inch))
            story.append(Paragraph(
                "Market Research Report & Ad Scripts",
                custom_styles['CustomTitle']
            ))
            story.append(Spacer(1, 0.3 * inch))

            # Brand information table
            brand_info_data = [
                ["Brand", brand_data.get('brand_name', 'N/A')],
                ["Product", brand_data.get('product_name', 'N/A')],
                ["Workflow ID", workflow_id],
                ["Generated", datetime.now().strftime("%B %d, %Y at %I:%M %p")]
            ]

            brand_info_table = Table(brand_info_data, colWidths=[2 * inch, 4 * inch])
            brand_info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7'))
            ]))

            story.append(brand_info_table)
            story.append(Spacer(1, 0.5 * inch))

            # Brand intake summary
            story.append(Paragraph("Brand & Product Overview", custom_styles['CustomHeading1']))
            story.append(Spacer(1, 0.2 * inch))

            if brand_data.get('product_description'):
                story.append(Paragraph(
                    f"<b>Product Description:</b><br/>{brand_data['product_description']}",
                    custom_styles['CustomBodyText']
                ))

            if brand_data.get('target_audience'):
                story.append(Paragraph(
                    f"<b>Target Audience:</b><br/>{brand_data['target_audience']}",
                    custom_styles['CustomBodyText']
                ))

            if brand_data.get('unique_value_props'):
                story.append(Paragraph(
                    f"<b>Unique Value Propositions:</b><br/>{brand_data['unique_value_props']}",
                    custom_styles['CustomBodyText']
                ))

            story.append(PageBreak())

            # Market Research Section
            if market_research:
                story.append(Paragraph("Market Research Findings", custom_styles['CustomHeading1']))
                story.append(Spacer(1, 0.2 * inch))

                # Split research into paragraphs (split by double newline)
                research_paragraphs = market_research.split('\n\n')
                for para in research_paragraphs:
                    if para.strip():
                        # Check if it's a heading (starts with ##)
                        if para.strip().startswith('##'):
                            heading_text = para.strip().replace('##', '').strip()
                            story.append(Paragraph(heading_text, custom_styles['CustomHeading2']))
                        else:
                            story.append(Paragraph(para.strip(), custom_styles['CustomBodyText']))

                story.append(PageBreak())

            # Generated Scripts Section
            if generated_scripts:
                story.append(Paragraph("Generated Ad Scripts", custom_styles['CustomHeading1']))
                story.append(Spacer(1, 0.3 * inch))

                # UGC Scripts
                if generated_scripts.get('ugc_scripts'):
                    story.append(Paragraph("UGC Scripts", custom_styles['CustomHeading2']))
                    story.append(Spacer(1, 0.15 * inch))

                    for i, script in enumerate(generated_scripts['ugc_scripts'], 1):
                        story.append(Paragraph(
                            f"<b>UGC Script #{i}</b>",
                            custom_styles['CustomBodyText']
                        ))
                        story.append(Paragraph(
                            script.replace('\n', '<br/>'),
                            custom_styles['ScriptText']
                        ))
                        story.append(Spacer(1, 0.2 * inch))

                    story.append(PageBreak())

                # Podcast Scripts
                if generated_scripts.get('podcast_scripts'):
                    story.append(Paragraph("Podcast Ad Scripts", custom_styles['CustomHeading2']))
                    story.append(Spacer(1, 0.15 * inch))

                    for i, script in enumerate(generated_scripts['podcast_scripts'], 1):
                        story.append(Paragraph(
                            f"<b>Podcast Script #{i}</b>",
                            custom_styles['CustomBodyText']
                        ))
                        story.append(Paragraph(
                            script.replace('\n', '<br/>'),
                            custom_styles['ScriptText']
                        ))
                        story.append(Spacer(1, 0.2 * inch))

            # Build PDF
            doc.build(story)

            logger.info(f"PDF generated successfully: {pdf_path}")
            return str(pdf_path)

        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
            return None

    def generate_simple_pdf(
        self,
        content: str,
        title: str,
        filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a simple PDF from text content.

        Args:
            content: Text content to include in PDF
            title: PDF title
            filename: Optional custom filename

        Returns:
            Path to the generated PDF file, or None if failed
        """
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"report_{timestamp}.pdf"

            pdf_path = self.output_dir / filename

            # Create PDF document
            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )

            # Get styles
            custom_styles = self._get_custom_styles()

            # Build story
            story = []
            story.append(Paragraph(title, custom_styles['CustomTitle']))
            story.append(Spacer(1, 0.5 * inch))

            # Split content into paragraphs
            paragraphs = content.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    story.append(Paragraph(para.strip(), custom_styles['CustomBodyText']))

            # Build PDF
            doc.build(story)

            logger.info(f"Simple PDF generated successfully: {pdf_path}")
            return str(pdf_path)

        except Exception as e:
            logger.error(f"Error generating simple PDF: {str(e)}", exc_info=True)
            return None


# Singleton instance
_pdf_service = None


def get_pdf_service() -> PDFService:
    """Get or create the singleton PDF service instance."""
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFService()
    return _pdf_service
