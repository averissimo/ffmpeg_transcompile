import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(name='ffmpeg_transcompile',
  version='1.0',
  description='A plugin to transcompile videos',
  url='http://github.com/averissimo/ffmpeg_transcompile',
  author='André Veríssimo',
  author_email='afsverissimo@gmail.com',
  long_description=long_description,
  long_description_content_type="text/markdown",
  license='MIT',
  install_requires=[
    "pyyaml"
  ],
  package_dir={"": "src"},
  py_modules=["transcode"],
  python_requires=">=3.6",
)
