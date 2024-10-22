from setuptools import setup, find_packages

setup(
    name='lucas',
    version='0.0.1',
    author='Oleksandr Kuvshynov',
    author_email='okuvshynov@gmail.com',
    description='Code assistant',
    long_description='Code assistant',
    packages=find_packages(),
    install_requires=[ ],
    url='https://github.com/okuvshynov/lucas',
    entry_points={
        'console_scripts': [
            'lcs = lucas.lcs:main'
        ]
    },
)
