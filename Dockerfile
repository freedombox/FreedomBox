FROM debian:sid
RUN apt-get update
# Ignore recommended packages for latex, so the big
# documentation packages aren't installed.
RUN apt-get install --no-install-recommends -y dblatex
RUN apt-get install -y \
    apache2 \
    libapache2-mod-gnutls \
    ntp \
    privoxy \
    mumble-server \
    ejabberd \
    transmission-daemon \
    avahi-daemon \
    augeas-tools \
    debhelper \
    dh-buildinfo \
    ldapscripts \
    libjs-jquery \
    libjs-modernizr \
    libjs-bootstrap \
    make \
    gcc \
    network-manager \
    nodejs \
    npm \
    libjs-ejs \
    node-ejs \
    node-redis \
    ppp \
    pppoe \
    python3 \
    python3-dev \
    python3-venv \
    python3-augeas \
    python3-bootstrapform \
    python3-cherrypy3 \
    python3-coverage \
    python3-django \
    python3-django-stronghold \
    python3-gi \
    python3-psutil \
    python3-setuptools \
    python3-yaml \
    gir1.2-glib-2.0 \
    gir1.2-networkmanager-1.0 \
    gir1.2-packagekitglib-1.0 \
    wget \
    xmlto
ENV PYTHONUNBUFFERED 1

# Install node-restore
RUN wget https://github.com/peacekeeper/debian-node-restore/archive/debian.tar.gz
RUN tar xzf debian.tar.gz
WORKDIR debian-node-restore-debian
RUN dpkg-buildpackage -rfakeroot -uc -b
RUN dpkg -i ../node-restore_*.deb
RUN service node-restore restart
WORKDIR ..

RUN mkdir -p /plinth
RUN mkdir -p /usr/share/plinth
COPY actions /usr/share/plinth/
COPY requirements.txt /plinth/
RUN pyvenv /plinth/ve
WORKDIR /plinth
COPY . /plinth
RUN /plinth/ve/bin/pip install -r /plinth/requirements.txt
RUN /plinth/ve/bin/python setup.py install
RUN a2enmod proxy
RUN a2enmod proxy_http
RUN a2enmod rewrite
RUN a2enmod headers
RUN a2enmod gnutls
RUN a2ensite default-tls
RUN a2ensite plinth
RUN a2ensite plinth-ssl
RUN service apache2 restart
EXPOSE 443
ADD docker-run.sh /run.sh
CMD ["/run.sh"]
