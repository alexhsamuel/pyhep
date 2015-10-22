#!/bin/bash

version=$1
cvstag=version-$(echo ${version} | sed -e 's#\.#-#g')

if [ ! -f version ]; then
    echo "cannot find 'version'" >2
    exit 1
fi

if [ $(cat version) != ${version} ]; then
    echo "updating version number to ${version}"
    echo ${version} > version
    cvs commit -m "Update version number to ${version}." version

    echo "reconfiguring to regenerate pyhep.spec"
    ./config.status --recheck
    ./config.status

    echo "tagging ${cvstag}"
    cvs tag ${cvstag}
fi

pyhepdir=$(pwd)

cd /tmp
rm -rf pyhep
echo "exporting source"
cvs -d cvs.indetermi.net:/cvs export -r ${cvstag} pyhep
echo "installing spec file"
cp ${pyhepdir}/pyhep.spec pyhep/
mv pyhep pyhep-${version}

echo "making tarball"
tar zcvf pyhep-${version}.tgz pyhep-${version}

rm -rf pyhep-${version}
chmod a+r $(pwd)/pyhep-${version}.tgz
ls -l $(pwd)/pyhep-${version}.tgz
