class Cubby < Formula
  include Language::Python::Virtualenv

  desc "Encrypted, namespaced secret store for AI coding agents"
  homepage "https://github.com/perlyer/cubby"
  url "https://files.pythonhosted.org/packages/74/43/03e54d65b3736b117874f5b844a2a6e28454273ca5c8951f71c7a99310be/cubby_secrets-0.7.0.tar.gz"
  sha256 "2233fe2d97ab2381c18bc9db23b5300eeb138791194a8f124cc7938cdbf92010"
  license "MIT"

  depends_on "age"
  depends_on "python@3.13"

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "cubby", shell_output("#{bin}/cubby --version")
  end
end
