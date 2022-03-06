from uuid import uuid1

default_app_config = 'blog.apps.BlogConfig'

def create_slug():
    return ''.join(str(uuid1()).split('-'))[0:8]