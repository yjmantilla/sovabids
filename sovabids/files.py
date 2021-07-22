"""Module with file utilities."""
import os
import requests

def get_files(root_path):
    """Recursively scan the directory for files, returning a list with the full-paths to each.
    
    Parameters
    ----------

    root_path : str
        The path we want to obtain the files from.

    Returns
    -------

    filepaths : list of str
        A list containing the path to each file in root_path.
    """
    filepaths = []
    for root, dirs, files  in os.walk(root_path, topdown=False):
        for name in files:
            filepaths.append(os.path.join(root, name))
    return filepaths



def download(url,path):
    """Download in the path the file from the given url.

    From H S Umer farooq answer at https://stackoverflow.com/questions/22676/how-to-download-a-file-over-http

    Parameters
    ----------

    url : str
        The url of the file to download.
    path : str
        The path where to download the file.
    """
    get_response = requests.get(url,stream=True)
    file_name  = url.split("/")[-1]
    p = os.path.abspath(os.path.join(path))
    os.makedirs(p,exist_ok=True)
    print('Downloading',file_name,'at',p)
    if not os.path.isfile(os.path.join(p,file_name)):
        with open(os.path.join(p,file_name), 'wb') as f:
            for chunk in get_response.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
            print('100')
    else:
        print("WARNING: File already existed. Skipping...")