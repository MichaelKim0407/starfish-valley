import os
import typing
from functools import cached_property

from returns import returns

from utils import merge
from . import t
from .base import AbstractProcessor, JsonFileProcessor
from .fish import FishProcessor


class BundleProcessorMixin(AbstractProcessor):
    RESULT_BUNDLE_EN_NAME = 'en_name'
    RESULT_BUNDLE_NAME = 'name'
    RESULT_BUNDLE_ITEMS = 'items'

    @property
    def _raw_bundles(self) -> typing.Iterator:
        raise NotImplementedError

    def _process_bundle(self, raw_bundle) -> dict | None:
        raise NotImplementedError

    @cached_property
    @returns(list)
    def _bundles(self) -> list[dict]:
        for raw_bundle in self._raw_bundles:
            bundle = self._process_bundle(raw_bundle)
            if not bundle[self.RESULT_BUNDLE_ITEMS]:
                continue
            yield bundle

    def __iter__(self) -> typing.Iterator[dict]:
        yield from self._bundles

    @cached_property
    @returns(merge)
    def _fish_bundles(self) -> dict[t.FishId, list[dict]]:
        for bundle in self._bundles:
            for fish_id in bundle[self.RESULT_BUNDLE_ITEMS]:
                yield fish_id, {
                    self.RESULT_BUNDLE_EN_NAME: bundle[BundleProcessor.RESULT_BUNDLE_EN_NAME],
                    self.RESULT_BUNDLE_NAME: bundle[BundleProcessor.RESULT_BUNDLE_NAME],
                }

    def __getitem__(self, fish_id: t.FishId) -> list[dict] | None:
        return self._fish_bundles.get(fish_id)


class BundleProcessor(JsonFileProcessor, BundleProcessorMixin):
    FILENAME = os.path.join('Data', 'Bundles')

    @property
    def _raw_bundles(self) -> typing.Iterator:
        yield from self._raw_data.values()

    @cached_property
    def _fish_processor(self) -> FishProcessor:
        return self.parent.get_processor(FishProcessor)

    @returns(list)
    def _parse_items(self, items: str) -> list[t.FishId]:
        values = items.split(' ')
        for i in range(0, len(values), 3):
            item_id = values[i]
            if item_id not in self._fish_processor:
                continue
            yield item_id

    def _process_bundle(self, value: str) -> dict | None:
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

        item_ids = self._parse_items(items)

        return {
            self.RESULT_BUNDLE_EN_NAME: name,
            self.RESULT_BUNDLE_NAME: localized_name,
            self.RESULT_BUNDLE_ITEMS: item_ids,
        }


class RemixedBundleNameProcessor(JsonFileProcessor):
    FILENAME = os.path.join('Strings', 'BundleNames')

    def __getitem__(self, en_name: t.BundleEnName) -> t.BundleName | None:
        return self._raw_data.get(en_name)


class RemixedBundleProcessor(JsonFileProcessor, BundleProcessorMixin):
    FILENAME = os.path.join('Data', 'RandomBundles')
    USE_LOCALE = False

    @property
    def _raw_bundles(self) -> typing.Iterator:
        for area in self._raw_data:
            for bundle_set in area['BundleSets']:
                yield from bundle_set['Bundles']
            yield from area['Bundles']

    @cached_property
    def _fish_processor(self) -> FishProcessor:
        return self.parent.get_processor(FishProcessor)

    @returns(list)
    def _parse_items(self, items: str) -> list[t.FishId]:
        for item in items.split(','):
            item = item.strip()
            count, item_en_name = item.split(' ', maxsplit=1)
            item_id = self._fish_processor.get_id_from_en_name(item_en_name)
            if item_id is None:
                continue
            yield item_id

    @cached_property
    def _bundle_name_processor(self) -> RemixedBundleNameProcessor:
        return self.parent.get_processor(RemixedBundleNameProcessor)

    def _process_bundle(self, bundle_raw) -> dict | None:
        name = bundle_raw['Name']
        localized_name = self._bundle_name_processor[name]
        return {
            self.RESULT_BUNDLE_EN_NAME: name,
            self.RESULT_BUNDLE_NAME: localized_name,
            self.RESULT_BUNDLE_ITEMS: self._parse_items(bundle_raw['Items']),
        }


class AllBundleProcessor(BundleProcessorMixin):
    PROCESSORS = (
        BundleProcessor,
        RemixedBundleProcessor,
    )

    @property
    def _processors(self) -> list[BundleProcessorMixin]:
        for processor_cls in self.PROCESSORS:
            yield self.parent.get_processor(processor_cls)

    @cached_property
    @returns(list)
    def _bundles(self) -> list[dict]:
        seen = set()
        for processor in self._processors:
            for bundle in processor:
                en_name = bundle[self.RESULT_BUNDLE_EN_NAME]
                if en_name in seen:
                    continue
                seen.add(en_name)
                yield bundle
