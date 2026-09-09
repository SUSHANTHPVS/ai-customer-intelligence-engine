"""
Customer Intelligence Engine - Main Package
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__description__ = "An end-to-end analytics platform for customer churn prediction and revenue risk management"

from .utils.logger import get_logger

logger = get_logger(__name__)
