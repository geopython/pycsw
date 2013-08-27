BUILDDIR=_site

html:
	jekyll build

linkcheck:
	check-links $(BUILDDIR)

clean:
	rm -fr $(BUILDDIR)
