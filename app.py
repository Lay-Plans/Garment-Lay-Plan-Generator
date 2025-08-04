from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import Schema, fields, ValidationError
import os
import tempfile
import uuid
import logging
from datetime import datetime
from dotenv import load_dotenv
from shirt_pattern_generator import ShirtPatternGenerator  # Updated import

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    PATTERNS_FOLDER = os.environ.get('PATTERNS_FOLDER', 'patterns')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')

app.config.from_object(Config)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri=app.config['RATELIMIT_STORAGE_URL'],
    default_limits=["200 per day", "50 per hour"]
)

# Ensure patterns directory exists
os.makedirs(app.config['PATTERNS_FOLDER'], exist_ok=True)

# Input validation schema for shirt measurements
class ShirtMeasurementSchema(Schema):
    """Validation schema for shirt measurements"""
    chest = fields.Float(required=True, validate=lambda x: 80 <= x <= 150,
                        error_messages={"validator_failed": "Chest must be between 80-150 cm"})
    waist = fields.Float(required=True, validate=lambda x: 60 <= x <= 130,
                        error_messages={"validator_failed": "Waist must be between 60-130 cm"})
    hip = fields.Float(required=True, validate=lambda x: 80 <= x <= 150,
                      error_messages={"validator_failed": "Hip must be between 80-150 cm"})
    neck = fields.Float(required=True, validate=lambda x: 32 <= x <= 50,
                       error_messages={"validator_failed": "Neck must be between 32-50 cm"})
    shoulder_length = fields.Float(required=True, validate=lambda x: 35 <= x <= 55,
                                  error_messages={"validator_failed": "Shoulder length must be between 35-55 cm"})
    arm_length = fields.Float(required=True, validate=lambda x: 55 <= x <= 80,
                             error_messages={"validator_failed": "Arm length must be between 55-80 cm"})
    back_length = fields.Float(required=True, validate=lambda x: 65 <= x <= 85,
                              error_messages={"validator_failed": "Back length must be between 65-85 cm"})
    shirt_length = fields.Float(required=True, validate=lambda x: 70 <= x <= 95,
                               error_messages={"validator_failed": "Shirt length must be between 70-95 cm"})
    bicep = fields.Float(required=True, validate=lambda x: 25 <= x <= 45,
                        error_messages={"validator_failed": "Bicep must be between 25-45 cm"})
    wrist = fields.Float(required=True, validate=lambda x: 14 <= x <= 22,
                        error_messages={"validator_failed": "Wrist must be between 14-22 cm"})
    armhole_depth = fields.Float(required=True, validate=lambda x: 18 <= x <= 28,
                                error_messages={"validator_failed": "Armhole depth must be between 18-28 cm"})

class PatternRequestSchema(Schema):
    """Schema for pattern generation requests"""
    measurements = fields.Nested(ShirtMeasurementSchema, required=True)
    user_name = fields.Str(missing="Customer", validate=lambda x: len(x) <= 100)
    garment_style = fields.Str(missing="Men's Dress Shirt", validate=lambda x: len(x) <= 50)
    fit_type = fields.Str(missing="regular", validate=lambda x: x in ['slim', 'regular', 'loose'])

# Error handlers
@app.errorhandler(ValidationError)
def handle_validation_error(e):
    logger.warning(f"Validation error: {e.messages}")
    return jsonify({
        "status": "error",
        "message": "Invalid input data",
        "errors": e.messages
    }), 400

@app.errorhandler(429)
def handle_rate_limit_exceeded(e):
    logger.warning(f"Rate limit exceeded: {request.remote_addr}")
    return jsonify({
        "status": "error",
        "message": "Rate limit exceeded. Please try again later."
    }), 429

@app.errorhandler(413)
def handle_file_too_large(e):
    return jsonify({
        "status": "error",
        "message": "File too large. Maximum size is 16MB."
    }), 413

@app.errorhandler(500)
def handle_internal_error(e):
    logger.error(f"Internal error: {str(e)}")
    return jsonify({
        "status": "error",
        "message": "Internal server error. Please try again later."
    }), 500

# Routes
@app.route('/')
def home():
    """Health check and basic info endpoint"""
    return jsonify({
        "status": "success",
        "message": "Shirt Pattern Generator Backend is Running",
        "version": "1.0.0",
        "supported_fits": ["slim", "regular", "loose"],
        "endpoints": {
            "generate": "/generate",
            "download": "/download/<filename>",
            "health": "/health",
            "patterns": "/patterns"
        }
    })

