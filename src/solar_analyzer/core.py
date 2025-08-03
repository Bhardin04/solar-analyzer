"""Core application components."""

from fastapi.templating import Jinja2Templates

# Setup templates
templates = Jinja2Templates(directory="src/solar_analyzer/templates")
