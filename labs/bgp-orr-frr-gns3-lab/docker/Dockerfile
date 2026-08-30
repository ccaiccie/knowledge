FROM quay.io/frrouting/frr:10.7.0

USER root
COPY --chmod=0755 orr-lab-start /usr/local/bin/orr-lab-start
COPY --chown=frr:frr --chmod=0640 vtysh.conf /etc/frr/vtysh.conf
