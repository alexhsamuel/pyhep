#
# cint dynimic link standard library makefile
#
done: statistics.dll array.dll carray.dll fft.dll xgraph.dll lsm.dll ReadF.dll RegE.dll
	rm G__* *.o | echo 'G__* not exist'
	echo > done

statistics.dll : statistics.c ../cint
	makecint -mk Makeit -dl statistics.dll -c statistics.c -cint -Z0
	make -f Makeit

array.dll : array.c ../cint
	makecint -mk Makeit  -dl array.dll -c array.c -cint -Z0
	make -f Makeit

carray.dll : carray.c ../cint
	makecint -mk Makeit  -dl carray.dll -c carray.c -cint -Z0
	make -f Makeit

fft.dll : fft.c ../cint
	makecint -mk Makeit  -dl fft.dll -c fft.c -cint -Z0
	make -f Makeit

lsm.dll : lsm.c ../cint
	makecint -mk Makeit  -dl lsm.dll -c lsm.c -cint -Z0
	make -f Makeit

xgraph.dll : xgraph.c ../cint
	makecint -mk Makeit  -dl xgraph.dll -c xgraph.c -cint -Z0
	make -f Makeit

ReadF.dll : ReadF.h ReadF.C ../cint
	makecint -mk Makeit  -dl ReadF.dll -H ReadF.h -C++ ReadF.C -cint -Z0
	make -f Makeit

RegE.dll : RegE.h RegE.C ../cint
	makecint -mk Makeit  -dl RegE.dll -H RegE.h -C++ RegE.C -cint -Z0
	make -f Makeit

