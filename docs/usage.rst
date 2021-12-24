********************************
Extracting data from  XML files
********************************

PwDocument instances can be used to extract data from XML data files converting them to dictionaries. 
One has just to create a PwDocument object use it to read the XML file and then use the decoders provided 
by qeschema. 

.. testsetup::

    import os
    project_dir = os.path.dirname(os.path.abspath('.'))
    os.chdir(project_dir)

.. doctest::
   
   >>> import qeschema
   >>> doc = qeschema.PwDocument(schema='qes.xsd')
   >>> doc.read('tests/resources/pw/Al001_relax_bfgs.xml')
   >>> pw_data = doc.to_dict()
   >>> control_variables = pw_data['qes:espresso']['input']['control_variables']


One can also use the elementpath  and xmlschema functionalities of the PwDocument object and obtain directly 
the desired dictionary: 

.. doctest::

    >>> import qeschema
    >>> doc = qeschema.PwDocument()
    >>> doc.read('tests/resources/pw/CO_bgfs_relax.xml')
    >>> path = './/input/atomic_species'
    >>> bsdict = doc.to_dict(path=path)
