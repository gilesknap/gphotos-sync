# locally build a runtime container for testing

THIS_DIR=$(dirname $(realpath $0))
PYTHON_ROOT=$(realpath $THIS_DIR/..)

# first make sure a wheel is built
(
    cd ${PYTHON_ROOT}
    pip install build
    rm -r dist
    python -m build --wheel
)

# make the container name the same as the root folder name of this clone
container_name=$(cd ${PYTHON_ROOT} ; basename $(realpath .))
echo building $container_name ...

# run the build with required build-args for a runtime build
cd ${THIS_DIR}
ln -s ../dist .
docker build --build-arg BASE=python:3.12-slim -t $container_name .. --file ./Dockerfile
unlink dist
