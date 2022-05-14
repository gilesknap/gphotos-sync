# locally build a runtime container for testing

# first make sure a wheel is built
(
    cd ..
    pip install build
    rm -r dist
    python -m build --wheel
)

# make the container name the same as the root folder name of this clone
container_name=$(cd ..; basename $(realpath .))
echo building $container_name ...

# run the build with required build-args for a runtime build
ln -s ../dist .
podman build --build-arg BASE=python:3.10-slim --build-arg ENTRYPOINT=$container_name -t $container_name .. --file ./Dockerfile
unlink dist
