.PHONY: all clean build

all: build

build:
	@./build.sh

clean:
	@rm -rf book
