import bottle

from bottle import HTTPError
from bottle.ext import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, Sequence, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
engine = create_engine('postgresql://postgres@db/postgres', echo=True)

app = bottle.Bottle()
plugin = sqlalchemy.Plugin(
    engine,
    Base.metadata,
    keyword='db',
    create=True,
    commit=True,
    use_kwargs=False,
)

app.install(plugin)


class Entity(Base):
    __tablename__ = 'entity'
    id = Column(Integer, Sequence('id_seq'), primary_key=True)
    name = Column(String(50))

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Entity('%d', '%s')>" % (self.id, self.name)


def is_valid_name(name):
    return name.isalpha()


@app.get('/:name')
def show(name, db):
    entity = db.query(Entity).filter_by(name=name).first()
    if entity:
        return {'id': entity.id, 'name': entity.name}
    return HTTPError(404, 'Entity not found.')


@app.put('/:name')
def put_name(name, db):
    entity = Entity(name)
    db.add(entity)


bottle.run(app, host='0.0.0.0', port=8080)
