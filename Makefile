BUILDDIR=_site

html:
	jekyll build

drafts:
	jekyll build --drafts

linkcheck:
	check-links $(BUILDDIR)

clean:
	rm -fr $(BUILDDIR)/*

publish: html
	./publish.sh $(username)
