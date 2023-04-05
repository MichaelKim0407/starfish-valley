from typing import TypeVar, Sequence

LangCode = TypeVar('LangCode', bound=str | None)
LocaleDict = dict[LangCode, str | None]
Translatable = LocaleDict | str | None

FishId = TypeVar('FishId', bound=str)
FishEnName = TypeVar('FishEnName', bound=str)
FishName = TypeVar('FishName', bound=str)
Weather = TypeVar('Weather', bound=str)
Weathers = Sequence[Weather]
Hour = TypeVar('Hour', bound=int)
TimeRange = tuple[Hour, Hour]
TimeRanges = Sequence[TimeRange]

LocationKey = TypeVar('LocationKey', bound=str)
LocationVariation = TypeVar('LocationVariation', bound=str)
LocationName = TypeVar('LocationName', bound=str)
Season = TypeVar('Season', bound=str)

BundleEnName = TypeVar('BundleEnName', bound=str)
BundleName = TypeVar('BundleName', bound=str)

CharacterKey = TypeVar('CharacterKey', bound=str)
CharacterName = TypeVar('CharacterName', bound=str)
CharacterPreferenceType = TypeVar('CharacterPreferenceType', bound=str)
CharacterPreferences = dict[CharacterPreferenceType, list[FishId]]
