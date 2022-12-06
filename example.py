from projectamber.models import APIClient

def main():
    client = APIClient()
    character = client.get_characters()[0]
    character.fetch()
    print(f'{character.name} ({character.info.title}) - {character.info.detail}')
    print(f'\tAttack: {character.get_attack(90, 6)}')
    print(f'\tDefense: {character.get_defense(90, 6)}')
    print(f'\tHP: {character.get_hp(90, 6)}')

if __name__ == '__main__':
    main()
