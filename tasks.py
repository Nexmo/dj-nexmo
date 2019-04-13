from invoke import task


@task
def build(c):
    # c.run("pandoc -f markdown -t rst -o README.rst README.md")
    c.run("python setup.py bdist_wheel sdist")


@task
def clean(c):
    c.run("rm -rf build dist")
