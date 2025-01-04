
add this fatrher 
option can change theme after get response 
option can edit response data code and get diagram after editor 
option can get more diagram can selected or all diagrams in same time
option can export diagram or diagrams as pdf 

add same option style change in same diagrams like hide circle in class left to right direction in usecase 

when get answer only write code without any explain 
pleas full code for file u can split the answer to 2 response 1 for python and second for html



import re
import requests
from flask import Flask, render_template, request, jsonify
import g4f
import os
import logging
from functools import wraps
import plantuml
import base64
import json

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
def get_plantuml_themes():
    """Return the fixed list of available PlantUML themes."""
    return [
        "amiga",
        "aws-orange",
        "black-knight",
        "bluegray",
        "blueprint",
        "carbon-gray",
        "cerulean-outline",
        "cerulean",
        "cloudscape-design",
        "crt-amber",
        "crt-green",
        "cyborg-outline",
        "cyborg",
        "hacker",
        "lightgray",
        "mars",
        "materia-outline",
        "materia",
        "metal",
        "mimeograph",
        "minty",
        "mono",
        "none",
        "plain",
        "reddress-darkblue",
        "reddress-darkgreen",
        "reddress-darkorange",
        "reddress-darkred",
        "reddress-lightblue",
        "reddress-lightgreen",
        "reddress-lightorange",
        "reddress-lightred",
        "sandstone",
        "silver",
        "sketchy-outline",
        "sketchy",
        "spacelab-white",
        "spacelab",
        "sunlust",
        "superhero-outline",
        "superhero",
        "toy",
        "united",
        "vibrant"
    ]

@app.route('/themes')
def get_themes():
    """Endpoint to fetch available PlantUML themes."""
    themes = get_plantuml_themes()
    return jsonify({'themes': themes})


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

def generate_ai_prompt(project_name, diagram_type, theme=None):
    """Generate a prompt for the AI based on project name, diagram type, and theme."""
    theme_directive = f"!theme {theme}\n" if theme else ""
    return f"""Create a PlantUML syntax for a {diagram_type} diagram for a project named {project_name}. 
    The diagram should be detailed and follow UML standards. 
    Provide only the PlantUML syntax without any additional text or explanations.
    Start with @startuml
    {theme_directive}"""

def extract_plantuml_syntax(text):
    """Extract and clean PlantUML syntax between @startuml and @enduml tags."""
    pattern = r'@startuml\s*(.*?)\s*@enduml'
    match = re.search(pattern, text, re.DOTALL)
    
    if not match:
        raise Exception("No valid PlantUML syntax found in AI response")
    
    content = match.group(1)
    lines = content.split('\n')
    lines = [line.rstrip() for line in lines]
    
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    
    cleaned_content = '\n'.join(lines)
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
        png_data = plantuml_instance.processes(plantuml_syntax)
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
    themes = get_plantuml_themes()
    return render_template('generate.html', diagram_types=diagram_types, themes=themes)

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
    theme = request.form.get('theme')

    if not project_name or not diagram_type:
        return jsonify({'error': 'Missing required fields'}), 400

    prompt = generate_ai_prompt(project_name, diagram_type, theme)
    plantuml_syntax = get_ai_response(prompt)
    
    # If theme is selected, add theme directive at the beginning
    if theme:
        plantuml_syntax = f"!theme {theme}\n{plantuml_syntax}"

    diagram_base64 = generate_diagram(plantuml_syntax)

    return jsonify({
        'diagram': diagram_base64,
        'syntax': plantuml_syntax
    })

