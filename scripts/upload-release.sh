#!/bin/bash

version=$1
release=$2

upload_host=www.indetermi.net
upload_path=/var/www/indetermi.net/html/pyhep/dl
rpm_path=/usr/src/redhat

echo "Making HTML doc tarball..."
html_doc_tarball=/tmp/pyhep-htmldocs-$version.tgz
mkdir /tmp/pyhep-htmldocs-$version
cp -r /usr/share/doc/pyhep-$version/html/* /tmp/pyhep-htmldocs-$version/
tar zcf $html_doc_tarball -C /tmp pyhep-htmldocs-$version

echo "Making directory..."
ssh $upload_host mkdir -p $upload_path/$version || exit 1

echo "Collecting files..."
files="$rpm_path/RPMS/i386/pyhep-$version-$release.i386.rpm
       $rpm_path/SRPMS/pyhep-$version-$release.src.rpm
       $rpm_path/SOURCES/pyhep-$version.tgz
       /usr/share/doc/pyhep-$version/pyhep-$version.pdf
       $html_doc_tarball"
ls -o $files || exit 1

echo "Uploading files..."
scp -r $files $upload_host:$upload_path/$version/

echo "Expanding HTML docs..."
ssh $upload_host \
  "cd $upload_path/$version; tar zxf pyhep-htmldocs-$version.tgz"

echo "Setting permissions..."
ssh $upload_host \
  "cd $upload_path/$version; chmod -R a+r *; chmod a+x \`find . -type d\`"

echo "Cleaning up..."
rm $html_doc_tarball
rm -rf /tmp/pyhep-htmldocs-$version

echo "Generating HTML fragment..."

cat <<EOF

   <tr>
    <td><b>${version}</b></td>
    <td><a href="${version}/pyhep-${version}.tgz">tarball</a></td>
    <td>
     <a href="${version}/pyhep-${version}-${release}.src.rpm">SRPM</a> |
       <a href="${version}/pyhep-${version}-${release}.i386.rpm">i386</a></td>
       <td>
     <a href="${version}/pyhep-${version}.pdf">PDF</a> |
     <a href="${version}/pyhep-htmldocs-${version}.tgz">HTML tarball</a> |
     <a href="${version}/pyhep-htmldocs-${version}">browseable HTML</a>
    </td>
   </tr>
   <tr>
    <td colspan="4">
     Minor bug-fix release.
    </td>
   </tr>
   <tr>
    <td colspan="4">&nbsp;</td>
   </tr>

EOF

