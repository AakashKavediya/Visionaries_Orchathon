import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from converter import convert_rvt_to_ifc
from mep_extractor import extract_mep_data
from clash_detector import detect_clashes

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
CONVERTED_IFC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'converted_ifc')
ALLOWED_EXTENSIONS = {'rvt'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_IFC_FOLDER'] = CONVERTED_IFC_FOLDER
# No upload size limit

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_IFC_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/convert', methods=['POST'])
def convert_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        input_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_filepath)

        try:
            # Convert and persist to /converted_ifc
            output_filename = convert_rvt_to_ifc(input_filepath, app.config['CONVERTED_IFC_FOLDER'])
            download_url = f"/download/{output_filename}"
            return jsonify({
                'status': 'success',
                'download_url': download_url,
                'filename': output_filename
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Invalid file type. Only .rvt files are allowed.'}), 400

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['CONVERTED_IFC_FOLDER'], filename, as_attachment=True)

@app.route('/api/mep-data/<path:filename>')
def get_mep_data(filename):
    """
    Loads the corresponding IFC file from /converted_ifc,
    parses it with IfcOpenShell, and returns MEP elements as JSON.
    """
    # Sanitise the filename
    safe_filename = secure_filename(filename)
    ifc_filepath = os.path.join(app.config['CONVERTED_IFC_FOLDER'], safe_filename)

    if not os.path.isfile(ifc_filepath):
        return jsonify({'error': f'IFC file not found: {safe_filename}'}), 404

    try:
        mep_elements = extract_mep_data(ifc_filepath)
        return jsonify({
            'status': 'success',
            'filename': safe_filename,
            'count': len(mep_elements),
            'elements': mep_elements
        })
    except ValueError as ve:
        # Parsing / invalid IFC errors
        return jsonify({'error': str(ve)}), 422
    except Exception as e:
        return jsonify({'error': f'Unexpected error during MEP extraction: {str(e)}'}), 500

@app.route('/api/clash-data/<path:filename>')
def get_clash_data(filename):
    """
    Parses IFC, extracts MEP elements, runs AABB clash detection,
    and returns clash reports with resolution strategies.
    """
    safe_filename = secure_filename(filename)
    ifc_filepath = os.path.join(app.config['CONVERTED_IFC_FOLDER'], safe_filename)

    if not os.path.isfile(ifc_filepath):
        return jsonify({'error': f'IFC file not found: {safe_filename}'}), 404

    try:
        mep_elements = extract_mep_data(ifc_filepath)
        clashes = detect_clashes(mep_elements)
        return jsonify({
            'status': 'success',
            'filename': safe_filename,
            'clash_count': len(clashes),
            'mep_element_count': len(mep_elements),
            'clashes': clashes
        })
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 422
    except Exception as e:
        return jsonify({'error': f'Clash detection error: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
