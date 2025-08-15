from db import db


class RoleModel(db.Model):
    __tablename__ = 'roles'

    role_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), unique=False, nullable=False)
    admin = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship('UserModel', back_populates='roles')

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
