#!/usr/bin/env python
import sys
from flask_script import Manager
from flask_script.commands import InvalidCommand
from flask_migrate import MigrateCommand
from product_identifier.commands import (
    GunicornServerCommand,
    ListCommand,
)
from product_identifier.webapp import create_webapp

manager = Manager(create_webapp)
manager.add_option('-c', '--config', dest='config', required=False)
manager.add_command('runserver_gunicorn', GunicornServerCommand())
manager.add_command('db', MigrateCommand)
manager.add_command('list', ListCommand)

if __name__ == '__main__':
    try:
        manager.run()
    except InvalidCommand, e:
        print >> sys.stderr, e
        sys.exit(1)
