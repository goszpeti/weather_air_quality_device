import json
from pathlib import Path

from piweather import config
from piweather.base.logger import Logger


def get_rsc_file(rsc_dir: str, rsc_id: str) -> Path:
    """
    Get a an indexed resource file from the specfifed path.
    The function expects a filetoc.json, with a mapping from id to filename in "filelist".
    An additional "filetype" an be specified for a default extension. (without the dot)
    No error is raised, the error is only logged.
    # TODO: a scan function for finding missing files would be nice.
    """

    # read filetoc.json
    rsc_path = config.resource_path / rsc_dir
    ftoc_path = rsc_path / "filetoc.json"
    content = {}
    logger = Logger()

    if not ftoc_path.exists():
        logger.error("Cannot find catalog file %s", ftoc_path)
        return None

    with open(ftoc_path, encoding='utf-8') as filetoc:
        content = json.load(filetoc)

    # get filetype and filelist
    filetype = content.get("filetype")
    filelist = content.get("filelist")

    file_name = filelist.get(rsc_id)
    if not file_name:
        logger.error(f"Cannot find resource id {rsc_id} in catalog")
        return None
    # append filetype, if applicable
    if filetype:
        file_name = file_name + "." + filetype

    rsc_file_path = rsc_path / file_name
    if not rsc_file_path.exists():
        logger.error("Cannot find resource file %s in %s", file_name, str(rsc_dir))
        return None

    return rsc_file_path
