"""Конвертирует XSD в pydantic-DTO

https://xmlschema.readthedocs.io/en/latest/

https://pypi.org/project/transliterate/
https://pypi.org/project/cyrtranslit/

https://pydash.readthedocs.io/en/latest/
"""
import datetime
import itertools
import typing

import cyrtranslit
import pydash.strings
import pytz
import xmlschema

ROOT_CLASS = 'upd.dto_xml.XmlBaseModel'
BASE_CLASS = 'XmlBaseClass'
XSD_PATH = '/Users/roveek/Downloads/XSD_NAKLADNAYA/DP_TOVTORGPOK.xsd'
ATTR_TYPE_MAP = {
    'xs:integer': 'int',
    'xs:string': 'str',
    'xs:decimal': 'float',
    # 'xs:decimal': 'pydantic.condecimal',
}
S = '    '
force_list = []


def transliterate(string) -> str:
    return cyrtranslit.to_latin(str(string), 'ru').replace("'", '')


def get_py_type(xsd_type: str) -> str:
    try:
        py_type = ATTR_TYPE_MAP[xsd_type]
    except KeyError:
        print(f'Unknown type {xsd_type=}')
        raise
    else:
        return py_type


def process_simple_type(obj: xmlschema.validators.XsdAtomicRestriction) -> str:
    """Набор ограничений для простого поля"""

    if not isinstance(obj, xmlschema.validators.XsdAtomicRestriction):
        raise TypeError(f'Wrong type {obj.__class__}')

    name = transliterate(obj.name)
    result = [
        f'{name} = dict(',
        f'{S}# {obj.name} ({obj.sequence_type})',
        f'{S}# {obj.annotation!s}',
    ]
    if obj.min_length:
        result += [f'{S}min_length={obj.min_length},']
    if obj.max_length:
        result += [f'{S}max_length={obj.max_length},']
    if obj.patterns and obj.patterns.regexps:
        result += [f"{S}regex=r'{obj.patterns.regexps[0]}',"]
    result += [')']
    return '\n'.join(result)


def process_simple_attribute(obj: xmlschema.validators.XsdAttribute) -> str:
    """Простое поле"""

    name = transliterate(obj.name)
    name = pydash.strings.snake_case(name)
    py_type = get_py_type(obj.type.sequence_type)
    comment = []

    is_required = obj.use == 'required'
    has_enumeration = isinstance(obj.type.enumeration, list) and obj.type.enumeration

    if not is_required:
        py_type = f'typing.Optional[{py_type}]'
    if has_enumeration:
        py_type = f'typing.Literal{obj.type.enumeration}'
    comment.append(f'use={obj.use}')
    result = [
        f'{S}{name}: {py_type} = pydantic.Field(',
        f"{S*2}alias='@{obj.name}',",
        f"{S*2}description='{obj.annotation}',",
    ]
    if not is_required:
        result += [f'{S*2}default=None,']
    elif len(obj.type.enumeration or []) == 1:
        result += [f"{S*2}default='{obj.type.enumeration[0]}',"]
    if not obj.type.name:
        # Наборы ограничений (типа ОКСМТип) уже содержат ограничения длины
        if not has_enumeration:
            # С typing.Literal min_length/max_length не работают
            if obj.type.simple_type.min_length:
                result += [f'{S*2}min_length={obj.type.simple_type.min_length},']
            if obj.type.simple_type.max_length:
                result += [f'{S*2}max_length={obj.type.simple_type.max_length},']
    else:
        result += [f'{S*2}**{transliterate(obj.type.name)},']
    if comment:
        comment = '  # %s' % ' • '.join(comment)
    result += [f'{S}){comment or ""}']
    return '\n'.join(result)


