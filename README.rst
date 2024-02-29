=====================================================
Quantum Espresso tools for XML Schema based documents
=====================================================

.. qeschema-introduction

The `qeschema <https://github.com/QEF/qeschema>`_ package provides tools for
converting XML data produced by the Quantum ESPRESSO suite of codes (ESPRESSO:
opEn-Source Package for Research in Electronic Structure, Simulation and Optimization).

Requirements
------------

* Python_ 3.7+
* xmlschema_ (Python library for processing XML Schema based documents)

.. _Python: http://www.python.org/
.. _xmlschema: https://github.com/brunato/xmlschema


Installation
------------

You can install the library with *pip* in a Python 3.7+ environment::

    pip install qeschema

If you need HDF5 utilities and/or the YAML format, install the extra
features using the appropriate command from these alternatives::

    pip install qeschema[HDF5]
    pip install qeschema[YAML]
    pip install qeschema[HDF5,YAML]


Usage
-----

Define you data document using:

.. code-block:: pycon

    >>> import qeschema
    >>> pw_document = qeschema.PwDocument()

and then read XML data from a file processed by the corresponding application of
Quantum ESPRESSO suite:

.. code-block:: pycon

    >>> pw_document.read("tests/examples/pw/Si.xml")

Loaded data can be decoded to Python data dictionary or written to JSON or YAML formats:

.. code-block:: pycon

    >>> xml_data = pw_document.to_dict()
    >>> json_data = pw_document.to_json()


Authors
-------
* Davide Brunato
* Pietro Delugas
* Giovanni Borghi
* Alexandr Fonari


License
-------
This software is distributed under the terms of the MIT License.
See the file 'LICENSE' in the root directory of the present
distribution, or http://opensource.org/licenses/MIT.

