from   hep.cernlib import hbook
import sys

def ls(hbook_dir, indent=0):
    # Loop over directory elements in 'path'.
    for name in hbook_dir.keys():
        info = hbook_dir.getinfo(name)
        print "%s%s%s%5d  %s" % (" " * indent, name,
                                 " " * (40 - indent - len(name)),
                                 info.rz_id, info.type)
        # If it's a directory, list its contents recursively.
        if info.type == "directory":
            ls(hbook_dir[name], indent + 1)


ls(hbook.open(sys.argv[1]))
