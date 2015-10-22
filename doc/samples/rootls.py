import hep.root

def ls(root_dir, indent=0):
    # Loop over directory elements in 'path'.
    for name in root_dir.keys():
        info = root_dir.getInfo(name)
        label = "%s (%s)" % (name, info.title)
        print (" " * indent) + label \
              + (" " * (64 - indent - len(label))) + info.class_name
        # If it's a directory, list its contents recursively.
        if info.is_directory:
            ls(root_dir[name], indent + 1)


if __name__ == "__main__":
    import sys
    file = hep.root.open(sys.argv[1])
    ls(file)
