import os
import zipfile
from io import BytesIO

from flask import Response

def download_files(list_files):
    # list_files = [
    #     "/home/leobahm/Escritorio/l7-back-end/media/users/documents/Rut_aQTaQ3I.pdf"
    # ]
    zip_subdir = "archivos"
    zip_filename = "%s.zip" % zip_subdir
    s = BytesIO()
    zf = zipfile.ZipFile(s, "w")

    for fpath in list_files:
        zip_path = fpath.split("_convert\\")[-1]
        
        # Add file, at correct path
        #zf.write(os.path.join(path,fpath), zip_path)
        zf.write(fpath, zip_path)

    # Must close zip for all contents to be written
    zf.close()

    response = Response(s.getvalue(), content_type = "application/x-zip-compressed")
    # # ..and correct content-disposition
    # response['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

    return response