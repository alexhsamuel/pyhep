
def listdir(domain, path=""):
    result = []
    for name in domain.listdir(path):
        sub_path = domain.join(path, name)
        result.append(sub_path)
        if domain.isdir(sub_path):
            result += listdir(domain, sub_path)
    return result


def printdir(domain, path="", indent=0):
    for name in domain.listdir(path):
        sub_path = domain.join(path, name)
        print "%s%s" % (indent * " ", name)
        if domain.isdir(sub_path):
            printdir(domain, sub_path, indent + 2)


