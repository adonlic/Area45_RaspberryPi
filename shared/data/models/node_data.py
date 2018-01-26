from sqlalchemy import Column, Integer, Float, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class Node(Base):
    __tablename__ = 'node'
    __table_args__ = {'info': {'without_rowid': True}}

    id = Column(String, primary_key=True)
    alias = Column(String, nullable=True)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)

    # we can use Component class instead of Component string, but Python interpreter
    # won't recognize Component class before it's being scanned, so we use Component
    # string, ps. if Component class was defined before this class (Node), using class
    # instead of string would work
    # back_populates attribute tells if one of objects of current class knows its
    # connected objects from other db table (class), then that object knows about this
    # one (in this case, if we pull fill up components list, then each component from
    # that list will hold this node too)
    # cascade delete means that if this node is deleted, so its components will be too
    # THIS PRINCIPLE IS USED IN OTHER CLASSES TOO
    components = relationship('Component', back_populates='node', cascade='delete')

    def __init__(self, _id, created_at, updated_at, alias=""):
        self.id = _id
        self.alias = alias
        self.created_at = created_at
        self.updated_at = updated_at


class Component(Base):
    __tablename__ = 'component'
    __table_args__ = {'info': {'without_rowid': True}}

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(String, ForeignKey('node.id'), nullable=False)
    id_used = Column(Integer, nullable=False)
    type = Column(String, nullable=False)
    name = Column(String, nullable=True)
    alias = Column(String, nullable=True)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)

    UniqueConstraint(node_id, id_used)

    node = relationship('Node', back_populates='components')
    component_value_types = relationship('ComponentValueType', back_populates='component', cascade='delete')

    def __init__(self, node_id, id_used, type, created_at, updated_at, name="", alias=""):
        self.node_id = node_id
        self.id_used = id_used
        self.type = type
        self.name = name
        self.alias = alias
        self.created_at = created_at
        self.updated_at = updated_at


class ComponentValueType(Base):
    __tablename__ = 'component_value_type'
    __table_args__ = {'info': {'without_rowid': True}}

    id = Column(Integer, primary_key=True, autoincrement=True)
    component_id = Column(Integer, ForeignKey('component.id'), nullable=False)
    value_type = Column(String, nullable=False)
    alias = Column(String, nullable=True)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)

    UniqueConstraint(component_id, value_type)

    component = relationship('Component', back_populates='component_value_types')
    component_settingss = relationship('ComponentSettings', back_populates='component_value_type', cascade='delete')

    def __init__(self, component_id, value_type, created_at, updated_at, alias=""):
        self.component_id = component_id
        self.value_type = value_type
        self.alias = alias
        self.created_at = created_at
        self.updated_at = updated_at


class ConfigUpdate(Base):
    __tablename__ = 'config_update'
    __table_args__ = {'info': {'without_rowid': True}}

    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String, nullable=True)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)

    component_settingss = relationship('ComponentSettings', back_populates='config_update', cascade='delete')

    def __init__(self, created_at, updated_at, description=""):
        self.description = description
        self.created_at = created_at
        self.updated_at = updated_at


class ComponentSettings(Base):
    __tablename__ = 'component_settings'
    __table_args__ = {'info': {'without_rowid': True}}

    id = Column(Integer, primary_key=True, autoincrement=True)
    component_value_type_id = Column(Integer, ForeignKey('component_value_type.id'), nullable=False)
    config_update_id = Column(Integer, ForeignKey('config_update.id'), nullable=False)
    measuring_unit = Column(String, nullable=False)
    measurement_period = Column(Integer, nullable=False)
    created_at = Column(String, nullable=False)

    UniqueConstraint(component_value_type_id, config_update_id)

    component_value_type = relationship('ComponentValueType', back_populates='component_settingss')
    config_update = relationship('ConfigUpdate', back_populates='component_settingss')
    measurements = relationship('Measurement', back_populates='component_settings', cascade='delete')

    def __init__(self, component_value_type_id, config_update_id, measuring_unit, measurement_period, created_at):
        self.component_value_type_id = component_value_type_id
        self.config_update_id = config_update_id
        self.measuring_unit = measuring_unit
        self.measurement_period = measurement_period
        self.created_at = created_at


class Measurement(Base):
    __tablename__ = 'measurement'
    __table_args__ = {'info': {'without_rowid': True}}

    id = Column(Integer, primary_key=True, autoincrement=True)
    component_settings_id = Column(Integer, ForeignKey('component_settings.id'), nullable=False)
    value = Column(Float, nullable=False)
    measured_at = Column(String, nullable=False)
    collector_delivery_confirmed = Column(Boolean, nullable=False, default=True)
    created_at = Column(String, nullable=False)

    component_settings = relationship('ComponentSettings', back_populates='measurements')

    def __init__(self, component_settings_id, value, measured_at, created_at):
        self.component_settings_id = component_settings_id
        self.value = value
        self.measured_at = measured_at
        self.created_at = created_at
