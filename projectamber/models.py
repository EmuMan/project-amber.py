from dataclasses import dataclass
from typing import Any

from projectamber.http import APIRequest
from projectamber.utils import _autogen_repr, _talent_format


class APIClient:
    
    curves: dict[str, 'Curve']
    
    def __init__(self) -> None:
        self.curves = {}
    
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

    def get_curve(self, curve_id: str) -> 'Curve':
        if len(self.curves) == 0:
            self._load_curves()
        return self.curves[curve_id]
    
    def _load_curves(self) -> None:
        endpoints = ('/avatarCurve',)
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
            description=data['description'],
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
    info: CharacterInfo | None
    ascensions: list[CharacterAscensionStep] | None
    level_stats: dict[str, CurvedValue] | None
    talents: list[CharacterTalent] | None
    constellations: list[CharacterConstellation] | None
    name_card: CharacterNameCard | None
    special_food = CharacterSpecialFood | None
    
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
        
        self.talents = [None] * 7
        for talent_index, talent_info in data['talent'].items():
            self.talents[int(talent_index)] = CharacterTalent._from_data(talent_info)
        
        self.constellations = [None] * 6
        for con_index, con_info in data['constellation'].items():
            self.constellations[int(con_index)] = CharacterConstellation._from_data(con_info)
            
        self.name_card = CharacterNameCard._from_data(data['other']['nameCard'])
        
        self.special_food = CharacterSpecialFood._from_data(data['other']['specialFood'])
    
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
