from fpdf import FPDF
import pandas as pd
import os
from datetime import datetime
import logging
import math

# Configure logging
logger = logging.getLogger(__name__)

class ShirtPatternGenerator:
    def __init__(self):
        """
        Initialize shirt pattern generator with industry-standard ease amounts
        Based on Seamly2D shirt pattern formulas and professional pattern-making standards
        """
        
        # Fit categories with different ease amounts (in cm)
        self.fit_types = {
            'slim': {
                'chest_ease': 3.0,      # Slim fit chest ease
                'armscye_height_back': 3.0,
                'armscye_height_front': 3.0,
                'front_width_ease': 0.75,
                'back_width_ease': 1.25,
                'armscye_width_ease': 3.5
            },
            'regular': {
                'chest_ease': 4.0,      # Regular fit chest ease  
                'armscye_height_back': 4.0,
                'armscye_height_front': 4.0,
                'front_width_ease': 1.0,
                'back_width_ease': 2.0,
                'armscye_width_ease': 4.5
            },
            'loose': {
                'chest_ease': 5.0,      # Loose fit chest ease
                'armscye_height_back': 5.0,
                'armscye_height_front': 5.0,
                'front_width_ease': 1.5,
                'back_width_ease': 3.0,
                'armscye_width_ease': 5.5
            }
        }
        
        # Seam allowances (in cm) - industry standard
        self.seam_allowance = {
            'standard': 1.5,        # Standard construction seams
            'shoulder': 1.0,        # Shoulder seams
            'armhole': 1.0,         # Armhole seams
            'neckline': 0.6,        # Neckline seams
            'hem': 2.5,             # Bottom hem
            'cuff': 1.0,            # Cuff attachment
            'button_band': 1.5      # Button placket
        }
        
        # Component dimensions (in cm)
        self.components = {
            'yoke_height': 8.0,             # Back yoke height
            'back_pleat': 3.0,              # Center back pleat
            'button_panel_width': 5.5,      # Button band width
            'collar_height_back': 3.8,      # Collar height at CB
            'collar_front_height': 7.0,     # Collar height at front
            'collar_base_height': 2.0,      # Collar stand height
            'cuff_width': 6.0,              # Cuff height
            'cuff_extension': 3.0,          # Cuff ease
            'placket_depth': 15.0,          # Sleeve placket depth
            'placket_width': 3.0,           # Sleeve placket width
            'pocket_width': 9.0,            # Chest pocket width
            'pocket_height': 13.0,          # Chest pocket height
            'armscye_drop': 1.0,            # Armhole lowering
            'shoulder_drop_back': 2.0,      # Back shoulder slope
            'shoulder_drop_front': 4.0,     # Front shoulder slope
            'shoulder_shift': 1.5           # Shoulder seam shift
        }

    def validate_measurements(self, measurements):
        """
        Validate shirt measurements against industry standards
        """
        validation_rules = {
            'chest': (80, 150, 'cm'),           # Chest circumference
            'waist': (60, 130, 'cm'),           # Waist circumference  
            'hip': (80, 150, 'cm'),             # Hip circumference
            'neck': (32, 50, 'cm'),             # Neck circumference
            'shoulder_length': (35, 55, 'cm'),   # Shoulder width
            'arm_length': (55, 80, 'cm'),       # Arm length (shoulder to wrist)
            'back_length': (65, 85, 'cm'),      # Back length (neck to waist)
            'shirt_length': (70, 95, 'cm'),     # Total shirt length
            'bicep': (25, 45, 'cm'),            # Bicep circumference
            'wrist': (14, 22, 'cm'),            # Wrist circumference
            'armhole_depth': (18, 28, 'cm')     # Armhole depth
        }
        
        errors = []
        for key, (min_val, max_val, unit) in validation_rules.items():
            if key in measurements:
                value = measurements[key]
                if not (min_val <= value <= max_val):
                    errors.append(f"{key}: {value}{unit} is outside valid range ({min_val}-{max_val}{unit})")
            else:
                errors.append(f"Missing measurement: {key}")
        
        return errors

    def calculate_bust_circumference(self, measurements, fit_type='regular'):
        """Calculate working bust circumference with ease"""
        ease = self.fit_types[fit_type]['chest_ease']
        return measurements['chest'] + ease

    def calculate_front_width(self, bust_circ, fit_type='regular'):
        """
        Calculate front width using Seamly2D formula
        """
        ease = self.fit_types[fit_type]['front_width_ease']
        
        if bust_circ < 112:
            # For smaller sizes: 2/10 bust - 1cm + ease
            front_width = (bust_circ / 5) - 1 + ease
        else:
            # For larger sizes: more complex calculation
            armscye_width = (bust_circ / 10) + 2
            back_width = (bust_circ / 10) + 10.5
            front_width = (bust_circ / 2) - (armscye_width + back_width) + ease
            
        return max(front_width, 8.0)  # Minimum practical width

    def calculate_back_width(self, bust_circ, fit_type='regular'):
        """
        Calculate back width using Seamly2D formula
        """
        ease = self.fit_types[fit_type]['back_width_ease']
        
        if bust_circ < 100:
            # For smaller sizes: 2/10 bust - 1cm + ease
            back_width = (bust_circ / 5) - 1 + ease
        else:
            # For larger sizes: 1/10 bust + 10.5cm + ease
            back_width = (bust_circ / 10) + 10.5 + ease
            
        return back_width

    def calculate_armscye_width(self, bust_circ, fit_type='regular'):
        """Calculate armhole width"""
        ease = self.fit_types[fit_type]['armscye_width_ease']
        return (bust_circ / 10) + 2 + ease

    def calculate_front_bodice(self, measurements, fit_type='regular'):
        """Calculate front bodice pattern piece"""
        bust_circ = self.calculate_bust_circumference(measurements, fit_type)
        front_width = self.calculate_front_width(bust_circ, fit_type)
        
        # Add seam allowances
        width = front_width + (self.seam_allowance['standard'] * 2)
        length = measurements['shirt_length'] + self.seam_allowance['hem']
        
        return {
            "Pattern Piece": "Front Bodice",
            "Dimensions": f"{round(width, 1)} x {round(length, 1)} cm",
            "Cutting Notes": "Cut 2 (1 left, 1 right)",
            "Grainline": "Vertical (parallel to center front)",
            "Notches": "Shoulder point, armhole, side seam, button band"
        }

    def calculate_back_bodice(self, measurements, fit_type='regular'):
        """Calculate back bodice pattern piece"""
        bust_circ = self.calculate_bust_circumference(measurements, fit_type)
        back_width = self.calculate_back_width(bust_circ, fit_type)
        
        # Back is typically wider than front for better fit
        width = back_width + (self.seam_allowance['standard'] * 2)
        length = measurements['shirt_length'] + self.seam_allowance['hem']
        
        return {
            "Pattern Piece": "Back Bodice",
            "Dimensions": f"{round(width, 1)} x {round(length, 1)} cm", 
            "Cutting Notes": "Cut 1 on fold or Cut 2",
            "Grainline": "Vertical (parallel to center back)",
            "Notches": "Shoulder point, armhole, side seam, center back"
        }

    def calculate_yoke(self, measurements, fit_type='regular'):
        """Calculate back yoke pattern piece"""
        bust_circ = self.calculate_bust_circumference(measurements, fit_type)
        back_width = self.calculate_back_width(bust_circ, fit_type)
        
        width = back_width + (self.seam_allowance['standard'] * 2)
        height = self.components['yoke_height'] + (self.seam_allowance['standard'] * 2)
        
        return {
            "Pattern Piece": "Back Yoke",
            "Dimensions": f"{round(width, 1)} x {round(height, 1)} cm",
            "Cutting Notes": "Cut 2 (1 outer, 1 lining)",
            "Grainline": "Horizontal",
            "Notches": "Shoulder points, center back, armhole"
        }

    def calculate_sleeve(self, measurements, fit_type='regular'):
        """Calculate sleeve pattern piece"""
        bust_circ = self.calculate_bust_circumference(measurements, fit_type)
        
        # Sleeve width accommodates bicep + ease
        bicep_ease = 6.0 if fit_type == 'slim' else 8.0 if fit_type == 'regular' else 10.0
        width = measurements['bicep'] + bicep_ease + (self.seam_allowance['standard'] * 2)
        
        # Sleeve length + cuff attachment
        length = measurements['arm_length'] + self.seam_allowance['cuff'] + 2.0
        
        return {
            "Pattern Piece": "Sleeve",
            "Dimensions": f"{round(width, 1)} x {round(length, 1)} cm",
            "Cutting Notes": "Cut 2",
            "Grainline": "Vertical (parallel to center line)",
            "Notches": "Front armhole, back armhole, elbow, wrist"
        }

    def calculate_cuff(self, measurements):
        """Calculate cuff pattern piece"""
        # Cuff circumference = wrist + ease + button overlap
        cuff_circumference = measurements['wrist'] + self.components['cuff_extension'] + 3.0
        
        width = cuff_circumference + (self.seam_allowance['standard'] * 2)
        height = self.components['cuff_width'] + (self.seam_allowance['standard'] * 2)
        
        return {
            "Pattern Piece": "Cuff",
            "Dimensions": f"{round(width, 1)} x {round(height, 1)} cm",
            "Cutting Notes": "Cut 4 (2 outer, 2 interfacing)",
            "Grainline": "Horizontal",
            "Notches": "Button placement, center fold"
        }

    def calculate_collar_band(self, measurements):
        """Calculate collar band (stand) pattern piece"""
        # Collar band length = neck circumference + ease + overlap
        band_length = measurements['neck'] + 2.0 + 1.5  # ease + button overlap
        band_height = self.components['collar_base_height'] + (self.seam_allowance['neckline'] * 2)
        
        return {
            "Pattern Piece": "Collar Band",
            "Dimensions": f"{round(band_length, 1)} x {round(band_height, 1)} cm",
            "Cutting Notes": "Cut 4 (2 outer, 2 interfacing)",
            "Grainline": "Horizontal",
            "Notches": "Center back, button placement, collar attachment"
        }

    def calculate_collar(self, measurements):
        """Calculate collar pattern piece"""
        # Collar length matches collar band
        collar_length = measurements['neck'] + 3.5  # includes spread
        collar_height = self.components['collar_front_height'] + self.seam_allowance['standard']
        
        return {
            "Pattern Piece": "Collar",
            "Dimensions": f"{round(collar_length, 1)} x {round(collar_height, 1)} cm",
            "Cutting Notes": "Cut 4 (2 outer, 2 interfacing)",
            "Grainline": "Horizontal",
            "Notches": "Center back, collar points, band attachment"
        }

    def calculate_button_band(self, measurements):
        """Calculate button placket pattern piece"""
        band_width = self.components['button_panel_width'] + (self.seam_allowance['button_band'] * 2)
        band_length = measurements['shirt_length'] * 0.7  # Typically 70% of shirt length
        
        return {
            "Pattern Piece": "Button Band",
            "Dimensions": f"{round(band_width, 1)} x {round(band_length, 1)} cm",
            "Cutting Notes": "Cut 2 (1 button, 1 buttonhole)",
            "Grainline": "Vertical",
            "Notches": "Button placement marks, hem attachment"
        }

    def calculate_sleeve_placket(self, measurements):
        """Calculate sleeve placket pattern piece"""
        placket_length = self.components['placket_depth'] + (self.seam_allowance['standard'] * 2)
        placket_width = self.components['placket_width'] + (self.seam_allowance['standard'] * 2)
        
        return {
            "Pattern Piece": "Sleeve Placket", 
            "Dimensions": f"{round(placket_width, 1)} x {round(placket_length, 1)} cm",
            "Cutting Notes": "Cut 4 (2 per sleeve)",
            "Grainline": "Vertical",
            "Notches": "Fold line, attachment points"
        }

    def calculate_pocket(self, measurements):
        """Calculate chest pocket pattern piece"""
        pocket_width = self.components['pocket_width'] + (self.seam_allowance['standard'] * 2)
        pocket_height = self.components['pocket_height'] + (self.seam_allowance['standard'] * 2)
        
        return {
            "Pattern Piece": "Chest Pocket",
            "Dimensions": f"{round(pocket_width, 1)} x {round(pocket_height, 1)} cm",
            "Cutting Notes": "Cut 2 (1 outer, 1 lining)",
            "Grainline": "Vertical",
            "Notches": "Fold line, attachment points"
        }

    def generate_pattern_data(self, measurements, fit_type='regular'):
        """Generate all shirt pattern pieces"""
        # Validate measurements first
        errors = self.validate_measurements(measurements)
        if errors:
            raise ValueError(f"Invalid measurements: {', '.join(errors)}")
        
        return [
            self.calculate_front_bodice(measurements, fit_type),
            self.calculate_back_bodice(measurements, fit_type),
            self.calculate_yoke(measurements, fit_type),
            self.calculate_sleeve(measurements, fit_type),
            self.calculate_cuff(measurements),
            self.calculate_collar_band(measurements),
            self.calculate_collar(measurements),
            self.calculate_button_band(measurements),
            self.calculate_sleeve_placket(measurements),
            self.calculate_pocket(measurements)
        ]

    def create_enhanced_pdf(self, pattern_data, measurements, user_name="Customer", garment_style="Men's Dress Shirt", fit_type="regular"):
        """Create enhanced PDF with shirt construction details"""
        
        class ShirtPatternPDF(FPDF):
            def header(self):
                self.set_font('Arial', 'B', 16)
                self.cell(0, 10, f'{garment_style} Pattern Specification', 0, 1, 'C')
                self.set_font('Arial', '', 10)
                self.cell(0, 5, f'Generated on: {datetime.now().strftime("%Y-%m-%d at %H:%M")}', 0, 1, 'C')
                self.cell(0, 5, f'Fit Type: {fit_type.title()}', 0, 1, 'C')
                self.ln(5)
            
            def footer(self):
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
                self.cell(0, 10, f'Page {self.page_no()} | Pattern for {user_name}', 0, 0, 'C')
        
        pdf = ShirtPatternPDF()
        pdf.add_page()
        
        # Customer and measurement info
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, f'Customer: {user_name}', 0, 1)
        pdf.cell(0, 8, f'Fit Type: {fit_type.title()} Fit', 0, 1)
        pdf.ln(3)
        
        # Measurements summary
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 8, 'Measurements Used:', 0, 1)
        pdf.set_font('Arial', '', 9)
        
        # Display measurements in organized layout
        measurement_labels = {
            'chest': 'Chest Circumference',
            'waist': 'Waist Circumference', 
            'hip': 'Hip Circumference',
            'neck': 'Neck Circumference',
            'shoulder_length': 'Shoulder Length',
            'arm_length': 'Arm Length',
            'back_length': 'Back Length',
            'shirt_length': 'Shirt Length',
            'bicep': 'Bicep Circumference',
            'wrist': 'Wrist Circumference',
            'armhole_depth': 'Armhole Depth'
        }
        
        col1_keys = list(measurement_labels.keys())[:6]
        col2_keys = list(measurement_labels.keys())[6:]
        
        for i, key in enumerate(col1_keys):
            if key in measurements:
                pdf.cell(90, 5, f'{measurement_labels[key]}: {measurements[key]} cm', 0, 0)
            if i < len(col2_keys) and col2_keys[i] in measurements:
                pdf.cell(90, 5, f'{measurement_labels[col2_keys[i]]}: {measurements[col2_keys[i]]} cm', 0, 1)
            else:
                pdf.ln()
        
        pdf.ln(8)
        
        # Pattern pieces table
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 8, 'Pattern Pieces:', 0, 1)
        
        # Table headers
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(35, 8, 'Pattern Piece', 1, 0, 'C')
        pdf.cell(30, 8, 'Dimensions', 1, 0, 'C')
        pdf.cell(35, 8, 'Cutting Notes', 1, 0, 'C')
        pdf.cell(35, 8, 'Grainline', 1, 0, 'C')
        pdf.cell(45, 8, 'Notches & Details', 1, 1, 'C')
        
        # Table rows
        pdf.set_font('Arial', '', 8)
        for item in pattern_data:
            pdf.cell(35, 8, item["Pattern Piece"], 1, 0)
            pdf.cell(30, 8, item["Dimensions"], 1, 0)
            pdf.cell(35, 8, item["Cutting Notes"], 1, 0)
            pdf.cell(35, 8, item["Grainline"], 1, 0)
            pdf.cell(45, 8, item["Notches"], 1, 1)
        
        # Construction notes
        pdf.ln(8)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 8, 'Construction Notes:', 0, 1)
        pdf.set_font('Arial', '', 9)
        
        notes = [
            "• All seam allowances are included in pattern dimensions",
            "• Interface collar, collar band, cuffs, and button bands", 
            "• Press seams toward back where possible",
            "• Attach yoke before setting sleeves",
            "• Install collar band before attaching collar",
            "• Complete plackets before attaching cuffs",
            "• Test fit at basting stage before final construction"
        ]
        
        for note in notes:
            pdf.cell(0, 5, note, 0, 1)
        
        return pdf

    def generate_shirt_pattern(self, measurements, user_name="Customer", garment_style="Men's Dress Shirt", fit_type="regular", output_dir="patterns"):
        """
        Main function to generate shirt pattern
        """
        try:
            logger.info(f"Generating {fit_type} fit shirt pattern for {user_name} with measurements: {measurements}")
            
            # Generate pattern data
            pattern_data = self.generate_pattern_data(measurements, fit_type)
            
            # Create DataFrame
            df = pd.DataFrame(pattern_data)
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate PDF
            pdf = self.create_enhanced_pdf(pattern_data, measurements, user_name, garment_style, fit_type)
            
            # Save PDF
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{garment_style.lower().replace(' ', '_')}_{fit_type}_pattern_{timestamp}.pdf"
            output_path = os.path.join(output_dir, filename)
            
            pdf.output(output_path)
            
            logger.info(f"Shirt pattern successfully generated: {output_path}")
            
            return {
                'success': True,
                'pattern_data': pattern_data,
                'dataframe': df,
                'pdf_path': output_path,
                'filename': filename,
                'message': f'{fit_type.title()} fit shirt pattern generated successfully for {user_name}'
            }
            
        except Exception as e:
            logger.error(f"Error generating shirt pattern: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to generate shirt pattern'
            }

# Example usage
if __name__ == "__main__":
    # Test measurements (in cm)
    test_measurements = {
        'chest': 102,                # Chest circumference
        'waist': 86,                 # Waist circumference
        'hip': 98,                   # Hip circumference  
        'neck': 39,                  # Neck circumference
        'shoulder_length': 45,       # Shoulder length
        'arm_length': 64,            # Arm length
        'back_length': 75,           # Back length (neck to waist)
        'shirt_length': 76,          # Total shirt length
        'bicep': 34,                 # Bicep circumference
        'wrist': 17,                 # Wrist circumference
        'armhole_depth': 22          # Armhole depth
    }
    
    # Generate pattern for different fits
    generator = ShirtPatternGenerator()
    
    for fit_type in ['slim', 'regular', 'loose']:
        result = generator.generate_shirt_pattern(
            test_measurements, 
            "Test User", 
            "Men's Dress Shirt",
            fit_type
        )
        
        if result['success']:
            print(f"✅ {fit_type.title()} fit pattern generated: {result['filename']}")
            print(result['dataframe'])
            print("-" * 50)
        else:
            print(f"❌ Error generating {fit_type} fit: {result['message']}")
