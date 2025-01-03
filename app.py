import re
from flask import Flask, render_template, request, jsonify
import g4f
import os
import logging
from functools import wraps
import plantuml
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'static/diagrams'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize PlantUML with the correct image URL
plantuml_instance = plantuml.PlantUML(url='http://www.plantuml.com/plantuml/img/')

def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except plantuml.PlantUMLHTTPError as e:
            logger.error(f"PlantUML HTTP Error: {str(e)}")
            return jsonify({'error': 'Failed to generate diagram: Server error'}), 500
        except plantuml.PlantUMLConnectionError as e:
            logger.error(f"PlantUML Connection Error: {str(e)}")
            return jsonify({'error': 'Failed to connect to PlantUML server'}), 500
        except plantuml.PlantUMLError as e:
            logger.error(f"PlantUML Error: {str(e)}")
            return jsonify({'error': 'Failed to process PlantUML syntax'}), 500
        except Exception as e:
            logger.error(f"Error occurred: {str(e)}")
            return jsonify({'error': str(e)}), 500
    return decorated_function

def generate_ai_prompt(project_name, diagram_type):
    """Generate a prompt for the AI based on project name and diagram type."""
    return f"""Create a PlantUML syntax for a {diagram_type} diagram for a project named {project_name}. 
    The diagram should be detailed and follow UML standards. 
    Provide only the PlantUML syntax without any additional text or explanations.
    Start with @startuml and end with @enduml."""

def extract_plantuml_syntax(text):
    """Extract and clean PlantUML syntax between @startuml and @enduml tags."""
    # Find the content between @startuml and @enduml
    pattern = r'@startuml\s*(.*?)\s*@enduml'
    match = re.search(pattern, text, re.DOTALL)
    
    if not match:
        raise Exception("No valid PlantUML syntax found in AI response")
    
    # Get the content and clean it
    content = match.group(1)
    
    # Clean the content:
    # 1. Split into lines
    lines = content.split('\n')
    # 2. Remove empty lines at start and end
    lines = [line.rstrip() for line in lines]
    # 3. Remove leading/trailing empty lines while preserving internal empty lines
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    
    # Reconstruct the cleaned PlantUML syntax
    cleaned_content = '\n'.join(lines)
    
    # Return the complete syntax with @startuml and @enduml
    return cleaned_content
def get_ai_response(prompt):
    """Get response from g4f AI API."""
    try:
        response = g4f.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return extract_plantuml_syntax(response)
    except Exception as e:
        logger.error(f"AI API Error: {str(e)}")
        raise Exception("Failed to generate diagram syntax from AI")

def generate_diagram(plantuml_syntax):
    """Generate diagram image from PlantUML syntax."""
    try:
        # Get the raw PNG image data
        png_data = plantuml_instance.processes(plantuml_syntax)
        
        # Convert to base64 for displaying in browser
        return base64.b64encode(png_data).decode()
    except Exception as e:
        logger.error(f"PlantUML Processing Error: {str(e)}")
        raise

@app.route('/try')
def try_app():
    """Render the main page."""
    diagram_types = [
        "Sequence Diagram",
        "Use Case Diagram",
        "Class Diagram",
        "Object Diagram",
        "Activity Diagram",
        "Component Diagram",
        "Deployment Diagram",
        "State Diagram",
        "Timing Diagram"
    ]
    return render_template('generate.html', diagram_types=diagram_types)


@app.route('/')
def index():
    """Render the main page."""

    return render_template('index.html')

@app.route('/generate', methods=['POST'])
@handle_errors
def generate():
    """Handle diagram generation request."""
    project_name = request.form.get('project_name')
    diagram_type = request.form.get('diagram_type')

    if not project_name or not diagram_type:
        return jsonify({'error': 'Missing required fields'}), 400

    # Generate AI prompt and get response
    prompt = generate_ai_prompt(project_name, diagram_type)
    print("prompt", prompt)
    plantuml_syntax =  get_ai_response(prompt)
    print("plantuml_syntax", plantuml_syntax)

    # Generate diagram
    diagram_base64 = generate_diagram(plantuml_syntax)

    return jsonify({
        'diagram': diagram_base64,
        'syntax': plantuml_syntax
    })

if __name__ == '__main__':
    app.run(debug=True)