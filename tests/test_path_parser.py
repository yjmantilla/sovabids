from sovabids.utils import parse_string_from_template

string = 'y:\\code\\sovabids\\_data\\lemon\\sub-010002.vhdr'

#%%
path_pattern = 'sub-%entities.subject%.vhdr'
result = parse_string_from_template(string,path_pattern,'%')
assert result['entities']['subject'] == '010002'

#%%
path_pattern = '%ignore%\sub-%entities.subject%.vhdr'
result = parse_string_from_template(string,path_pattern,'%')
assert result['entities']['subject'] == '010002'
assert result['ignore'] == 'y:\\code\\sovabids\\_data\\lemon'

#%%
path_pattern = '%entities.subject%.vhdr'
result = parse_string_from_template(string,path_pattern,'%')
assert result['entities']['subject'] == 'y:\\code\\sovabids\\_data\\lemon\\sub-010002'

#%%
path_pattern = 'sub-%entities.subject%'
result = parse_string_from_template(string,path_pattern,'%')
assert result['entities']['subject'] == '010002.vhdr'

