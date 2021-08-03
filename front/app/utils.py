import yaml

def level_key(data, parent, level=0, stored=[]):
    if isinstance(data, dict):
        level+=1
        # print(f'{data} is dict, level: {level}')
        for key in data.keys():
            if isinstance(data[key], dict):
                
                #print(f'{data[key]} is dict')
                stored = level_key(data[key], parent=key, level=level)
            else: 
                datos = {'name': key, 'value': data[key], 'level': level, 'parent': parent}
                stored.append(datos)
        return stored
    return stored
    

# file = open('rules.yaml')
# data = yaml.load(file, Loader=yaml.FullLoader)
# stored = []
# for key in data.keys():
#     if isinstance(data[key], dict):
#         stored = level_key(data[key], parent=key, stored=stored)
# print(stored)

def create_file():
    for i in range(20):
        file = open(f'./media/{i}.txt', 'w')
        file.close()

create_file()

    
