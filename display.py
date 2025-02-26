from matplotlib import pyplot as plt
import re

__all__ = [
    'displayPlanetData'
]

def displayPlanetData(data: str, show: bool = True) -> None:
    for chunk in data.rstrip('\n')[data.index('\n')+1:-8].split('\nEND\n'):
        lines = chunk.split('\n')
        # name = lines[0]
        ps = [[float(i) for i in re.sub('[\t ]+', ' ', ln)[1:].split(' ')] for ln in lines[1:]]
        xs, ys = zip(*ps)
        plt.plot(xs, ys)
    
    if show:
        plt.show()
