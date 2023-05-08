from setuptools import setup
import os


requirements = []
f = open('requirements.txt', 'r')
while True:
    l = f.readline()
    if l == '':
        break
    requirements.append(l.rstrip())
f.close()

test_requirements = []
f = open('test_requirements.txt', 'r')
while True:
    l = f.readline()
    if l == '':
        break
    test_requirements.append(l.rstrip())
f.close()

man_dir = 'man/build'
mans = [
        'eth-balance',
        'eth-count',
        'eth-decode',
        'eth-encode',
        'eth-gas',
        'eth-get',
        'eth-info',
        'eth-raw',
        'eth-wait',
        ]
for i in range(len(mans)):
    mans[i] = os.path.join(man_dir, mans[i] + '.1')

setup(
        install_requires=requirements,
        tests_require=test_requirements,
        data_files=[("man/man1", mans)],
    )
