clean:
	rm /tmp/test.db || true
	rm -rf ./venv || true

install:
	./init.sh

run:
	pwd
	source `pwd`/venv/bin/activate; \
	export FLASK_APP=TSBackEnd; \
	flask run
