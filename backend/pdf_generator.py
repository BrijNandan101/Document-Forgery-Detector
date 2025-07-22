from fpdf import FPDF
import os
import logging
from datetime import datetime
from pathlib import Path

class PDFReportGenerator:
    def __init__(self, output_dir="reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, analysis_data):
        """
        analysis_data = {
            'id': str,
            'verdict': 'Genuine' or 'Forged',
            'confidence': float,
            'ela_processed': bool,
            'filename': str,
            'timestamp': datetime,
        }
        """
        try:
            pdf = FPDF()
            pdf.add_page()

            # Title
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "Document Forgery Detection Report", ln=True, align='C')
            pdf.ln(10)

            # Analysis Summary
            pdf.set_font("Arial", '', 12)
            pdf.cell(40, 10, "Analysis ID:", ln=False)
            pdf.cell(0, 10, str(analysis_data.get('id')), ln=True)

            pdf.cell(40, 10, "Filename:", ln=False)
            pdf.cell(0, 10, analysis_data.get('filename', 'N/A'), ln=True)

            pdf.cell(40, 10, "Date:", ln=False)
            pdf.cell(0, 10, analysis_data.get('timestamp', str(datetime.now())), ln=True)

            pdf.cell(40, 10, "Verdict:", ln=False)
            pdf.cell(0, 10, analysis_data.get('verdict'), ln=True)

            pdf.cell(40, 10, "Confidence:", ln=False)
            pdf.cell(0, 10, f"{analysis_data.get('confidence')}%", ln=True)

            pdf.cell(40, 10, "ELA Processed:", ln=False)
            pdf.cell(0, 10, "Yes" if analysis_data.get('ela_processed') else "No", ln=True)

            pdf.cell(40, 10, "Method:", ln=False)
            pdf.cell(0, 10, analysis_data.get('analysis_method', 'N/A'), ln=True)

            # Save PDF
            output_path = self.output_dir / f"forgery_report_{analysis_data['id']}.pdf"
            pdf.output(str(output_path))
            logging.info(f"📄 PDF report generated: {output_path}")
            return output_path

        except Exception as e:
            logging.error(f"❌ Failed to generate PDF report: {e}")
            raise e
