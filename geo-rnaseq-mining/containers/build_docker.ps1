param(
    [string]$Tag = "geo-rnaseq-mining:mvp"
)

docker build -f containers/Dockerfile -t $Tag .
