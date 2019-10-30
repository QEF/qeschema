=====================================================
Quantum Espresso tools for XML Schema based Documents
=====================================================

Tools for converting XML data produced by the Quantum ESPRESSO suite of codes 
(ESPRESSO: opEn-Source Package for Research in Electronic Structure, Simulation, 
and Optimization).

Requirements
------------

* Python_ 3.5+
* xmlschema_ (Python library for processing XML Schema based documents)

.. _Python: http://www.python.org/
.. _xmlschema: https://github.com/brunato/xmlschema


Installation
------------

You can install the library with *pip* in a Python 3.5+ environment::

    pip install qeschema


Usage
-----

Define you data document using:

.. code-block:: pycon

    >>> import qeschema
    >>> my_document = qeschema.PwDocument()

and then read XML data from a file processed by the corresponding application of
Quantum ESPRESSO suite:

.. code-block:: pycon

    >>> my_document.read("my_data.xml")

Loaded data can be decoded to Python data dictionary or written to JSON or YAML formats.


Authors
-------
Davide Brunato
Pietro Delugas
Giovanni Borghi


License
-------
This software is distributed under the terms of the MIT License.
See the file 'LICENSE' in the root directory of the present
distribution, or http://opensource.org/licenses/MIT.

