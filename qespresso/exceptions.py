# -*- coding: utf-8 -*-
"""
This module contain exception classes for Quantum Espresso package.
"""

import logging

logger = logging.getLogger('qespresso')


class QEspressoError(Exception):
    pass


class ConfigError(QEspressoError):
    """
    This exception is raised when there are errors with the validation
    of a XML configuration.
    """
    def __init__(self, message):
        Exception.__init__(self, message)
        logger.debug('!ConfigError: {0}'.format(message))


