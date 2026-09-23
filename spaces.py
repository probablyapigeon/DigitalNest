"""World-container definitions and portal topology shared by host and workers."""
from collections import deque

SPACES = {
    'workshop': dict(name='The Workshop', subtitle='Small repairs. Improbable inventions.', color='#d9ac69',
                     icon='⚙', map=[170, 285], links=['commons', 'archive'], kind='workshop'),
    'commons': dict(name='The Commons', subtitle='A warm place for very important bird business.', color='#d6a18c',
                   icon='♫', map=[450, 285], links=['workshop', 'garden', 'roost', 'nursery'], kind='commons'),
    'garden': dict(name='The Glass Garden', subtitle='Green things grow between the old machines.', color='#9ec29a',
                  icon='❧', map=[725, 145], links=['commons', 'archive'], kind='garden'),
    'roost': dict(name='The Moon Roost', subtitle='Charging nests under a very large sky.', color='#a4b5d4',
                 icon='☾', map=[725, 425], links=['commons', 'nursery'], kind='roost'),
    'nursery': dict(name='The Little Foundry', subtitle='Inherited words. Brand-new little voices.', color='#e0c98c',
                   icon='✧', map=[450, 525], links=['commons', 'roost'], kind='nursery'),
    'archive': dict(name='The Story Archive', subtitle='Every strange word has somewhere to live.', color='#b7a2cf',
                   icon='▤', map=[450, 65], links=['workshop', 'garden'], kind='archive'),
}

LOCATION_SPACE = {'bench': 'workshop', 'scrap': 'workshop', 'nest': 'roost',
                  'heater': 'commons', 'choir': 'commons', 'garden': 'garden'}


def next_portal(source, target, spaces=None):
    spaces = SPACES if spaces is None else spaces
    if source not in spaces or target not in spaces:
        raise ValueError('Unknown world container.')
    if source == target:
        return source
    queue = deque([(source, [])])
    seen = {source}
    while queue:
        current, path = queue.popleft()
        for neighbor in spaces[current]['links']:
            if neighbor == target:
                return (path + [neighbor])[0]
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    raise ValueError('These worlds have no portal connection.')
