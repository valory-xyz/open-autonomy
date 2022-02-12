

_obj_json = {0: "a", 1: {"00": "aa", "01": "aaa", "02": {"000": "aaa"}}}
from copy import copy

def recurse(_obj_json):
    if not any([isinstance(i, dict) for i in _obj_json.values()]):
        return _obj_json
    new_obj = {}
    for k, v in _obj_json.items():
        if isinstance(v, dict):
            for k2, v2 in v.items():
                new_obj["_".join([str(k), str(k2)])] = v2
        else:
            new_obj[k] = v
    return recurse(new_obj)


if __name__ == "__main__":
    print(recurse(_obj_json))



