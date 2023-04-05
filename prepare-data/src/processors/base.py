import json
import os
from functools import cached_property

from . import t
from .languages import LanguageProcessor


class AbstractProcessor:
    def __init__(self, parent: LanguageProcessor):
        self.parent = parent

    def __call__(self, result: t.Result):
        raise NotImplementedError


class FileProcessor(AbstractProcessor):
    FILENAME: str = None
    EXT: str = None
    USE_LOCALE: bool = True

    def __init__(
            self,
            parent: LanguageProcessor,
            filename: str = None,
            ext: str = None,
            use_locale: bool = None,
    ):
        super().__init__(parent)

        if filename is None:
            filename = self.FILENAME
        self.filename = filename

        if ext is None:
            ext = self.EXT
        self.ext = ext

        if use_locale is None:
            use_locale = self.USE_LOCALE
        self.use_locale = use_locale

    @cached_property
    def _filename(self) -> str:
        if (not self.use_locale) or self.parent.lang_code is None:
            return f'{self.filename}.{self.ext}'
        else:
            return f'{self.filename}.{self.parent.lang_code}.{self.ext}'

    @cached_property
    def _source_file_name(self) -> str:
        return os.path.join(self.parent.game_data_dir, self._filename)


class JsonFileProcessor(FileProcessor):
    EXT = 'json'

    @cached_property
    def _raw_data(self):
        with open(self._source_file_name) as f:
            return json.load(f)
