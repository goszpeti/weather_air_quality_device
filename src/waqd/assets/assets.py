import json
from pathlib import Path

import waqd
from waqd.base.file_logger import Logger

TOC_FILE_NAME = "filetoc.json"


def get_asset_file_relative(rsc_file_path: Path) -> str:
    """
    Get a an indexed resource file from the specified path.
    The function expects a filetoc.json, with a mapping from id to filename in "filelist".
    An additional "filetype" an be specified for a default extension. (without the dot)
    No error is raised, the error is only logged.
    """
    return rsc_file_path.relative_to(waqd.assets_path).as_posix()


def get_asset_file(rsc_dir: str, rsc_id: str) -> Path:
    """
    Get a an indexed resource file from the specified path.
    The function expects a filetoc.json, with a mapping from id to filename in "filelist".
    An additional "filetype" an be specified for a default extension. (without the dot)
    No error is raised, the error is only logged.
    """

    if rsc_id == "dummy-pic":  # specal case for a dummy picture
        rsc_dir = "gui_base"
    # read filetoc.json
    rsc_path = waqd.assets_path / rsc_dir
    ftoc_path = rsc_path / TOC_FILE_NAME
    logger = Logger()

    if not ftoc_path.exists():
        logger.debug("Cannot find catalog file %s, fallback to real filename.", ftoc_path)
        file_name = rsc_id
    else:
        content = {}
        with open(ftoc_path, encoding="utf-8") as filetoc:
            content = json.load(filetoc)

        # get filetype and filelist
        filetype = content.get("filetype", "")
        filelist = content.get("filelist", {})

        file_name = filelist.get(rsc_id, "")
        if not file_name:
            logger.debug(
                f"Cannot find resource id {rsc_id} in catalog, fallback to real filename."
            )
            file_name = rsc_id
        # append filetype, if applicable
        if filetype:
            file_name = file_name + "." + filetype

    rsc_file_path = rsc_path / file_name
    if not rsc_file_path.exists():
        logger.error("Cannot find resource file %s in %s", file_name, str(rsc_dir))
        return Path("NULL")

    return rsc_file_path
