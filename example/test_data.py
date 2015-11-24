try:
    from toto.data_access import get_data_dir, ls
except ImportError:
    print("try namespace")
    from oa.toto.data_access import get_data_dir, ls

print("data dir", get_data_dir())
print(ls("."))