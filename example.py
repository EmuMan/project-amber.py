from projectamber.models import APIClient

def main():
    client = APIClient()

    character = client.get_character(name='raiden')
    character.fetch()
    print(f'{character.name} ({character.info.title}) - {character.info.detail}\n')
    print(f'\tAttack: {character.get_attack(90, 6)}')
    print(f'\tDefense: {character.get_defense(90, 6)}')
    print(f'\tHP: {character.get_hp(90, 6)}\n')
    print(f'NA Talent lvl 10 description:\n')
    na_talent = character.talent_normal
    print(na_talent.description, end='\n\n')
    print('\n'.join(f'\t{line}' for line in na_talent.promotions['10'].description))

if __name__ == '__main__':
    main()
