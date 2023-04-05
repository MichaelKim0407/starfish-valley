import os
import typing
from functools import cached_property

from returns import returns

from .base import AbstractProcessor, JsonFileProcessor
from .fish import FishProcessor


class BundleProcessor(JsonFileProcessor):
    FILENAME = os.path.join('Data', 'Bundles')

    # RESULT_BUNDLE_AREA_NAME = 'area_name'
    # RESULT_BUNDLE_KEY = 'key'
    RESULT_BUNDLE_EN_NAME = 'en_name'
    RESULT_BUNDLE_NAME = 'name'
    RESULT_BUNDLE_ITEMS = 'items'
    RESULT_BUNDLE_ITEM_ID = FishProcessor.RESULT_ID

    @classmethod
    @returns(list)
    def _parse_items(cls, items: str) -> list[dict]:
        values = items.split(' ')
        for i in range(0, len(values), 3):
            yield {cls.RESULT_BUNDLE_ITEM_ID: values[i]}

    def _parse_bundle_value(self, value: str) -> dict:
        # https://stardewvalleywiki.com/Modding:Bundles
        (
            name,
            reward,
            items,
            color,
            *other_fields,
        ) = value.split('/')

        if self.parent.lang_code is not None:
            localized_name = other_fields[-1]
        else:
            localized_name = name

        return {
            self.RESULT_BUNDLE_EN_NAME: name,
            self.RESULT_BUNDLE_NAME: localized_name,
            self.RESULT_BUNDLE_ITEMS: self._parse_items(items),
        }

    @cached_property
    @returns(dict)
    def _bundles(self) -> dict[str, dict]:
        for key, value in self._raw_data.items():
            # area_name, bundle_key = key.split('/')
            bundle = self._parse_bundle_value(value)
            # bundle[self.RESULT_BUNDLE_AREA_NAME] = area_name
            # bundle[self.RESULT_BUNDLE_KEY] = int(bundle_key)
            yield bundle[self.RESULT_BUNDLE_EN_NAME], bundle

    def __iter__(self) -> typing.Iterator[tuple[str, dict]]:
        yield from self._bundles.items()

    def __contains__(self, en_name: str) -> bool:
        return en_name in self._bundles


class RemixedBundleNameProcessor(JsonFileProcessor):
    FILENAME = os.path.join('Strings', 'BundleNames')

    def __getitem__(self, en_name: str) -> str | None:
        return self._raw_data.get(en_name)


class RemixedBundleProcessor(JsonFileProcessor):
    FILENAME = os.path.join('Data', 'RandomBundles')
    USE_LOCALE = False

    RESULT_BUNDLE_ITEM_EN_NAME = FishProcessor.RESULT_EN_NAME

    @staticmethod
    def _area_bundles_raw(area):
        for bundle_set in area['BundleSets']:
            yield from bundle_set['Bundles']
        yield from area['Bundles']

    @classmethod
    @returns(list)
    def _parse_items(cls, items: str) -> list[dict]:
        for item in items.split(','):
            item = item.strip()
            count, item_en_name = item.split(' ', maxsplit=1)
            yield {cls.RESULT_BUNDLE_ITEM_EN_NAME: item_en_name}

    @cached_property
    def _bundle_name_processor(self) -> RemixedBundleNameProcessor:
        return self.parent.get_processor(RemixedBundleNameProcessor)

    def _process_bundle(self, bundle_raw) -> dict:
        name = bundle_raw['Name']
        localized_name = self._bundle_name_processor[name]
        return {
            BundleProcessor.RESULT_BUNDLE_EN_NAME: name,
            BundleProcessor.RESULT_BUNDLE_NAME: localized_name,
            BundleProcessor.RESULT_BUNDLE_ITEMS: self._parse_items(bundle_raw['Items']),
        }

    @cached_property
    @returns(dict)
    def _bundles(self) -> dict[str, dict]:
        for area in self._raw_data:
            # area_name = area['AreaName']
            for bundle_raw in self._area_bundles_raw(area):
                bundle = self._process_bundle(bundle_raw)
                # bundle[BundleProcessor.RESULT_BUNDLE_AREA_NAME] = area_name
                yield bundle[BundleProcessor.RESULT_BUNDLE_EN_NAME], bundle

    def __iter__(self) -> typing.Iterator[tuple[str, dict]]:
        yield from self._bundles.items()

    def __contains__(self, en_name: str) -> bool:
        return en_name in self._bundles


class AllBundleProcessor(AbstractProcessor):
    RESULT_SUBKEY = 'bundles'

    @cached_property
    def _bundle_processor(self) -> BundleProcessor:
        return self.parent.get_processor(BundleProcessor)

    @cached_property
    def _remixed_bundle_processor(self) -> RemixedBundleProcessor:
        return self.parent.get_processor(RemixedBundleProcessor)

    @cached_property
    @returns(dict)
    def _bundles(self) -> dict[str, dict]:
        yield from self._bundle_processor

        for en_name, bundle in self._remixed_bundle_processor:
            if en_name in self._bundle_processor:
                continue
            yield en_name, bundle

    def __call__(self, result: dict):
        for bundle in self._bundles.values():
            for item in bundle[BundleProcessor.RESULT_BUNDLE_ITEMS]:
                item_id = item.get(BundleProcessor.RESULT_BUNDLE_ITEM_ID)
                item_en_name = item.get(RemixedBundleProcessor.RESULT_BUNDLE_ITEM_EN_NAME)
                for fish in result[FishProcessor.RESULT_KEY].values():
                    if not (
                            (item_id is not None and fish[FishProcessor.RESULT_ID] == item_id)
                            or (item_en_name is not None and fish[FishProcessor.RESULT_EN_NAME] == item_en_name)
                    ):
                        continue

                    if self.RESULT_SUBKEY not in fish:
                        fish[self.RESULT_SUBKEY] = []
                    fish[self.RESULT_SUBKEY].append({
                        BundleProcessor.RESULT_BUNDLE_EN_NAME: bundle[BundleProcessor.RESULT_BUNDLE_EN_NAME],
                        BundleProcessor.RESULT_BUNDLE_NAME: bundle[BundleProcessor.RESULT_BUNDLE_NAME],
                    })
                    break