def process_complex_attribute(obj: xmlschema.XsdElement) -> str:
    """Поле-ссылка на объект"""

    name = transliterate(obj.name)
    name_snake = pydash.strings.snake_case(name)
    min_occurs = obj.min_occurs
    max_occurs = obj.max_occurs if obj.max_occurs is not None else '∞'
    comment = [f'[{obj.min_occurs}-{obj.max_occurs}]']
    default_factory = None
    default = None
    min_items = None
    max_items = None

    if obj.type.is_simple():
        py_type = get_py_type(obj.type.sequence_type)
    elif obj.type.name:
        py_type = transliterate(obj.type.name)
    else:
        py_type = name

    if max_occurs == '∞' or max_occurs > 1:
        py_type = f'typing.List[{py_type}]'
        default_factory = 'default_factory=list'
        force_list.append(obj.name)
        if min_occurs > 0:
            # Ограничения min_items/max_items только для списков
            min_items = f'min_items={min_occurs}'
        if str(max_occurs).isdecimal() and max_occurs > 0:
            # При max_occurs == '∞': max_items не указываем
            max_items = f'max_items={max_occurs}'
    if min_occurs < 1 or obj.parent.model == 'choice':
        py_type = f'typing.Optional[{py_type}]'
        default = 'None'
        if obj.parent.model == 'choice':
            comment += [f'{obj.parent.model=} → Optional']

    annotation = str(obj.annotation).replace('\n', ' ')
    result = [
        f'{S}{name_snake}: {py_type} = pydantic.Field(',
        f"{S*2}alias='{obj.name}',",
        f"{S*2}description='{annotation}',",
    ]
    if default_factory:
        result += [f'{S*2}{default_factory},']
    elif default is not None:
        result += [f'{S*2}default={default},']
    if min_items:
        result += [f'{S*2}{min_items},']
    if max_items:
        result += [f'{S*2}{max_items},']
    if obj.type.is_simple():
        if obj.type.simple_type.min_length is not None:
            result += [f'{S*2}min_length={obj.type.simple_type.min_length},']
        if obj.type.simple_type.max_length is not None:
            result += [f'{S*2}max_length={obj.type.simple_type.max_length},']
    comment = '  # %s' % ' • '.join(comment)
    result += [f'{S}){comment}']
    return '\n'.join(result)


def process_xsd_element(
        obj: xmlschema.XsdElement) -> typing.Generator[str, None, None]:
    """Создаёт pydantic-класс из element'a"""

    name = transliterate(obj.name)
    annotation = obj.annotation.documentation[0].text
    result = [
        f'class {name}({BASE_CLASS}):',
        f'    """{obj.name}',
        f'',
        f'    {annotation}',
        f'    """',
    ]
    for attr_name in obj.attributes:
        attr = obj.attributes[attr_name]
        result += [process_simple_attribute(attr)]

    if isinstance(obj, xmlschema.validators.XsdComplexType):
        elements = obj.content
    elif isinstance(obj, xmlschema.XsdElement):
        elements = obj
    else:
        raise TypeError(f'Wrong type {obj.__class__}')

    for element in elements:
        result += [process_complex_attribute(element)]
        if element.type.is_simple():
            continue
        if element.type.name:
            continue
        yield from process_xsd_element(element)

    yield '\n'.join(result)


def base_class() -> str:
    result = [
        f'class XmlBaseClass({ROOT_CLASS}):',
        f'    pass',
    ]
    return '\n'.join(result)


def main_wrapper() -> str:
    """Обвязка для корневого элемента «Файл»"""
    result = [
        f'class Xml({BASE_CLASS}):',
        f'    fajl: Fajl = pydantic.Field(',
        f"        alias='Файл',",
        f"        description='Файл обмена',",
        f'    )',
        f'',
        f'    @staticmethod',
        f'    def xmltodict_force_list() -> tuple:',
        f'        """Возвращает список атрибутов, которые xmltodict должен заворачивать в списки"""',
        f'        return tuple({force_list})',
    ]
    return '\n'.join(result)


if __name__ == '__main__':

    xsd = xmlschema.XMLSchema(XSD_PATH)

    print('"""\nGenerated at %s\n"""' % datetime.datetime.now(tz=pytz.utc), end='\n'*2)
    print('import pydantic')
    print('import typing')
    print('from apps import upd')
    print('\n')

    print(*map(process_simple_type, xsd.simple_types), sep='\n', end='\n'*3)

    print(base_class(), end='\n'*3)

    print(*itertools.chain.from_iterable(map(process_xsd_element, xsd.complex_types)), sep='\n'*3, end='\n'*3)

    print(*itertools.chain.from_iterable(map(process_xsd_element, xsd)), sep='\n'*3, end='\n'*3)

    print(main_wrapper())
