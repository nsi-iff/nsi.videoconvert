PYTHON=python

all: install run_unit_test

install_nsimultimedia:
	@rm -Rf nsi.multimedia-0.1.2.tar.gz nsi.multimedia-0.1.2
	wget http://newton.iff.edu.br/pypi/nsi.multimedia-0.1.2.tar.gz
	tar -vzxf nsi.multimedia-0.1.2.tar.gz
	cd nsi.multimedia-0.1.2 && $(PYTHON) setup.py install
	@rm -Rf nsi.multimedia-0.1.2.tar.gz nsi.multimedia-0.1.2

install_cyclone:
	@rm -Rf cyclone
	git clone git://github.com/fiorix/cyclone.git
	cd cyclone && $(PYTHON) setup.py install
	@rm -Rf cyclone

install_restfulie:
	@rm -Rf restfulie
	git clone git://github.com/caelum/restfulie-py.git restfulie
	cd restfulie && $(PYTHON) setup.py install
	@rm -Rf restfulie

install: install_cyclone install_nsimultimedia
	$(PYTHON) setup.py develop

run_unit_test:
	cd nsivideoconvert/tests && $(PYTHON) testInterface.py && $(PYTHON) testAuth.py

