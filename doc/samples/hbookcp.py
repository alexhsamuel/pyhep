from   hep.cernlib import hbook

def copy(src_dir, dest_dir):
    # Loop over directory elements in 'path'.
    for name in src_dir.keys():
        info = src_dir.getInfo(name)
        if info.is_directory:
            # It's a directory.  Make the destination directory, and
            # call ourselves recursively to copy its contents.
            copy(src_dir[name], dest_dir.mkdir(name))
        elif info.type in ("1D histogram", "2D histogram"):
            # It's a histogram.  Load it, and save it to the destination. 
            dest_dir[name] = src_dir[name]
        # Ignore other types of entries.


if __name__ == "__main__":
    import sys
    copy(hbook.open(sys.argv[1]), hbook.create(sys.argv[2]))
