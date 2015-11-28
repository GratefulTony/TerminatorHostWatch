all:
	@echo "Usage: make (deb|clean)"

clean:
	rm -rf build

deb: clean
	mkdir -p build/debian 2> /dev/null || true
	cp -a README.md build/debian/
	cp -a files build/debian/files
	cp -a debian build/debian/debian
	cd build/debian; debuild -us -uc -i	

