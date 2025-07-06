"""
PDF Report Generator for Document Forgery Detection System
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os
from pathlib import Path
import logging

class PDFReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.reports_dir = Path(__file__).parent / "static" / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            alignment=TA_LEFT
        )
    
    def generate_report(self, analysis_data):
        """
        Generate PDF report for document analysis
        
        Args:
            analysis_data: Dictionary containing analysis results
            
        Returns:
            Path to generated PDF report
        """
        try:
            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"forgery_report_{analysis_data['id']}_{timestamp}.pdf"
            file_path = self.reports_dir / filename
            
            # Create PDF document
            doc = SimpleDocTemplate(
                str(file_path),
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build content
            story = []
            
            # Title
            title = Paragraph("Document Forgery Detection Report", self.title_style)
            story.append(title)
            story.append(Spacer(1, 20))
            
            # Report Information
            report_info = [
                ["Report ID:", analysis_data['id']],
                ["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                ["Analysis Date:", analysis_data['timestamp']],
                ["Document Name:", analysis_data['filename']]
            ]
            
            info_table = Table(report_info, colWidths=[2*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 30))
            
            # Analysis Results
            story.append(Paragraph("Analysis Results", self.heading_style))
            
            # Verdict with colored background
            verdict_color = colors.red if analysis_data['verdict'] == 'Forged' else colors.green
            verdict_bg = colors.lightpink if analysis_data['verdict'] == 'Forged' else colors.lightgreen
            
            results_data = [
                ["Verdict:", analysis_data['verdict']],
                ["Confidence Score:", f"{analysis_data['confidence']:.2f}%"],
                ["ELA Processed:", "Yes" if analysis_data.get('ela_processed', False) else "No"],
                ["Analysis Method:", analysis_data.get('analysis_method', 'AI Analysis')]
            ]
            
            results_table = Table(results_data, colWidths=[2*inch, 4*inch])
            results_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (1, 0), (1, 0), verdict_bg),
                ('TEXTCOLOR', (1, 0), (1, 0), verdict_color),
                ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(results_table)
            story.append(Spacer(1, 30))
            
            # Technical Details
            story.append(Paragraph("Technical Analysis Details", self.heading_style))
            
            technical_details = [
                "• Error Level Analysis (ELA) was performed to detect image manipulation",
                "• Deep learning CNN model analyzed the ELA-processed image",
                "• Confidence score indicates the certainty of the prediction",
                "• Higher confidence scores indicate more reliable predictions"
            ]
            
            for detail in technical_details:
                story.append(Paragraph(detail, self.body_style))
            
            story.append(Spacer(1, 20))
            
            # Interpretation Guide
            story.append(Paragraph("Interpretation Guide", self.heading_style))
            
            interpretation_text = """
            <b>Genuine Documents:</b> Show consistent compression artifacts and uniform 
            error levels across the image. The AI model detects patterns typical of 
            authentic documents.
            <br/><br/>
            <b>Forged Documents:</b> Display inconsistent error levels, indicating potential 
            manipulation. Common signs include altered text, replaced photos, or modified 
            signatures that create detectable artifacts.
            <br/><br/>
            <b>Confidence Levels:</b>
            <br/>• 90-100%: Very High Confidence
            <br/>• 70-89%: High Confidence  
            <br/>• 50-69%: Moderate Confidence
            <br/>• Below 50%: Low Confidence (manual review recommended)
            """
            
            story.append(Paragraph(interpretation_text, self.body_style))
            story.append(Spacer(1, 30))
            
            # Disclaimer
            story.append(Paragraph("Disclaimer", self.heading_style))
            disclaimer_text = """
            This report is generated by an AI-powered document forgery detection system. 
            While the system uses advanced techniques including Error Level Analysis and 
            deep learning models, it should be used as a tool to assist in document 
            verification rather than as a definitive determination. For critical 
            applications, additional expert analysis is recommended.
            """
            
            story.append(Paragraph(disclaimer_text, self.body_style))
            
            # Footer
            story.append(Spacer(1, 20))
            footer_text = f"Generated by Document Forgery Detection System v1.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            footer_style = ParagraphStyle(
                'Footer',
                parent=self.styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                textColor=colors.grey
            )
            story.append(Paragraph(footer_text, footer_style))
            
            # Build PDF
            doc.build(story)
            
            logging.info(f"PDF report generated: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logging.error(f"Error generating PDF report: {e}")
            raise e
    
    def generate_batch_report(self, analyses_data):
        """
        Generate batch report for multiple analyses
        
        Args:
            analyses_data: List of analysis dictionaries
            
        Returns:
            Path to generated batch PDF report
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"batch_forgery_report_{timestamp}.pdf"
            file_path = self.reports_dir / filename
            
            doc = SimpleDocTemplate(
                str(file_path),
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            story = []
            
            # Title
            title = Paragraph("Batch Document Forgery Detection Report", self.title_style)
            story.append(title)
            story.append(Spacer(1, 20))
            
            # Summary
            total_docs = len(analyses_data)
            forged_docs = sum(1 for analysis in analyses_data if analysis['verdict'] == 'Forged')
            genuine_docs = total_docs - forged_docs
            
            summary_data = [
                ["Total Documents:", str(total_docs)],
                ["Genuine Documents:", str(genuine_docs)],
                ["Forged Documents:", str(forged_docs)],
                ["Forgery Rate:", f"{(forged_docs/total_docs)*100:.1f}%" if total_docs > 0 else "0%"]
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 30))
            
            # Individual Results
            story.append(Paragraph("Individual Analysis Results", self.heading_style))
            
            # Create table with results
            table_data = [["Document", "Verdict", "Confidence", "Analysis Date"]]
            
            for analysis in analyses_data:
                table_data.append([
                    analysis['filename'],
                    analysis['verdict'],
                    f"{analysis['confidence']:.1f}%",
                    str(analysis['timestamp'])[:19]
                ])
            
            results_table = Table(table_data, colWidths=[2*inch, 1*inch, 1*inch, 1.5*inch])
            results_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(results_table)
            
            # Build PDF
            doc.build(story)
            
            logging.info(f"Batch PDF report generated: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logging.error(f"Error generating batch PDF report: {e}")
            raise e