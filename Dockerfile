FROM archlinux/base

COPY setup.py /
ADD setup.cfg /
ADD botrytis/ /botrytis
ADD static/ /static

EXPOSE 8080

ENV BUILD_DEPS="upx yarn tar"
ENV DEPS="python python-setuptools python-biopython python-cherrypy python-jinja"

RUN pacman --noconfirm -Syu \
 && pacman --noconfirm -S $BUILD_DEPS $DEPS \
 && curl -SsL "http://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/ncbi-blast-2.8.1+-x64-linux.tar.gz" \
  | tar xzv --wildcards '*/bin/makeblastdb' --wildcards '*/bin/blast?' --strip-components=1 | tee binaries.txt \
 && upx $(cut binaries.txt -d/ -f2,3) \
 && python setup.py build_js \
 && pacman --noconfirm -R $BUILD_DEPS \
 && while pacman -Qtdq; do pacman --noconfirm -R $(pacman -Qtdq); done \
 && rm -rf /var/cache/pacman/pkg/ /tmp/* \
 && rm -rf /usr/share/.cache /usr/lib/python3.7/test /usr/share/doc

CMD python setup.py run --host 0.0.0.0 --port 80
