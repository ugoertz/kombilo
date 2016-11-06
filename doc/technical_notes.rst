==================================
Technical Notes
==================================

Some notes around development and deploying (currently not included in the
online documentation or the pdf; it is more notes to myself).

Miscellaneous
================

Signing the installer
-----------------------

You need the certificate to sign the code with as a pfx file. Install
osslsigncode.  Build the installer exe file first. Then run::

  ./osslsigncode sign -pkcs12 ug201611.pfx -pass PASSWORD_FOR_CERTIFICATE
    -n "Kombilo" -i http://www.u-go.net/
    -t http://timestamp.verisign.com/scripts/timstamp.dll
    -in kombilo081-32.exe -out kombilo-081.exe

with password, certificate file name, infile, outfile suitably adapted.

(It would also be possible to make this part of the build process, using
encrypted environment variables on Appveyor to encrypt the certificate and
decrypt it during build, and then use signtool.exe. Since we do not release
a signed installer that often, this does not seem to make much sense, though.)
