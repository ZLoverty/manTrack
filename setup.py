from setuptools import setup, find_packages

# Read dependencies from requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='manTrack',                           # Package name
    version='1.0',                            # Package version
    packages=find_packages(),                   # Automatically find all packages
    install_requires=requirements,               # Dependencies from requirements.txt
    entry_points={                              # Make package runnable as a script
        'console_scripts': [
            'manTrack=manTrack.__main__:run'
        ]
    },
    author='Zhengyang Liu',                         # Author information
    author_email='liuzy19911112@gmail.com',
    description='A python GUI software that makes modifying circle detection data easier.',       # Short description
    long_description=open('readme.md').read(),  # Long description from README
    long_description_content_type='text/markdown',
    url='https://zloverty.github.io/manTrack/', # Project URL
    classifiers=[                               # Metadata and classification
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',                    # Minimum Python version
)