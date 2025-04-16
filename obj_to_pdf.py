#!/usr/bin/env python3
"""
OBJ to PDF Converter
This script converts OBJ files to PDF format through U3D intermediate format

Workflow:
1. OBJ -> U3D: Using example_workflow.py
2. U3D -> PDF: Using latex_3d_pdf.py

Requirements:
- pymeshlab: pip install pymeshlab
- pdflatex: For PDF generation
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ObjToPdfConverter:
    def __init__(self, progress_callback=None):
        """Initialize the converter"""
        # Create output directory
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Get the script directory
        self.script_dir = Path(__file__).parent
        
        # Store progress callback
        self.progress_callback = progress_callback
    
    def convert(self, obj_file: str, output_pdf: str = None) -> str:
        """Convert OBJ file to PDF with embedded 3D model."""
        try:
            # Get base filename without extension
            base_name = os.path.splitext(os.path.basename(obj_file))[0]
            
            # Set default output PDF name if not provided
            if not output_pdf:
                output_pdf = f"output/pdf/{base_name}.pdf"

            # Ensure output directories exist
            os.makedirs("output/pdf", exist_ok=True)
            
            # Import example_workflow
            sys.path.append(str(self.script_dir / "obj_to_u3d"))
            import example_workflow
            
            # Step 1: Convert OBJ to U3D
            logger.info(f"\n==== Converting {obj_file} to U3D ====")
            u3d_output = f"output/{base_name}.u3d"
            
            if self.progress_callback:
                self.progress_callback('load', 0, 'Lade 3D-Modell...')
            
            # Convert to U3D using example_workflow
            if not example_workflow.obj_to_u3d(obj_file, u3d_output, simplify=5000):
                logger.error("U3D conversion failed")
                if self.progress_callback:
                    self.progress_callback('error', -1, 'U3D-Konvertierung fehlgeschlagen')
                return None
            
            if self.progress_callback:
                self.progress_callback('u3d', 50, 'U3D-Konvertierung erfolgreich. Erstelle PDF...')
            
            # Step 2: Create PDF with embedded U3D using latex_3d_pdf.py
            logger.info(f"\nCreating PDF with embedded 3D model: {output_pdf}")
            
            cmd = [
                "python",
                str(self.script_dir / "u3d_pdf" / "latex_3d_pdf.py"),
                u3d_output,
                output_pdf,
                "--title", f"{base_name} 3D Model"
            ]
            
            logger.info(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"PDF creation failed with error code {result.returncode}")
                logger.error(f"Error output: {result.stderr}")
                logger.error(f"Command output: {result.stdout}")
                if self.progress_callback:
                    self.progress_callback('error', -1, 'PDF-Erstellung fehlgeschlagen')
                return None
            
            if self.progress_callback:
                self.progress_callback('pdf', 100, 'PDF erfolgreich erstellt')
            
            logger.info(f"\nConversion complete! PDF saved to: {output_pdf}")
            return output_pdf
            
        except Exception as e:
            logger.error(f"Error converting OBJ to PDF: {str(e)}")
            if self.progress_callback:
                self.progress_callback('error', -1, f'Fehler bei der Konvertierung: {str(e)}')
            return None

def main():
    parser = argparse.ArgumentParser(description="Convert OBJ files to PDF")
    parser.add_argument("obj_file", help="Path to the OBJ file to convert")
    parser.add_argument("-o", "--output", help="Path to the output PDF file")
    
    args = parser.parse_args()
    
    converter = ObjToPdfConverter()
    pdf_file = converter.convert(args.obj_file, args.output)
    
    if pdf_file:
        logger.info(f"Successfully converted {args.obj_file} to {pdf_file}")
    else:
        logger.error("Conversion failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 