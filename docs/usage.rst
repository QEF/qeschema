********************************
Extracting data from  XML files
********************************

PwDocument instances can be used to extract data from XML data files converting them to dictionaries. 
One has just to create a PwDocument object use it to read the XML file and then use the decoders provided 
by qeschema. 


::
   
   >>>import qeschema
   >>>doc = qeschema.PwDocument(schema='../qeschema/schemas/releases/qes_190304.xsd')
   >>>doc.read('pwscf.save/data-file-schema.xml') 
   >>>pwdict = doc.to_dict() 
   >>>bsdict = pwdict['qes:espresso']['output']['band_structure'] 


One can also use the elementpath  and xmlschema functionalities of the PwDocument object and obtain directly 
the desired dictionary: 

::

    >>>import qeschema
    >>>doc = qeschema.PwDocument(schema='../qeschema/schemas/releases/qes_190304.xsd')
    >>>doc.read('pwscf.save/data-file-schema.xml') 
    >>>path = './/output/band_structure' 
    >>>bsdict = doc.schema.find(path).decode(doc.find(path) 


In the pwdata module can be found a group of helper functions for extracting data from a XML data file produced by pw.x. It is sufficient give in input the path to the XML data file. If one provides the path to the schema file a strict validation of the file format is also done.  

.. autofunction:: qeschema.pwdata.get_total_energy 
