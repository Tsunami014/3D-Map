from API import planetDataPth, planetDataFile
cwd = ""
while True:
    try:
        try:
            cmd = input(f'/{cwd} > ').split(' ')
        except KeyboardInterrupt:
            break
        if cmd[0] == 'ls':
            print('\n'.join(planetDataPth(cwd)))
        elif cmd[0] == 'cat':
            print(planetDataFile(cwd+cmd[1]))
        elif cmd[0] == 'cd':
            if cmd[1] == '..':
                cwd = '/'.join(cwd.split('/')[:-1])
            else:
                if cmd[1][-1] != '/':
                    cmd[1] += '/'
                if cmd[1] in planetDataPth(cwd):
                    cwd += cmd[1]
    except IndexError:
        pass
