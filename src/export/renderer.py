"""Jinja2 template rendering."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template

from src.logging_config import get_logger

logger = get_logger(__name__)


class TemplateRenderer:
    """Template renderer using Jinja2."""

    def __init__(self, templates_dir: Path | str = "templates"):
        """Initialize renderer.

        Args:
            templates_dir: Directory containing templates
        """
        self.templates_dir = Path(templates_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, context: dict) -> str:
        """Render template with context.

        Args:
            template_name: Template filename
            context: Template context dictionary

        Returns:
            Rendered string
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            raise


# Global renderer instance
_renderer: TemplateRenderer | None = None


def get_renderer() -> TemplateRenderer:
    """Get global renderer instance.

    Returns:
        Template renderer
    """
    global _renderer
    if _renderer is None:
        _renderer = TemplateRenderer()
    return _renderer
