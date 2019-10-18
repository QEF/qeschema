# -*- coding: utf-8 -*-
#
# Copyright (c), 2015-2019, Quantum Espresso Foundation and SISSA (Scuola
# Internazionale Superiore di Studi Avanzati). All rights reserved.
# This file is distributed under the terms of the MIT License. See the
# file 'LICENSE' in the root directory of the present distribution, or
# http://opensource.org/licenses/MIT.
#
# Authors: Davide Brunato
#
import logging

logger = logging.getLogger('qeschema')


class QESchemaError(Exception):
    pass


class XmlDocumentError(QESchemaError, RuntimeError):
    """An error or a wrong condition with an XML document instance."""

    def __init__(self, message):
        Exception.__init__(self, message)
        logger.debug('!XmlDocumentError: {0}'.format(message))
