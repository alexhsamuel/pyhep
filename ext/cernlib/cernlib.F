c     ------------------------------------------------------------------
c
c     cernlib.F
c
c     Copyright 2003 by Alex Samuel.  All rights reserved.
c
c     ------------------------------------------------------------------

c     Utilities for CERNLIB support.

c     ------------------------------------------------------------------

      SUBROUTINE hbook_init

      IMPLICIT NONE
      INTEGER PAWC_SIZE
      PARAMETER (PAWC_SIZE = 1000000)
      INTEGER p
      COMMON /PAWC/ p(PAWC_SIZE)

      CALL hlimit(PAWC_SIZE)
      RETURN

      END SUBROUTINE

c     ------------------------------------------------------------------

      SUBROUTINE open_lun(lun, path, status)

      IMPLICIT NONE
      INTEGER lun
      INTEGER status
      CHARACTER*1024 path

      open(unit=lun, file=path, access='SEQUENTIAL', iostat=status)
      RETURN

      END SUBROUTINE

c     ------------------------------------------------------------------

      SUBROUTINE close_lun(lun)

      IMPLICIT NONE
      INTEGER lun

      close(lun)
      RETURN

      END SUBROUTINE

c     ------------------------------------------------------------------

      SUBROUTINE hfnoent(idd, numb)

      IMPLICIT NONE
      INTEGER idd, numb

#include "hbook.inc"

      INTEGER i4
      INTEGER jbit

      CALL hfind(idd, 'HNOENT')
      IF (IQUEST(1) .EQ. 0) THEN
         i4 = jbit(IQ(LCID + KBITS), 4)
         IF (i4 .NE. 0) THEN
            IQ(LCID + 3) = numb
         ELSE
            IQ(LCONT + KNOENT) = numb
         ENDIF
      ENDIF

      END SUBROUTINE
      
