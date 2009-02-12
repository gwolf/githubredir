If Hpricot refuses to run, probably it is because it's not locally
installed - But don't worry, it is all here, in lib/. We are currently
shipping both 32-bit (i386) and 64-bit (AMD64) versions. If you have a
different architecture, or if this does not work for you, just install
it locally in your system.

You just have to create a link from the right binary to what Ruby
expects. This means, on i386 systems:

ln -s hpricot_scan.so.32bit hpricot_scan.so

And on AMD64:

ln -s hpricot_scan.so.64bit hpricot_scan.so

And don't worry, SVN will ignore hpricot_scan.so.
