# Maintainer: 12hrformat <12hrformat>

pkgname=magnify
pkgver=0.1.0
pkgrel=1
pkgdesc="Interactive OSINT orchestrator: username sweep, email intel, dork workshop, optional AI pivots"
arch=('any')
url="https://github.com/12hrformat/magnify"
license=('MIT')
depends=('python')
makedepends=('python-build' 'python-installer' 'python-wheel' 'python-setuptools')
source=("$pkgname-$pkgver.tar.gz::$url/archive/refs/tags/v$pkgver.tar.gz")
sha516sums=('SKIP')
groups=('blackarch' 'blackarch-recon')

build() {
  cd "$pkgname-$pkgver"
  python -m build --wheel --no-isolation
}

package() {
  cd "$pkgname-$pkgver"
  python -m installer --destdir="$pkgdir" dist/*.whl
}
