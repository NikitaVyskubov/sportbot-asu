# techniques/__init__.py
from .chest import CHEST_TECHNIQUES
from .back import BACK_TECHNIQUES
from .legs import LEGS_TECHNIQUES
from .shoulders import SHOULDERS_TECHNIQUES
from .arms import ARMS_TECHNIQUES
from .core import CORE_TECHNIQUES

TECHNIQUES = {
    **CHEST_TECHNIQUES,
    **BACK_TECHNIQUES,
    **LEGS_TECHNIQUES,
    **SHOULDERS_TECHNIQUES,
    **ARMS_TECHNIQUES,
    **CORE_TECHNIQUES,
}

CATEGORIES = {
    "ГРУДЬ": list(CHEST_TECHNIQUES.keys()),
    "СПИНА": list(BACK_TECHNIQUES.keys()),
    "НОГИ": list(LEGS_TECHNIQUES.keys()),
    "ПЛЕЧИ": list(SHOULDERS_TECHNIQUES.keys()),
    "РУКИ": list(ARMS_TECHNIQUES.keys()),
    "ПРЕСС И КОР": list(CORE_TECHNIQUES.keys()),
}

__all__ = ['TECHNIQUES', 'CATEGORIES']