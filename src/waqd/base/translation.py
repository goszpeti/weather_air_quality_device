import json
from waqd.settings import LANG_ENGLISH, LANG_GERMAN, LANG_HUNGARIAN
from waqd.assets import get_asset_file
from waqd.base.file_logger import Logger

# Runtime translations

# map settings to internal shortened lang names
LANGS_MAP = {
    LANG_ENGLISH: "en",
    LANG_GERMAN: "de",
    LANG_HUNGARIAN: "hu"
}

class Translation():
    _instance = None
    _resources = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_localized_string(self, asset_dir: str, asset_id: str, key: str, lang=LANG_ENGLISH) -> str:
        if lang in LANGS_MAP:
            lang = LANGS_MAP.get(lang)
        id = asset_dir + "/" + asset_id
        if id not in self._resources.keys():
            dict_file = get_asset_file(asset_dir, asset_id)
            # read filetoc.json
            with open(str(dict_file), encoding='utf-8') as f:
                ts_dict = json.load(f)
            self._resources[id] = ts_dict

        # get filetype and filelist
        lang_dict = self._resources[id].get(lang, {})
        if not lang_dict:
            Logger().error(f"TL: Cannot find language string for {lang}")
            return ""

        value = lang_dict.get(key)
        if not value:
            Logger().error("TL: Cannot find resource id %s in catalog", key)
        return value
