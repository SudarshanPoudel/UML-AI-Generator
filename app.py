import re
import base64
import logging
import os
import plantuml
import streamlit as st
import g4f

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
st.set_page_config(page_title="UML Senpai",page_icon="📈", initial_sidebar_state="expanded")

# Initialize PlantUML instance
plantuml_instance = plantuml.PlantUML(url='http://www.plantuml.com/plantuml/img/')

def get_plantuml_themes():
    """Return the fixed list of available PlantUML themes."""
    return [
        "plain",
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


def generate_ai_prompt(project_name, diagram_type, description=None, theme=None):
    theme_directive = f"!theme {theme}\n" if theme  else ""
    description_directive = f"{description}\n" if description else ""
    return f"""Create a PlantUML syntax for a {diagram_type} for a project named {project_name}. 
    The diagram should include the essential elements with basic functionality, following UML standards. 
    {description_directive}
    Keep it simple and avoid excessive details. 
    Start with @startuml
    {theme_directive}"""


def extract_plantuml_syntax(text):
    """Extract and clean PlantUML syntax between @startuml and @enduml tags."""
    pattern = r'@startuml\s*(.*?)\s*@enduml'
    match = re.search(pattern, text, re.DOTALL)
    
    if not match:
        raise Exception("No valid PlantUML syntax found in AI response")
    
    content = match.group(1).strip()
    return content

def get_ai_response(prompt):
    """Get response from AI API."""
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
    """Generate a diagram image from PlantUML syntax."""
    try:
        png_data = plantuml_instance.processes(plantuml_syntax)
        return base64.b64encode(png_data).decode()
    except Exception as e:
        logger.error(f"PlantUML Processing Error: {str(e)}")
        logger.error("Try again")
        raise

st.title("UML-SENPAI")
st.write("Generate UML diagrams using AI and PlantUML")

project_name = st.text_input("Project Name")
diagram_types = [
    "Sequence Diagram", "Use Case Diagram", "Class Diagram", "Object Diagram", "Activity Diagram",
    "Component Diagram", "Deployment Diagram", "State Diagram", "Timing Diagram"
]
themes = get_plantuml_themes()
diagram_type = st.selectbox("Select Diagram Type", diagram_types)
theme = st.selectbox("Select Theme", themes)
description = st.text_area("Additional Prompt (Optional)")
if st.button("Generate Diagram", type="primary"):
    if not project_name or not diagram_type:
        st.error("Project Name and Diagram Type are required")
        
    else:
        prompt = generate_ai_prompt(project_name, diagram_type, description, theme=theme)
        
        try:
            plantuml_syntax = get_ai_response(prompt)
            diagram_base64 = generate_diagram(plantuml_syntax)
            
            st.subheader(f"Generated {diagram_type}")
            st.image(f"data:image/png;base64,{diagram_base64}", use_container_width=True)
            image_data = base64.b64decode(diagram_base64)
            st.download_button(
                label="Download Diagram",
                data=image_data,
                file_name=f"umlsenpai-{project_name}-{diagram_type}.png",
                mime="image/png",   
                type="primary"
            )

        except Exception as e:
            st.error(str(e))
            raise

