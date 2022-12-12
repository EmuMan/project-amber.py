from projectamber.models import APIClient, WeaponAffix

def main():
    client = APIClient()

    character = client.get_character(name='amber')
    character.fetch()
    print(f'{character.name} ({character.info.title}) - {character.info.detail}\n')
    print(f'\tAttack: {character.get_attack(90, 6)}')
    print(f'\tDefense: {character.get_defense(90, 6)}')
    print(f'\tHP: {character.get_hp(90, 6)}\n')
    print(f'NA Talent lvl 10 description:\n')
    na_talent = character.talent_normal
    print(na_talent.description, end='\n\n')
    print('\n'.join(f'\t{line}' for line in na_talent.promotions['10'].description))
    print()
    
    weapon = client.get_weapon(name='skyward harp')
    weapon.fetch()
    weapon_level = 70 if weapon.rank < 3 else 90
    weapon_ascension = 4 if weapon.rank < 3 else 6
    print(f'{weapon.name}: {weapon.rank}* {weapon.type}')
    print(f'\tBase Attack: {weapon.get_base_attack(weapon_level, weapon_ascension)}')
    substat_name, substat_value = weapon.get_substat(weapon_level, weapon_ascension)
    if substat_name != None:
        print(f'\tSubstat: {substat_name} - {substat_value:.1%}')
    if len(weapon.affix) != 0:
        primary_affix = list(weapon.affix.values())[0]
        print(f'\tRefinement 1: {primary_affix.descriptions[0]}')

if __name__ == '__main__':
    main()
