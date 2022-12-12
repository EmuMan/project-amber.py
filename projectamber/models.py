from dataclasses import dataclass
from functools import cache
from typing import Any

from projectamber.http import APIRequest
from projectamber.utils import _autogen_repr, _talent_format, find_any


class APIClient:
    
    curves: dict[str, 'Curve']
    
    def __init__(self) -> None:
        self.curves = {}
    
    @cache
    def get_characters(self) -> list['Character']:
        request = APIRequest('GET', 'en', '/avatar')
        data = request.request()
        
        avatars_raw: dict[str, dict[str, Any]] = data['items']
        
        avatars: list[Character] = []
        
        for id, info in avatars_raw.items():
            avatars.append(Character(
                client=self,
                id=id,
                rank=info['rank'],
                name=info['name'],
                element=info['element'],
                weapon_type=info['weaponType'],
                icon=info['icon'],
                birthday=info['birthday'],
                release=info.get('release', None),
                _route=info['route']
            ))
        
        return avatars
    
    def get_character(self, *, id: str = None, name: str = None) -> 'Character':
        if id is not None:
            return find_any(self.get_characters(), lambda c: c.id == id)
    
        if name is not None:
            return find_any(self.get_characters(), lambda c: name.lower() in c.name.lower())
        
        raise TypeError('get_character() requires at least one argument: \'id\' or \'name\'')
    
    @cache
    def get_weapons(self) -> list['Weapon']:
        request = APIRequest('GET', 'en', '/weapon')
        data = request.request()
        
        weapon_types: dict[str, str] = data['types']
        weapons_raw: dict[str, dict[str, Any]] = data['items']
        
        weapons: list[Character] = []
        
        for id, info in weapons_raw.items():
            weapons.append(Weapon(
                client=self,
                id=id,
                rank=info['rank'],
                type=weapon_types[info['type']],
                name=info['name'],
                icon=info['icon'],
                _route=info['route']
            ))
        
        return weapons

    def get_weapon(self, *, id: int = None, name: str = None) -> 'Weapon':
        if id is not None:
            return find_any(self.get_weapons(), lambda w: w.id == id)
    
        if name is not None:
            return find_any(self.get_weapons(), lambda w: name.lower() in w.name.lower())
        
        raise TypeError('get_weapon() requires at least one argument: \'id\' or \'name\'')
        
    def get_curve(self, curve_id: str) -> 'Curve':
        if len(self.curves) == 0:
            self._load_curves()
        return self.curves[curve_id]
    
    def _load_curves(self) -> None:
        endpoints = ('/avatarCurve', '/weaponCurve')
        for endpoint in endpoints:
            request = APIRequest('GET', 'static', endpoint)
            data = request.request()
            counter = 0
            in_list = False
            while (cstr := str(counter)) in data or not in_list:
                if cstr in data:
                    if not in_list:
                        in_list = True
                    for name, multiplier in data[cstr]['curveInfos'].items():
                        if name not in self.curves:
                            self.curves[name] = Curve([], counter)
                        self.curves[name].values.append(multiplier) # why type checking messed up??
                counter += 1

@dataclass
class CharacterInfo:
    
    title: str
    detail: str
    constellation: str
    native: str
    cv: dict[str, str]
    
    @classmethod
    def _from_data(cls, data: dict) -> 'CharacterInfo':
        return cls(
            title=data['title'],
            detail=data['detail'],
            constellation=data['constellation'],
            native=data['native'],
            cv=data['cv']
        )

@dataclass
class Curve:
    
    values: list[float]
    start_index: int
        
    def curve_value(self, index: int, initial: float) -> float:
        # let index out of bounds propogate
        return self.values[index - self.start_index] * initial

@dataclass
class CurvedValue:
    
    initial: float
    curve: Curve
    
    def get_value(self, index: int):
        return self.curve.curve_value(index, self.initial)

@dataclass
class CharacterAscensionStep:
    
    first: bool
    step_index: int
    item_cost: dict[str, int] # TODO: Will become Material dict, or potentially new structure
    max_level: int
    stats: dict[str, float]
    required_adventure_rank: int
    coin_cost: int
    
    @classmethod
    def _from_data(cls, first: bool, data: dict) -> 'CharacterAscensionStep':
        return CharacterAscensionStep(
            first=first,
            step_index=data['promoteLevel'],
            item_cost=data.get('costItems', {}),
            max_level=data['unlockMaxLevel'],
            stats=data.get('addProps', {}),
            required_adventure_rank=data.get('requiredPlayerLevel', 0),
            coin_cost=data.get('coinCost', 0)
        )

