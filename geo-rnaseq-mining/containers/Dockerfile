FROM mambaorg/micromamba:1.5.10

LABEL org.opencontainers.image.title="geo-rnaseq-mining"
LABEL org.opencontainers.image.description="Static MVP container definition for workflow tests"

COPY workflow/envs/base.yaml /tmp/base.yaml
RUN micromamba install -y -n base -f /tmp/base.yaml && micromamba clean --all --yes

WORKDIR /workspace
