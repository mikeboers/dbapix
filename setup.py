from setuptools import setup, find_packages

setup(

    name='dbapix',
    version='2.0.0',
    description="A unification of, and extension to, several DB-API 2.0 drivers.",

    url='http://github.com/mikeboers/dbapix',
    
    packages=find_packages(exclude=['build*', 'tests*']),
    include_package_data=True,
    
    author='Mike Boers',
    author_email='dbapix@mikeboers.com',
    license='BSD-3',

    install_requires='''
        six
    ''',
    
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    
)
