#!/usr/bin/env python3
"""
OBJ to PDF Converter
This script converts OBJ files to PDF format through U3D intermediate format

Workflow:
1. OBJ -> U3D: Using pymeshlab_u3d_example.py
2. U3D -> PDF: Using latex_3d_pdf.py

Requirements:
- pymeshlab: pip install pymeshlab
- pdflatex: For PDF generation
"""

import os
import sys
import subprocess
from pathlib import Path
import argparse

class ObjToPdfConverter:
    def __init__(self):
        """Initialize the converter"""
        # Create output directory
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Get the script directory
        self.script_dir = Path(__file__).parent
    
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
            
            # Step 1: Convert OBJ to U3D using pymeshlab_u3d_example.py
            print(f"\n==== Converting {obj_file} to U3D ====")
            u3d_output = f"output/{base_name}.u3d"
            
            cmd = [
                "python", str(self.script_dir / "obj_to_u3d" / "pymeshlab_u3d_example.py"),
                str(obj_file),
                u3d_output,
                "--clean",
                "--simplify", "5000"
            ]
            
            print(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Conversion failed with error code {result.returncode}")
                print(f"Error output: {result.stderr}")
                print(f"Command output: {result.stdout}")
                return None
            
            # Step 2: Create PDF with embedded U3D using latex_3d_pdf.py
            print(f"\nCreating PDF with embedded 3D model: {output_pdf}")
            cmd = [
                "python", str(self.script_dir / "u3d_pdf" / "latex_3d_pdf.py"),
                u3d_output,
                output_pdf,
                "--title", f"{base_name} 3D Model"
            ]
            
            print(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"PDF creation failed with error code {result.returncode}")
                print(f"Error output: {result.stderr}")
                print(f"Command output: {result.stdout}")
                return None
            
            print(f"\nConversion complete! PDF saved to: {output_pdf}")
            return output_pdf
            
        except Exception as e:
            print(f"Error converting OBJ to PDF: {str(e)}")
            return None

def main():
    parser = argparse.ArgumentParser(description="Convert OBJ files to PDF")
    parser.add_argument("obj_file", help="Path to the OBJ file to convert")
    parser.add_argument("-o", "--output", help="Path to the output PDF file")
    
    args = parser.parse_args()
    
    converter = ObjToPdfConverter()
    pdf_file = converter.convert(args.obj_file, args.output)
    
    if pdf_file:
        print(f"Successfully converted {args.obj_file} to {pdf_file}")
    else:
        print("Conversion faisled")
        sys.exit(1)

if __name__ == "__main__":
    main() 