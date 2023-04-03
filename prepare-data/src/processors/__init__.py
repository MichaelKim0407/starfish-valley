import json
import os
from functools import cached_property


class LanguageProcessor:
    LANGUAGES = {
        None: 'English',  # English
        'ru-RU': 'Русский',  # Russian
        'zh-CN': '简体中文',  # Simplified Chinese
        'de-DE': 'Deutsch',  # German
        'pt-BR': 'Português',  # Brazilian Portuguese
        'fr-FR': 'Français',  # French
        'es-ES': 'Español',  # Spanish
        'ja-JP': '日本語',  # Japanese
        'ko-KR': '한국어',  # Korean
        'it-IT': 'Italiano',  # Italian
        'tr-TR': 'Türkçe',  # Turkish
        'hu-HU': 'Magyar',  # Hungarian
    }

    @classmethod
    def run_all(cls, source: str, output: str, version_name: str):
        for lang_code in cls.LANGUAGES:
            processor = cls(source, output, version_name, lang_code)
            processor()

    def __init__(self, source: str, output: str, version_name: str, lang_code: str):
        self.source = source
        self.output = output
        self.version_name = version_name
        self.lang_code = lang_code

    @cached_property
    def language(self) -> str:
        return self.LANGUAGES[self.lang_code]

    @cached_property
    def data(self):
        return {
            'version': self.version_name,
            'lang_code': self.lang_code,
            'language': self.language,
        }

    @cached_property
    def output_file_name(self) -> str:
        return os.path.join(self.output, f'{self.version_name} ({self.language}).json')

    def __call__(self):
        with open(self.output_file_name, 'w') as f:
            json.dump(self.data, f)
