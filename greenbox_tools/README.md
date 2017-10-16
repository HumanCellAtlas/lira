# Installable Python package providing all listener functions of Green-Box

## APIs


## To-DOs
- [x] Cover all functions of existing green-box functions
- [x] Replace the gsutil with gogle-cloud-storage Python API to get files from GCS
- [x] Refactor the authentication process of google storage client into a separate class
- [ ] Add elaborate docs to package readme.rst
- [ ] Modify kubernetes scripts and reduce the length of call-chain of listener
- [ ] Add CLI command entry_points to setup.py
- [ ] Extract docs with Sphinx

## Potential Problems

- Dockerfile may be conflicted to the Dockerfile of secondary-analysis
- `RUN pip install` in Dockerfile is conflictet with the required packages in setup.py
- Unit Tests are not covering all the usecases
- Haven't test with Kubernetes, especially no failure test for authentication with GCS using gcs python API

Because of above problems and potential problems, this package is not currently able to fully replace the existing green_box api.