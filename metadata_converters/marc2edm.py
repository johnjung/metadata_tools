#!/usr/bin/env python
"""Usage:
    marc2edm (--socscimaps -|--socscimaps-project-triples)
"""

import getpass
import hashlib
import os
import paramiko
import pathlib
import shutil
import subprocess
import tempfile
import sys
import xml.etree.ElementTree as ElementTree
from . import SocSciMapsMarcXmlToEDM
from docopt import docopt
from PIL import Image
Image.MAX_IMAGE_PIXELS = 1000000000

def main():
    options = docopt(__doc__)

    if options['--socscimaps']:
        collection = ElementTree.fromstring(sys.stdin.read())

        for record in collection.findall('{http://www.loc.gov/MARC21/slim}record'):
            identifier = record.find('/'.join([
                '{http://www.loc.gov/MARC21/slim}datafield[@tag="856"]',
                '{http://www.loc.gov/MARC21/slim}subfield[@code="u"]'
            ])).text.split('/').pop()
            tiff_path = '/'.join([
                '',
                'data',
                'digital_collections',
                'IIIF',
                'IIIF_Files',
                'maps',
                'chisoc',
                identifier,
                'tifs',
                '{0}.tif'.format(identifier)
            ])

            try:
                mime_type = 'image/tiff'
                size = os.path.getsize(tiff_path)
                img = Image.open(tiff_path)
                width = img.size[0]
                height = img.size[1]
            except AttributeError:
                sys.stdout.write('trouble with {}\n'.format(tiff_path))
                sys.exit()

            with open(tiff_path, 'rb') as f:
                tiff_contents = f.read()
                md5 = hashlib.md5(tiff_contents).hexdigest()
                sha256 = hashlib.sha256(tiff_contents).hexdigest()
   
            edm = SocSciMapsMarcXmlToEDM(
                '<collection>{}</collection>'.format(
                    ElementTree.tostring(record, 'utf-8', method='xml').decode('utf-8')
                ),
                [{
                    'height': height,
                    'md5': md5,
                    'mime_type': mime_type,
                    'name': '{}.tif'.format(identifier),
                    'path': tiff_path,
                    'sha256': sha256,
                    'size': size,
                    'width': width
                }]
            )

        edm.build_item_triples()

    if options['--socscimaps-project-triples']:
        SocSciMapsMarcXmlToEDM.build_repository_triples()
        SocSciMapsMarcXmlToEDM.build_digital_collections_triples()
        SocSciMapsMarcXmlToEDM.build_map_collection_triples()
        SocSciMapsMarcXmlToEDM.build_socscimap_collection_triples()

        
    sys.stdout.write(SocSciMapsMarcXmlToEDM.triples())

if __name__ == "__main__":
    main()
