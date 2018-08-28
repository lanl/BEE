echo "==> Installing Prometheus"
wget "https://github.com/prometheus/prometheus/releases/download/v1.4.1/prometheus-1.4.1.linux-amd64.tar.gz"
tar -xvzf prometheus-1.4.1.linux-amd64.tar.gz
cd prometheus-1.4.1.linux-amd64/
./prometheus -version
# Might want to install node exporter
# Would start like:
# nohup ./prometheus -config.file=prometheus.yml > prometheus.log 2>&1 &
# Also, make sure to set no_proxy=localhost


