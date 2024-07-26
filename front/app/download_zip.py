import os
import zipfile
from io import BytesIO
from flask import send_file
from flask import Response

def download_files(list_files,filename):
    zip_subdir = "archivos"
    #s = BytesIO()
    zf = zipfile.ZipFile(filename, "w")

    for fpath in list_files:
        zip_path = fpath.split("_convert\\")[-1]
        zf.write(fpath, zip_path)

    # Must close zip for all contents to be written
    zf.close()
    name = 'bids-converted_dataset.zip'
    #response = Response(s.getvalue(), content_type = "application/x-zip-compressed")
    #response['Content-Disposition'] = 'attachment; filename= "%s"' % filename

    # See https://stackoverflow.com/a/53390515/14068216
    response = send_file(filename, mimetype="application/x-zip-compressed", download_name=name, as_attachment=True)
    response.headers["x-filename"] = name
    response.headers["Access-Control-Expose-Headers"] = 'x-filename'
    # # ..and correct content-disposition
    # response['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

    return response
