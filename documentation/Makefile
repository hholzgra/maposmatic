stylesheet = rocket-panda.css
styledir   = /usr/local/share/asciidoctor/stylesheets
remote     = h4:/home/maposmatic/maposmatic/www/static/documentation

all: html pdf
	@echo "<html>" > index.html
	@echo "  <head><title>MapOSMatic documentation</title></head>" >> index.html
	@echo "  <body>" >> index.html
	@echo "    <ul>" >> index.html
	@echo "      <li>README: <a href='README.html'>HTML</a> <a href='README.pdf'>PDF</a></li>" >> index.html
	@echo "      <li>INSTALL: <a href='INSTALL.html'>HTML</a> <a href='INSTALL.pdf'>PDF</a></li>" >> index.html
	@echo "      <li>MapOSMatic User Guide: <a href='user-guide.html'>HTML</a> <a href='user-guige.pdf'>PDF</a></li>" >> index.html
	@echo "      <li>MapOSMatic API Reference: <a href='api-docs.html'>HTML</a> <a href='api-docs.pdf'>PDF</a></li>" >> index.html
	@echo "    </ul>" >> index.html
	@echo "  </body>" >> index.html
	@echo "</html>" >> index.html

html: api-docs.html user-guide.html README.html INSTALL.html
pdf: api-docs.pdf user-guide.pdf README.pdf INSTALL.pdf

%.html: %.adoc
	asciidoctor $<

%.pdf: %.adoc 
	asciidoctor-pdf $<

%.html: ../%.md
	pandoc $< -o $@

%.pdf: ../%.md
	pandoc $< -t html5 -o $@

clean:
	rm -f *.html *.pdf *~

install: html
	cp *.html ../www/maposmatic/templates/generated

.PHONY = html clean all install
