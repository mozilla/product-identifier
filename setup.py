from setuptools import setup, find_packages


setup(
    name="product-identifier",
    version="0.0.1",
    description="A set of tools to obtain product urls",
    author="Mozilla",
    packages=find_packages(),
    package_data={"": ["*.json"]},
    include_package_data=True,
    scripts=[
        "scripts/manage.py",
        "scripts/master.py",
        "scripts/worker.py",
    ],
)
