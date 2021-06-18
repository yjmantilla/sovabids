from typing import Pattern
from sovabids.utils import parse_string_from_template

string = 'Y:\code\sovabids\_data\lemon2\sub-010004\ses-001\sub-010004.vhdr'
path_pattern = 'ses-%entities.task%\s%ignore%-%entities.subject%.vhdr'
result = parse_string_from_template(string,path_pattern,'%')
assert result['entities']['task']=='001'
assert result['entities']['subject']=='010004'
assert result['ignore']=='ub'

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