@dataclass
class TalentPromotionStep:
    
    level: int
    item_cost: dict[str, int]
    coin_cost: int
    _description_format: list[str]
    parameters: list[float]
    
    @property
    def description(self) -> list[str]:
        return [_talent_format(line, self.parameters) for line in self._description_format if line != '']
    
    @classmethod
    def _from_data(cls, data: dict) -> 'TalentPromotionStep':
        return cls(
            level=data['level'],
            item_cost=data['costItems'] or {},
            coin_cost=data['coinCost'] or {},
            _description_format=data['description'],
            parameters=data['params']
        )

@dataclass
class CharacterTalent:

    _type: int
    name: str
    description: str
    icon: str
    promotions: dict[str, TalentPromotionStep] | None
    cooldown: int | None
    energy_cost: int | None
    
    @classmethod
    def _from_data(cls, data: dict) -> 'CharacterTalent':
        _type: int = data['type']
        
        return cls(
            _type=_type,
            name=data['name'],
            description=data['description'].replace('\\n', '\n'),
            icon=data['icon'],
            promotions=None if _type == 2 else \
                {promo_index: TalentPromotionStep._from_data(promo_entry) \
                    for promo_index, promo_entry in data['promote'].items()},
            cooldown=None if _type == 2 else data['cooldown'],
            energy_cost=None if _type == 2 else data['cost'],
        )

@dataclass
class CharacterConstellation:
    
    name: str
    description: str
    icon: str
    
    @classmethod
    def _from_data(cls, data: dict) -> 'CharacterConstellation':
        return cls(
            name=data['name'],
            description=data['description'],
            icon=data['icon'],
        )
        
@dataclass
class CharacterNameCard:
    
    id: int
    name: str
    description: str
    icon: str
    
    @classmethod
    def _from_data(cls, data: dict) -> 'CharacterNameCard':
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            icon=data['icon'],
        )


@dataclass
class CharacterSpecialFood:
    
    id: int
    name: str
    rank: int
    effect_icon: str
    icon: str
    
    @classmethod
    def _from_data(cls, data: dict) -> 'CharacterSpecialFood':
        return cls(
            id=data['id'],
            name=data['name'],
            rank=data['rank'],
            effect_icon=data['effectIcon'],
            icon=data['icon'],
        )

class Character:
    
    # always present
    client: APIClient
    id: str
    rank: int
    name: str
    element: str
    weapon_type: str
    icon: str
    birthday: tuple[int, int]
    release: int | None
    _route: str
    
    lazy: bool
    
    # require load
    info: CharacterInfo
    ascensions: list[CharacterAscensionStep]
    level_stats: dict[str, CurvedValue]
    talents: dict[str, CharacterTalent]
    constellations: list[CharacterConstellation]
    name_card: CharacterNameCard | None
    special_food = CharacterSpecialFood | None
    
    @property
    def talent_normal(self) -> CharacterTalent:
        return find_any(self.talents.values(), lambda t: t.icon.startswith('Skill_A'))
    
    @property
    def talent_skill(self) -> CharacterTalent:
        return find_any(self.talents.values(), lambda t: \
            t.icon.startswith('Skill_S') and t.icon.endswith('01'))
    
    @property
    def talent_alternate_dash(self) -> CharacterTalent | None:
        return find_any(self.talents.values(), lambda t: \
            t.icon.startswith('Skill_S') and t.icon.endswith('02'))
    
    @property
    def talent_burst(self) -> CharacterTalent:
        return find_any(self.talents.values(), lambda t: t._type == 1)
    
    @property
    def talent_passives(self) -> list[CharacterTalent]:
        return [talent for talent in self.talents.values() if talent._type == 2]
    
    def __init__(self, client: APIClient, id: str, rank: int, name: str, element: str, weapon_type: str,
                 icon: str, birthday: tuple[int, int], release: int | None, _route: str) -> None:
        self.client = client
        self.id = id
        self.rank = rank
        self.name = name
        self.element = element
        self.weapon_type = weapon_type
        self.icon = icon
        self.birthday = birthday
        self.release = release
        self._route = _route
        
        self.lazy = True
        
    def __str__(self):
        return f'Avatar({self.id}, {self.name})'
    
    def __repr__(self):
        return _autogen_repr(self)
    
    def fetch(self) -> 'Character':
        request = APIRequest('GET', 'en', f'/avatar/{self.id}')
        data = request.request()
        self._load_data(data)
        self.lazy = False
        return self
    
    def _load_data(self, data: dict):
        self.info = CharacterInfo._from_data(data['fetter'])
        
        self.ascensions = []
        for i, step in enumerate(data['upgrade']['promote']):
            self.ascensions.append(CharacterAscensionStep._from_data(i == 0, step))
            
        self.level_stats = {}
        for stat in data['upgrade']['prop']:
            curve = self.client.get_curve(stat['type'])
            self.level_stats[stat['propType']] = CurvedValue(stat['initValue'], curve)
        
        self.talents = {}
        for talent_index, talent_info in data['talent'].items():
            self.talents[talent_index] = CharacterTalent._from_data(talent_info)
        
        self.constellations = [None] * 6
        for con_index, con_info in data['constellation'].items():
            self.constellations[int(con_index)] = CharacterConstellation._from_data(con_info)
        
        if data['other'] is None:
            self.name_card = self.special_food = None
        else:
            self.name_card = CharacterNameCard._from_data(data['other']['nameCard']) # traveller
            
            self.special_food = None if data['other']['specialFood'] is None else \
                CharacterSpecialFood._from_data(data['other']['specialFood']) # raiden kekw
    
    def get_base_stat(self, stat_id: str, level: int, ascension: int) -> float:
        return self.level_stats[stat_id].get_value(level) + \
            self.ascensions[ascension].stats.get(stat_id, 0)
    
    def get_hp(self, level: int, ascension: int) -> float:
        return self.get_base_stat('FIGHT_PROP_BASE_HP', level, ascension)

    def get_attack(self, level: int, ascension: int) -> float:
        return self.get_base_stat('FIGHT_PROP_BASE_ATTACK', level, ascension)
    
    def get_defense(self, level: int, ascension: int) -> float:
        return self.get_base_stat('FIGHT_PROP_BASE_DEFENSE', level, ascension)

    def get_extra_stats(self, ascension: int) -> list[tuple[str, int]]:
        return [(name, value) for name, value in self.ascensions[ascension].stats.items() \
            if not name.startswith('FIGHT_PROP_BASE_')]
        

