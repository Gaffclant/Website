# Source code for my website gaffclant.com
import datetime
import json
import os.path

import cherrypy
import requests
from cherrypy.lib import auth_digest
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape
from peewee import *
from playhouse.signals import pre_save

env = Environment(loader=FileSystemLoader('public'), autoescape=select_autoescape())
db = SqliteDatabase('blog_database.db')


class BaseModel(Model):
    class Meta:
        database = db


class Post(BaseModel):
    date = DateTimeField(default=datetime.datetime.now)
    title = TextField()
    text = TextField()
    id = IntegerField(primary_key=True)


@pre_save(sender=Post)
def on_save_handler(model_class, instance, created):
    next_value = Post.select(fn.Max(Post.temp_id))[0].temp_id + 1
    instance.temp_id = next_value


db.connect()

if not db.get_tables([Post]):
    db.create_tables([Post])

# Post.create(
#     title="Not a test",
#     text="lorem ipsum samet",
# )
# Post.create(
#     title="Post 2",
#     text="Lorem lmao",
# )
# Post.create(
#     title="Friends are mean",
#     text="Hayden is a bitch",
# )
# Post.create(
#     title="Linux is cool",
#     text="Insert rant here",
# )
# Post.create(
#     title="How to code",
#     text="gamer moment am i right?",
# )

blog = Post.select().order_by(Post.date.desc())


class Website(object):
    @cherrypy.expose
    def index(self):
        preview = Post.select().order_by(Post.date.desc()).limit(3)
        template = env.get_template("html/index.html")
        motdJson = requests.get("https://xkcd.com/info.0.json").json()
        motd = motdJson.get("img")
        return template.render(index=True, blog=preview, motd=motd)

    @cherrypy.expose
    def about(self):
        template = env.get_template("html/about.html")
        return template.render(about=True)

    @cherrypy.expose
    def admin(self):
        template = env.get_template("html/admin.html")
        return template.render()

    @cherrypy.expose
    def post(self, title, text):
        Post.create(
            title=title,
            text=text
        )

        raise cherrypy.HTTPRedirect("/#")

    @cherrypy.expose
    def blogpost(self, id):
        template = env.get_template("html/blogpost.html")
        post = Post.get(id=id)
        return template.render(p=post)


load_dotenv()
USERS = os.environ['USERS']
USERS = json.loads(USERS)

if __name__ == '__main__':
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './public'
        },
        '/admin': {
            'tools.auth_digest.on': True,
            'tools.auth_digest.realm': 'localhost',
            'tools.auth_digest.get_ha1': auth_digest.get_ha1_dict_plain(USERS),
            'tools.auth_digest.key': 'a565c27146791cfb',
            'tools.auth_digest.accept_charset': 'UTF-8',
        },
        '/post': {
            'tools.auth_digest.on': True,
            'tools.auth_digest.realm': 'localhost',
            'tools.auth_digest.get_ha1': auth_digest.get_ha1_dict_plain(USERS),
            'tools.auth_digest.key': os.environ['DIGESTKEY'],
            'tools.auth_digest.accept_charset': 'UTF-8',
        }
    }
cherrypy.quickstart(Website(), '/', conf)
