ARG BUILD_FROM=ghcr.io/hassio-addons/base:16.3.2
# hadolint ignore=DL3006
FROM ${BUILD_FROM}

# Environment variables
ENV \
    PATH="/usr/local/bin:$PATH" \
    GPG_KEY="7169605F62C751356D054A26A821E680E5FA6305"

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install base system
ARG PYTHON_VERSION="v3.12.7"
ARG PYTHON_PIP_VERSION="24.2"
ARG PYTHON_SETUPTOOLS_VERSION="75.1.0"
# hadolint ignore=DL3003,DL4006,SC2155
RUN \
    apk add --no-cache --virtual .build-dependencies \
        bzip2-dev=1.0.8-r6 \
        dpkg-dev=1.22.6-r1 \
        dpkg=1.22.6-r1 \
        expat-dev=2.6.3-r0 \
        findutils=4.9.0-r5 \
        gcc=13.2.1_git20240309-r0 \
        gdbm-dev=1.23-r1 \
        gnupg=2.4.5-r0 \
        libffi-dev=3.4.6-r0 \
        libnsl-dev=2.0.1-r0 \
        libtirpc-dev=1.3.4-r0 \
        linux-headers=6.6-r0 \
        make=4.4.1-r2 \
        musl-dev=1.2.5-r0 \
        ncurses-dev=6.4_p20240420-r1 \
        openssl-dev=3.3.2-r0 \
        pax-utils=1.3.7-r2 \
        readline-dev=8.2.10-r0 \
        sqlite-dev=3.45.3-r1 \
        tar=1.35-r2 \
        tcl-dev=8.6.14-r1 \
        tk-dev=8.6.14-r0 \
        tk=8.6.14-r0 \
        util-linux-dev=2.40.1-r1 \
        xz-dev=5.6.2-r0 \
        xz=5.6.2-r0 \
        zlib-dev=1.3.1-r1 \
    \
    && curl -J -L -o /tmp/python.tar.xz \
        "https://www.python.org/ftp/python/${PYTHON_VERSION#v}/Python-${PYTHON_VERSION#v}.tar.xz" \
    && curl -J -L -o /tmp/python.tar.xz.asc \
        "https://www.python.org/ftp/python/${PYTHON_VERSION#v}/Python-${PYTHON_VERSION#v}.tar.xz.asc" \
    \
    && export GNUPGHOME="$(mktemp -d)" \
    && gpg \
        --batch \
        --keyserver hkps://keys.openpgp.org \
        --recv-keys "$GPG_KEY" \
    && gpg \
        --batch \
        --verify /tmp/python.tar.xz.asc /tmp/python.tar.xz \
    && { command -v gpgconf > /dev/null && gpgconf --kill all || :; } \
    \
    && mkdir -p /usr/src/python \
    && tar -xJC /usr/src/python --strip-components=1 -f /tmp/python.tar.xz \
    && cd /usr/src/python \
    \
    && gnuArch="$(dpkg-architecture --query DEB_BUILD_GNU_TYPE)" \
    && ./configure \
        --build="$gnuArch" \
        --enable-loadable-sqlite-extensions \
        --enable-optimizations \
        --enable-option-checking=fatal \
        --enable-shared \
        --with-lto \
        --with-system-expat \
        --without-ensurepip \
    \
    && make -j "$(nproc)" \
        EXTRA_CFLAGS="-DTHREAD_STACK_SIZE=0x100000" \
        LDFLAGS="-Wl,--strip-all" \
    && make install \
    \
    && find /usr/local \
        -type f \
        -executable \
        -not \( -name '*tkinter*' \) \
        -exec scanelf \
        --needed \
        --nobanner \
        --format '%n#p' '{}' ';' \
            | tr ',' '\n' \
            | sort -u \
            | awk 'system("[ -e /usr/local/lib/" $1 " ]") == 0 { next } { print "so:" $1 }' \
            | xargs -rt apk add --no-cache --virtual .python-rundeps \
    \
    && cd /usr/local/bin \
    && ln -s idle3 idle \
    && ln -s pydoc3 pydoc \
    && ln -s python3 python \
    && ln -s python3-config python-config \
    \
    && curl -J -L -o /tmp/get-pip.py \
        'https://bootstrap.pypa.io/get-pip.py' \
    \
    && python /tmp/get-pip.py \
        --disable-pip-version-check \
        --no-cache-dir \
        --no-compile \
        "pip==$PYTHON_PIP_VERSION" \
        "setuptools==$PYTHON_SETUPTOOLS_VERSION" \
    \
    && apk del --no-cache --purge .build-dependencies \
    && rm -f -r \
        /usr/src \
        "$GNUPGHOME" \
        /tmp/* \
    \
    && python3 --version \
    && pip3 --version \
    \
    && find /usr -depth \
        \( \
            \( -type d -a \( -name test -o -name tests -o -name idle_test \) \) \
            -o \
            \( -type f -a \( -name '*.pyc' -o -name '*.pyo' -o -name 'libpython*.a' \) \) \
        \) -exec rm -rf '{}' +

# Entrypoint & CMD
ENTRYPOINT ["/init"]

# Build arugments
ARG BUILD_DATE
ARG BUILD_REF
ARG BUILD_VERSION
ARG BUILD_REPOSITORY

# Labels
LABEL \
    io.hass.name="Addon Python base for ${BUILD_ARCH}" \
    io.hass.description="Home Assistant Community Add-on: ${BUILD_ARCH} Python base image" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="base" \
    io.hass.version=${BUILD_VERSION} \
    maintainer="Franck Nijhof <frenck@addons.community>" \
    org.opencontainers.image.title="Addon Python base for ${BUILD_ARCH}" \
    org.opencontainers.image.description="Home Assistant Community Add-on: ${BUILD_ARCH} Python base image" \
    org.opencontainers.image.vendor="Home Assistant Community Add-ons" \
    org.opencontainers.image.authors="Franck Nijhof <frenck@addons.community>" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.url="https://addons.community" \
    org.opencontainers.image.source="https://github.com/${BUILD_REPOSITORY}" \
    org.opencontainers.image.documentation="https://github.com/${BUILD_REPOSITORY}/blob/master/README.md" \
    org.opencontainers.image.created=${BUILD_DATE} \
    org.opencontainers.image.revision=${BUILD_REF} \
    org.opencontainers.image.version=${BUILD_VERSION}

# Set environment variables
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Set working directory
# WORKDIR /app

ENV NODE_ENV=production

# Expose port 5000
EXPOSE 5000/tcp

# Copy the workout data script
# COPY workout_data.py /

# Copy the startup script
COPY run.sh /

# Make the run.sh script executable
# RUN chmod +x /run.sh
RUN chmod a+x /run.sh
# Start the Flask server
CMD ["/run.sh"]
