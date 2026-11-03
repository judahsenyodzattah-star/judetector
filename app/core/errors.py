"""Domain errors for JUDEtector.

Every error here is *reportable*: the UI catches them and shows the user what is
actually wrong (missing weights, missing package, bad image) instead of crashing
or, worse, pretending a detection happened.
"""

from __future__ import annotations


class JudetectorError(Exception):
    """Base class for all application errors."""


class ModelUnavailableError(JudetectorError):
    """The detector cannot run: weights are missing, or the ML stack is absent."""


class ModelLoadError(JudetectorError):
    """Weights were found but could not be loaded or used."""


class InvalidImageError(JudetectorError):
    """The uploaded/captured file is not a usable image."""


class MetricsUnavailableError(JudetectorError):
    """Evaluation metrics were requested but no metrics record exists."""


class MetricsSchemaError(JudetectorError):
    """A metrics record exists but does not match the expected schema."""


class RegistryError(JudetectorError):
    """The model registry configuration is missing or malformed."""