if __name__ == '__main__':
    app.run(debug=True)
    
    
    
    
    
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UML Diagram Generator</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        .fade-in {
            animation: fadeIn 1s ease-in-out;
        }
        @keyframes fadeIn {
            0% { opacity: 0; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body class="bg-gray-100 min-h-screen p-8">
    <div class="max-w-6xl mx-auto grid grid-cols-6  space-x-8">
        <!-- Input Form Section -->
        <div class="bg-white rounded-lg col-span-2 shadow-md p-6">
            <h1 class="text-3xl font-bold text-gray-800 mb-8">UML Diagram Generator</h1>
            <form id="diagramForm" class="space-y-6">
                <div>
                    <label for="project_name" class="block text-sm font-medium text-gray-700">Project Name</label>
                    <input type="text" id="project_name" name="project_name" required
                           class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500">
                </div>
                
                <div>
                    <label for="diagram_type" class="block text-sm font-medium text-gray-700">Diagram Type</label>
                    <select id="diagram_type" name="diagram_type" required
                            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500">
                        <option value="class">Class Diagram</option>
                        {% for type in diagram_types %}
                        <option value="{{ type }}">{{ type }}</option>
                        {% endfor %}
                    </select>
                </div>
                
                <button type="submit" 
                        class="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2">
                    Generate Diagram
                </button>
            </form>
        </div>
        
        <!-- Results Section -->
        <div id="results" class=" col-span-4 place-content-center     space-y-6">
            <div class="bg-white rounded-lg shadow-md p-6 ">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-semibold text-gray-800">Generated Diagram</h2>
                    <button id="downloadButton" 
                            class="bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2">
                        Download Diagram
                    </button>
                </div>
                <img id="diagram" class="max-w-full h-auto fade-in " alt="Generated UML Diagram">
            </div>
            
            <div class="bg-white rounded-lg shadow-md p-6">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-semibold text-gray-800">PlantUML Syntax</h2>
                    <button id="copyButton" 
                            class="bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
                        Copy Code
                    </button>
                </div>
                <pre id="syntax" class="bg-gray-50 p-4 rounded-md overflow-x-auto"></pre>
            </div>
        </div>

        <div id="loading" class="hidden flex w-full justify-center items-center space-x-2 place-self-center">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            <span class="text-gray-600">Generating diagram...</span>
        </div>

        <div id="error" class="hidden bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-8">
            <span id="errorMessage"></span>
        </div>
    </div>


  

    <!-- Success Pop-up Messages -->
    <div id="message" class="fixed bottom-5 right-5 bg-green-500 text-white p-4 rounded-lg shadow-md hidden">
        <span id="messageText"></span>
    </div>

    <script>
        document.getElementById('diagramForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const loading = document.getElementById('loading');
            const error = document.getElementById('error');
            const results = document.getElementById('results');
            const message = document.getElementById('message');
            const messageText = document.getElementById('messageText');
            
            // Show loading, hide other sections
            loading.classList.remove('hidden');
            error.classList.add('hidden');
            results.classList.add('hidden');
            
            try {
                const formData = new FormData(e.target);
                const response = await fetch('/generate', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // Update diagram and syntax
                    document.getElementById('diagram').src = `data:image/png;base64,${data.diagram}`;
                    document.getElementById('syntax').textContent = data.syntax;
                    results.classList.remove('hidden');
                    messageText.textContent = "Diagram generated successfully!";
                    message.classList.remove('hidden');
                    setTimeout(() => message.classList.add('hidden'), 3000);
                } else {
                    throw new Error(data.error || 'Failed to generate diagram');
                }
            } catch (err) {
                error.classList.remove('hidden');
                document.getElementById('errorMessage').textContent = err.message;
            } finally {
                loading.classList.add('hidden');
            }
        });

        // Copy PlantUML code button
        document.getElementById('copyButton').addEventListener('click', async () => {
            const syntax = document.getElementById('syntax').textContent;
            try {
                await navigator.clipboard.writeText(syntax);
                const button = document.getElementById('copyButton');
                button.textContent = 'Copied!';
                button.classList.remove('bg-blue-600', 'hover:bg-blue-700');
                button.classList.add('bg-green-600', 'hover:bg-green-700');
                setTimeout(() => {
                    button.textContent = 'Copy Code';
                    button.classList.remove('bg-green-600', 'hover:bg-green-700');
                    button.classList.add('bg-blue-600', 'hover:bg-blue-700');
                }, 2000);
                
                // Show success message
                const message = document.getElementById('message');
                const messageText = document.getElementById('messageText');
                messageText.textContent = "Code copied to clipboard!";
                message.classList.remove('hidden');
                setTimeout(() => message.classList.add('hidden'), 3000);
            } catch (err) {
                console.error('Failed to copy text:', err);
            }
        });

        // Download diagram button
        document.getElementById('downloadButton').addEventListener('click', () => {
            const img = document.getElementById('diagram');
            const link = document.createElement('a');
            link.download = 'diagram.png';
            link.href = img.src;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Show success message
            const message = document.getElementById('message');
            const messageText = document.getElementById('messageText');
            messageText.textContent = "Diagram downloaded successfully!";
            message.classList.remove('hidden');
            setTimeout(() => message.classList.add('hidden'), 3000);
        });
    </script>
</body>
</html>