from API import planetDataPth, planetDataFile
from display import displayPlanetData
from matplotlib import pyplot as plt
cwd = ""
def displayAll(cwd):
    for i in planetDataPth(cwd):
        if i[-1] == '/':
            displayAll(cwd+i)
        else:
            displayPlanetData(planetDataFile(cwd+i), False)

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
        elif cmd[0] == 'disp':
            if cmd[1] == 'all':
                displayAll(cwd)
                plt.show()
            else:
                displayPlanetData(planetDataFile(cwd+cmd[1]))
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