@app.route('/health')
def health_check():
    """Detailed health check"""
    try:
        # Check if patterns directory is writable
        test_file = os.path.join(app.config['PATTERNS_FOLDER'], 'test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)

        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "patterns_folder": app.config['PATTERNS_FOLDER'],
            "patterns_folder_writable": True,
            "supported_garments": ["Men's Dress Shirt", "Casual Shirt"],
            "supported_fits": ["slim", "regular", "loose"]
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route('/generate', methods=['POST'])
@limiter.limit("10 per minute")
def generate_pattern():
    """Generate a shirt pattern"""
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                "status": "error",
                "message": "Request must be JSON"
            }), 400

        # Parse and validate input
        schema = PatternRequestSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as e:
            return jsonify({
                "status": "error",
                "message": "Invalid input data",
                "errors": e.messages
            }), 400

        measurements = data['measurements']
        user_name = data['user_name']
        garment_style = data['garment_style']
        fit_type = data['fit_type']

        logger.info(f"Generating {fit_type} fit {garment_style} pattern for {user_name}")
        logger.debug(f"Measurements: {measurements}")

        # Generate pattern
        generator = ShirtPatternGenerator()
        result = generator.generate_shirt_pattern(
            measurements=measurements,
            user_name=user_name,
            garment_style=garment_style,
            fit_type=fit_type,
            output_dir=app.config['PATTERNS_FOLDER']
        )

        if result['success']:
            response_data = {
                "status": "success",
                "message": result['message'],
                "pattern_data": result['pattern_data'],
                "download_url": f"/download/{result['filename']}",
                "fit_type": fit_type,
                "generated_at": datetime.now().isoformat(),
                "pattern_pieces_count": len(result['pattern_data'])
            }
            
            logger.info(f"Shirt pattern generated successfully: {result['filename']}")
            return jsonify(response_data)
        else:
            logger.error(f"Pattern generation failed: {result['error']}")
            return jsonify({
                "status": "error",
                "message": result['message'],
                "error": result['error']
            }), 500

    except Exception as e:
        logger.error(f"Unexpected error in generate_pattern: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500

@app.route('/download/<filename>')
@limiter.limit("20 per minute")
def download_pattern(filename):
    """Download generated pattern PDF"""
    try:
        # Validate filename (security check)
        if not filename.endswith('.pdf') or '..' in filename or '/' in filename:
            return jsonify({
                "status": "error",
                "message": "Invalid filename"
            }), 400

        file_path = os.path.join(app.config['PATTERNS_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({
                "status": "error",
                "message": "File not found"
            }), 404

        logger.info(f"Serving file: {filename}")
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )

    except Exception as e:
        logger.error(f"Error serving file {filename}: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error downloading file"
        }), 500

@app.route('/patterns', methods=['GET'])
@limiter.limit("30 per minute")
def list_patterns():
    """List available patterns (for development/admin use)"""
    try:
        patterns = []
        pattern_dir = app.config['PATTERNS_FOLDER']

        if os.path.exists(pattern_dir):
            for filename in os.listdir(pattern_dir):
                if filename.endswith('.pdf'):
                    file_path = os.path.join(pattern_dir, filename)
                    stat = os.stat(file_path)
                    
                    # Extract pattern info from filename if possible
                    pattern_info = {
                        'filename': filename,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'download_url': f'/download/{filename}'
                    }
                    
                    # Try to extract fit type and garment style from filename
                    if 'slim' in filename:
                        pattern_info['fit_type'] = 'slim'
                    elif 'loose' in filename:
                        pattern_info['fit_type'] = 'loose'
                    else:
                        pattern_info['fit_type'] = 'regular'
                    
                    if 'dress_shirt' in filename:
                        pattern_info['garment_style'] = "Men's Dress Shirt"
                    elif 'casual' in filename:
                        pattern_info['garment_style'] = "Casual Shirt"
                    else:
                        pattern_info['garment_style'] = "Shirt"
                    
                    patterns.append(pattern_info)
        
        # Sort by creation date (newest first)
        patterns.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({
            "status": "success",
            "patterns": patterns,
            "total": len(patterns),
            "supported_fits": ["slim", "regular", "loose"]
        })

    except Exception as e:
        logger.error(f"Error listing patterns: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Error listing patterns"
        }), 500

@app.route('/fit-guide')
def fit_guide():
    """Provide fitting guide information"""
    fit_guide_info = {
        "fit_types": {
            "slim": {
                "description": "Close-fitting with minimal ease. Best for lean builds.",
                "chest_ease": "3-4 cm total ease",
                "characteristics": ["Fitted through torso", "Tapered sleeves", "Modern silhouette"]
            },
            "regular": {
                "description": "Classic fit with comfortable ease. Suitable for most body types.",
                "chest_ease": "4-5 cm total ease", 
                "characteristics": ["Comfortable fit", "Standard proportions", "Traditional silhouette"]
            },
            "loose": {
                "description": "Relaxed fit with generous ease. Comfortable for layering.",
                "chest_ease": "5-6 cm total ease",
                "characteristics": ["Roomy fit", "Relaxed silhouette", "Great for layering"]
            }
        },
        "measurement_tips": {
            "chest": "Measure around fullest part of chest, arms at sides",
            "neck": "Measure around base of neck where collar would sit",
            "shoulder_length": "From neck point to end of shoulder",
            "arm_length": "From shoulder point to wrist bone",
            "shirt_length": "From high point shoulder to desired hem length"
        }
    }
    
    return jsonify({
        "status": "success",
        "fit_guide": fit_guide_info
    })

# Development route to serve the frontend (optional)
@app.route('/app')  
def serve_app():
    """Serve the frontend application (development only)"""
    return render_template('index.html')

if __name__ == '__main__':
    # Development server
    app.run(
        debug=app.config['DEBUG'],
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000))
    )