@dataclass
class WeaponAffix:
    
    id: int
    name: str
    descriptions: list[str]
    
    @classmethod
    def _from_data(cls, id: str, data: dict) -> 'WeaponAffix':
        descriptions = [None] * 5
        for index, description in data['upgrade'].items():
            descriptions[int(index)] = description
        return cls(
            id=int(id),
            name=data['name'],
            descriptions=descriptions,
        )

@dataclass
class WeaponAscensionStep:
    
    first: bool
    step_index: int
    item_cost: dict[str, int] # TODO: Will become Material dict, or potentially new structure
    coin_cost: int
    stats: dict[str, float]
    max_level: int
    required_adventure_rank: int
    
    @classmethod
    def _from_data(cls, first: bool, data: dict) -> 'WeaponAscensionStep':
        return CharacterAscensionStep(
            first=first,
            step_index=data['promoteLevel'],
            item_cost=data.get('costItems', {}),
            coin_cost=data.get('coinCost', 0),
            stats=data.get('addProps', {}),
            max_level=data['unlockMaxLevel'],
            required_adventure_rank=data.get('requiredPlayerLevel', 0),
        )

class Weapon:
    
    # always present
    client: APIClient
    id: int
    rank: int
    type: str
    name: str
    icon: str
    _route: str
    
    # require load
    description: str
    story_id: int
    affix: dict[str, WeaponAffix]
    refinement_costs: list[int]
    level_stats: dict[str, CurvedValue]
    ascensions: list[WeaponAscensionStep]
    
    lazy: bool
    
    def __init__(self, client: APIClient, id: int, rank: int, type: str, name: str, icon: str, _route: str):
        self.client = client
        self.id = id
        self.rank = rank
        self.type = type
        self.name = name
        self.icon = icon
        self._route = _route

    def fetch(self) -> 'Weapon':
        request = APIRequest('GET', 'en', f'/weapon/{self.id}')
        data = request.request()
        self._load_data(data)
        self.lazy = False
        return self
    
    def _load_data(self, data: dict):
        self.description = data['description']
        self.story_id = data['storyId']
        
        self.affix = {} if data['affix'] is None else \
            {affix_id: WeaponAffix._from_data(affix_id, affix_data) \
            for affix_id, affix_data in data['affix'].items()}
        
        self.refinement_costs = data['upgrade']['awakenCost']
        
        self.level_stats = {}
        for stat in data['upgrade']['prop']:
            if 'propType' not in stat: continue
            curve = self.client.get_curve(stat['type'])
            self.level_stats[stat['propType']] = CurvedValue(stat['initValue'], curve)
        
        self.ascensions = []
        for i, step in enumerate(data['upgrade']['promote']):
            self.ascensions.append(WeaponAscensionStep._from_data(i == 0, step))

    def get_base_attack(self, level: int, ascension: int) -> float:
        return self.level_stats['FIGHT_PROP_BASE_ATTACK'].get_value(level) + \
            self.ascensions[ascension].stats['FIGHT_PROP_BASE_ATTACK']
    
    def get_substat(self, level: int, ascension: int) -> tuple[str, CurvedValue] | tuple[None, None]:
        for stat_name, stat_curve in self.level_stats.items():
            if not stat_name.startswith('FIGHT_PROP_BASE_'):
                return (stat_name, stat_curve.get_value(level) + \
                    self.ascensions[ascension].stats.get(stat_name, 0.0))
        return (None, None)
