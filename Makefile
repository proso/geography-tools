SSH_CONNECTION=51bb5930500446923f000201@geography-conqueror.rhcloud.com

.PHONY: target/reports target/maps

target/download:
	mkdir -p target/download; \
	cd target/download; \
	git clone git@github.com:kartograph/kartograph.py.git; \
	cd kartograph.py; \
	python setup.py build; \
	cd ..; \
	wget http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/110m/cultural/ne_110m_admin_0_countries.zip -O geoshapes.zip; \
	mkdir geoshapes; \
	unzip geoshapes.zip -d geoshapes; \
	ssh $(SSH_CONNECTION) -t '/var/lib/openshift/51bb5930500446923f000201/app-root/runtime/repo/wsgi/openshift/manage.py dumpdata questions.answer > /tmp/data.answers.json' && \
	scp $(SSH_CONNECTION):/tmp/data.answers.json answers.json; \
	ssh $(SSH_CONNECTION) -t '/var/lib/openshift/51bb5930500446923f000201/app-root/runtime/repo/wsgi/openshift/manage.py dumpdata core.place > /tmp/data.places.json' && \
	scp $(SSH_CONNECTION):/tmp/data.places.json places.json;

target/external-libs: target/download
	mkdir -p target/external-libs; \
	cp -r target/download/kartograph.py/build/*/kartograph target/external-libs

target/data: target/download
	mkdir -p target/data; \
	python prepare-data.py; \
	for EXT in shp dbf prj shx; do \
		cp "target/download/geoshapes/ne_110m_admin_0_countries.$$EXT" "target/data/world.$$EXT"; \
	done

target/reports: target/data notebooks/* libs/geodata/*
	mkdir -p target/reports; \
	cd notebooks; for NOTEBOOK in *.ipynb; do \
		BASENAME=`basename $$NOTEBOOK .ipynb`; \
		echo "$$BASENAME"; \
		runipy $$NOTEBOOK -q --pylab --html ../target/reports/$$BASENAME.html; \
	done;\

target/maps:
	mkdir -p target/maps; \
	cd scripts; for SCRIPT in *.py; do \
		python "$$SCRIPT"; \
	done;

publish: target/reports target/maps
	ssh jpapouse@zimodej.cz -t "rm -rf /var/www/zimodej.cz/subdomeny/geodata/ && mkdir /var/www/zimodej.cz/subdomeny/geodata/ && (echo 'Options +Indexes' > /var/www/zimodej.cz/subdomeny/geodata/.htaccess)"; \
	scp target/reports/*.html jpapouse@zimodej.cz:/var/www/zimodej.cz/subdomeny/geodata;
	scp target/maps/*.svg jpapouse@zimodej.cz:/var/www/zimodej.cz/subdomeny/geodata;
